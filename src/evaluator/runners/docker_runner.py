"""Docker-isolated test execution runner for untrusted student code."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from typing import Any, Callable, Union
import uuid

from evaluator.assignment import AssignmentDefinition
from evaluator.collector import SourceBundle
from evaluator.grading import TestCaseResult
from evaluator.runner import Runner

logger = logging.getLogger(__name__)

_START_SENTINEL = "---TEST_RESULTS_START---"
_END_SENTINEL = "---TEST_RESULTS_END---"

_DOCKER_HARNESS_TEMPLATE = f"""# Isolated In-Container Test Harness
import json
import sys

with open("_tests.json", "r", encoding="utf-8") as f:
    config = json.load(f)

test_cases = config["test_cases"]
results = []

try:
    import solution
except Exception as exc:
    err_msg = f"Import error: {{type(exc).__name__}}: {{exc}}"
    for tc in test_cases:
        results.append({{"test_case_id": tc["test_case_id"], "passed": False, "message": err_msg}})
    print("\\n{_START_SENTINEL}")
    print(json.dumps(results))
    print("{_END_SENTINEL}")
    sys.exit(0)

for tc in test_cases:
    tc_id = tc["test_case_id"]
    assertion = tc.get("assertion")
    expected_output = tc.get("expected_output")

    try:
        if assertion:
            scope = {{"solution": solution}}
            for attr in dir(solution):
                if not attr.startswith("_"):
                    scope[attr] = getattr(solution, attr)
            
            outcome = eval(assertion, scope)
            if not bool(outcome):
                results.append({{
                    "test_case_id": tc_id,
                    "passed": False,
                    "message": f"Assertion failed: {{assertion}}"
                }})
            else:
                results.append({{"test_case_id": tc_id, "passed": True, "message": None}})
        else:
            func = getattr(solution, tc_id, None) or getattr(solution, f"test_{{tc_id}}", None)
            if func is None:
                results.append({{
                    "test_case_id": tc_id,
                    "passed": False,
                    "message": f"Function or test '{{tc_id}}' not found in solution."
                }})
            else:
                if callable(func):
                    func()
                results.append({{"test_case_id": tc_id, "passed": True, "message": None}})

    except AssertionError as exc:
        results.append({{
            "test_case_id": tc_id,
            "passed": False,
            "message": f"AssertionError: {{exc}}"
        }})
    except Exception as exc:
        results.append({{
            "test_case_id": tc_id,
            "passed": False,
            "message": f"{{type(exc).__name__}}: {{exc}}"
        }})

