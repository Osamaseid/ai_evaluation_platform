"""Isolated subprocess-based execution runner."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Union

from evaluator.assignment import AssignmentDefinition
from evaluator.collector import SourceBundle
from evaluator.grading import TestCaseResult
from evaluator.runner import Runner


_HARNESS_TEMPLATE = """# Auto-generated isolated test harness
import json
import sys
import io

with open("_tests.json", "r", encoding="utf-8") as f:
    config = json.load(f)

test_cases = config["test_cases"]
results = []

try:
    import solution
except Exception as exc:
    err_msg = f"Import error: {type(exc).__name__}: {exc}"
    for tc in test_cases:
        results.append({"test_case_id": tc["test_case_id"], "passed": False, "message": err_msg})
    with open("_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f)
    sys.exit(0)

for tc in test_cases:
    tc_id = tc["test_case_id"]
    assertion = tc.get("assertion")
    expected_output = tc.get("expected_output")

    try:
        if assertion:
            scope = {"solution": solution}
            for attr in dir(solution):
                if not attr.startswith("_"):
                    scope[attr] = getattr(solution, attr)
            
            outcome = eval(assertion, scope)
            if not bool(outcome):
                results.append({
                    "test_case_id": tc_id,
                    "passed": False,
                    "message": f"Assertion failed: {assertion}"
                })
            else:
                results.append({"test_case_id": tc_id, "passed": True, "message": None})
        else:
            # Fallback: inspect solution module for function or test method
            func = getattr(solution, tc_id, None) or getattr(solution, f"test_{tc_id}", None)
            if func is None:
                results.append({
                    "test_case_id": tc_id,
                    "passed": False,
                    "message": f"Function or test '{tc_id}' not found in solution."
                })
            else:
                if callable(func):
                    func()
                results.append({"test_case_id": tc_id, "passed": True, "message": None})

    except AssertionError as exc:
        results.append({
            "test_case_id": tc_id,
            "passed": False,
            "message": f"AssertionError: {exc}"
        })
    except Exception as exc:
        results.append({
            "test_case_id": tc_id,
            "passed": False,
            "message": f"{type(exc).__name__}: {exc}"
        })

with open("_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f)
"""


class IsolatedProcessRunner(Runner):
    """Executes student code in an isolated child process with timeout constraints."""

    def __init__(
        self,
        timeout_seconds: float = 4.0,
        python_executable: str | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

        self.timeout_seconds = timeout_seconds
        self.python_executable = python_executable or sys.executable

    def run(
        self,
        assignment: AssignmentDefinition,
        source_code: Union[str, SourceBundle],
    ) -> tuple[TestCaseResult, ...]:
        """Execute test cases against submitted source code in an ephemeral directory."""
        if not isinstance(assignment, AssignmentDefinition):
            raise TypeError("assignment must be an AssignmentDefinition instance.")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Stage source files
            if isinstance(source_code, SourceBundle):
                for src_file in source_code.files:
                    target_file = temp_path / src_file.relative_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_text(src_file.content, encoding="utf-8")
                # Ensure solution.py is available as entry point
                if not (temp_path / "solution.py").exists():
                    primary = source_code.primary_module
                    (temp_path / "solution.py").write_text(primary.content, encoding="utf-8")
            elif isinstance(source_code, str):
                (temp_path / "solution.py").write_text(source_code, encoding="utf-8")
            else:
                raise TypeError("source_code must be a str or SourceBundle instance.")

            # Stage test configuration
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
            (temp_path / "_harness.py").write_text(_HARNESS_TEMPLATE, encoding="utf-8")

            # Environment isolation
            env = {
                "PYTHONPATH": str(temp_path),
                "PYTHONNOUSERSITE": "1",
                "PYTHONSAFEPATH": "1",
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "PATH": os.environ.get("PATH", ""),
                "TEMP": str(temp_path),
                "TMP": str(temp_path),
            }

            try:
                proc = subprocess.run(
                    [self.python_executable, "_harness.py"],
                    cwd=str(temp_path),
                    env=env,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    text=True,
                )
            except subprocess.TimeoutExpired:
                return tuple(
                    TestCaseResult(
                        test_case_id=tc.test_case_id,
                        passed=False,
                        message=f"Execution timed out after {self.timeout_seconds} seconds.",
                    )
                    for tc in assignment.test_cases
                )

            results_file = temp_path / "_results.json"
            if results_file.exists():
                try:
                    data = json.loads(results_file.read_text(encoding="utf-8"))
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
                            message=f"Failed to parse test results: {exc}",
                        )
                        for tc in assignment.test_cases
                    )

            # Harness crashed without producing results
            err_msg = proc.stderr.strip() or proc.stdout.strip() or f"Process exited with code {proc.returncode}"
            return tuple(
                TestCaseResult(
                    test_case_id=tc.test_case_id,
                    passed=False,
                    message=f"Execution crashed: {err_msg}",
                )
                for tc in assignment.test_cases
            )