print("\\n{_START_SENTINEL}")
print(json.dumps(results))
print("{_END_SENTINEL}")
"""


@dataclass(frozen=True)
class DockerSecurityConfig:
    """Security boundaries enforced on containerized untrusted workers."""

    docker_image: str = "python:3.11-slim"
    cpus: float = 0.5
    memory_limit: str = "256m"
    pids_limit: int = 64
    timeout_seconds: float = 5.0
    network_disabled: bool = True
    read_only_root: bool = True
    drop_capabilities: str = "ALL"
    no_new_privileges: bool = True
    max_output_bytes: int = 50_000


@dataclass(frozen=True)
class ExecutionAuditRecord:
    """Audit record capturing complete metadata and diagnostics for an execution run."""

    execution_id: str
    task_id: str
    duration_seconds: float
    security_config: DockerSecurityConfig
    stdout: str
    stderr: str
    exit_code: int
    worker_type: str = "docker_container"
    timed_out: bool = False
    oom_killed: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DockerExecutionError(Exception):
    """Raised when worker container dispatch fails."""


class DockerExecutionRunner(Runner):
    """Executes untrusted student submissions inside hardened, ephemeral Docker containers."""

    def __init__(
        self,
        security_config: DockerSecurityConfig | None = None,
        command_executor: Callable[..., Any] | None = None,
    ) -> None:
        self.config = security_config or DockerSecurityConfig()
        self._command_executor = command_executor or subprocess.run
        self.last_audit_record: ExecutionAuditRecord | None = None

    def build_docker_command(self, staging_dir: str) -> list[str]:
        """Construct the hardened docker run command line."""
        # Convert staging directory path to POSIX format for cross-platform Docker mount
        normalized_path = Path(staging_dir).resolve().as_posix()

        cmd = [
            "docker", "run", "--rm",
            "--network", "none" if self.config.network_disabled else "bridge",
            f"--cpus={self.config.cpus}",
            f"--memory={self.config.memory_limit}",
            f"--memory-swap={self.config.memory_limit}",
            f"--pids-limit={self.config.pids_limit}",
            f"--cap-drop={self.config.drop_capabilities}",
            f"--security-opt=no-new-privileges:{str(self.config.no_new_privileges).lower()}",
            "--read-only" if self.config.read_only_root else "",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
            "-v", f"{normalized_path}:/workspace:ro",
            "-w", "/workspace",
            self.config.docker_image,
            "python", "-u", "/workspace/_harness.py",
        ]
        return [part for part in cmd if part]

    def run(
        self,
        assignment: AssignmentDefinition,
        source_code: Union[str, SourceBundle],
    ) -> tuple[TestCaseResult, ...]:
        """Stage untrusted code and execute inside an isolated container."""
        if not isinstance(assignment, AssignmentDefinition):
            raise TypeError("assignment must be an AssignmentDefinition instance.")

        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        start_time = time.monotonic()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Stage student code
            if isinstance(source_code, SourceBundle):
                for src_file in source_code.files:
                    target = temp_path / src_file.relative_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(src_file.content, encoding="utf-8")
                if not (temp_path / "solution.py").exists():
                    (temp_path / "solution.py").write_text(
                        source_code.primary_module.content, encoding="utf-8"
                    )
            elif isinstance(source_code, str):
                (temp_path / "solution.py").write_text(source_code, encoding="utf-8")
            else:
                raise TypeError("source_code must be a str or SourceBundle.")

            # Stage test configuration and harness
            tests_payload = {
                "test_cases": [
                    {
                        "test_case_id": tc.test_case_id,
                        "assertion": tc.assertion,
                        "expected_output": tc.expected_output,
                        "input_data": tc.input_data,
                    }
                    for tc in assignment.test_cases
                ]
            }
            (temp_path / "_tests.json").write_text(json.dumps(tests_payload), encoding="utf-8")
            (temp_path / "_harness.py").write_text(_DOCKER_HARNESS_TEMPLATE, encoding="utf-8")

            docker_cmd = self.build_docker_command(str(temp_path))

            # Run container with completely clean environment (NO host secrets passed)
            clean_env: dict[str, str] = {
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "PATH": os.environ.get("PATH", ""),
            }

            timed_out = False
            oom_killed = False
            stdout_text = ""
            stderr_text = ""
            exit_code = -1

            try:
                proc = self._command_executor(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout_seconds,
                    env=clean_env,
                )
                exit_code = proc.returncode
                stdout_text = proc.stdout[: self.config.max_output_bytes]
                stderr_text = proc.stderr[: self.config.max_output_bytes]

                if exit_code == 137:
                    oom_killed = True

            except subprocess.TimeoutExpired as exc:
                timed_out = True
                exit_code = 124
                raw_out = getattr(exc, "output", "") or getattr(exc, "stdout", "") or ""
                raw_err = getattr(exc, "stderr", "") or ""
                stdout_text = str(raw_out)[: self.config.max_output_bytes]
                stderr_text = str(raw_err)[: self.config.max_output_bytes]
            except Exception as exc:
                exit_code = -1
                stderr_text = f"Worker launch failure: {type(exc).__name__}: {exc}"

            duration = time.monotonic() - start_time

            # Generate and record audit log
            self.last_audit_record = ExecutionAuditRecord(
                execution_id=execution_id,
                task_id=assignment.task_id,
                duration_seconds=duration,
                security_config=self.config,
                stdout=stdout_text,
                stderr=stderr_text,
                exit_code=exit_code,
                timed_out=timed_out,
                oom_killed=oom_killed,
            )

            # Failure branch 1: Timeout
            if timed_out:
                return tuple(
                    TestCaseResult(
                        test_case_id=tc.test_case_id,
                        passed=False,
                        message=f"Container execution timed out after {self.config.timeout_seconds}s.",
                    )
                    for tc in assignment.test_cases
                )

            # Failure branch 2: OOM Kill
            if oom_killed:
                return tuple(
                    TestCaseResult(
                        test_case_id=tc.test_case_id,
                        passed=False,
                        message=f"Container was killed (OOM: Out of Memory limit {self.config.memory_limit} exceeded).",
                    )
                    for tc in assignment.test_cases
                )

            # Extract test results from sentinel markers in stdout
            pattern = re.compile(
                rf"{re.escape(_START_SENTINEL)}\s*(.*?)\s*{re.escape(_END_SENTINEL)}",
                re.DOTALL,
            )
            match = pattern.search(stdout_text)
            if match:
                raw_json = match.group(1).strip()
                try:
                    data = json.loads(raw_json)
                    results_map = {item["test_case_id"]: item for item in data}
                    return tuple(
                        TestCaseResult(
                            test_case_id=tc.test_case_id,
                            passed=bool(results_map.get(tc.test_case_id, {}).get("passed", False)),
                            message=results_map.get(tc.test_case_id, {}).get("message"),
                        )
                        for tc in assignment.test_cases
                    )
                except Exception as exc:
                    return tuple(
                        TestCaseResult(
                            test_case_id=tc.test_case_id,
                            passed=False,
                            message=f"Failed to parse container test results JSON: {exc}",
                        )
                        for tc in assignment.test_cases
                    )

            # Worker crashed without producing sentinel output
            err_summary = stderr_text.strip() or stdout_text.strip() or f"Process exited with code {exit_code}"
            return tuple(
                TestCaseResult(
                    test_case_id=tc.test_case_id,
                    passed=False,
                    message=f"Worker crashed: {err_summary}",
                )
                for tc in assignment.test_cases
            )
