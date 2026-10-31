"""Tests for DockerExecutionRunner security controls, worker failure handling, and audit records."""

import subprocess
import pytest

from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.grading import grade_submission
from evaluator.runners.docker_runner import (
    DockerExecutionRunner,
    DockerSecurityConfig,
    _START_SENTINEL,
    _END_SENTINEL,
)


class FakeSubprocessResult:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture
def assignment():
    return AssignmentDefinition(
        task_id="algo_task",
        title="Algorithms Test",
        test_cases=(
            TestCaseDefinition("test_1", "Case 1", 5, assertion="add(1, 2) == 3"),
            TestCaseDefinition("test_2", "Case 2", 5, assertion="add(-1, 1) == 0"),
        ),
    )


class TestDockerSecurityCommandConstruction:
    def test_strict_security_flags_present(self):
        config = DockerSecurityConfig(
            cpus=0.5,
            memory_limit="256m",
            pids_limit=64,
            network_disabled=True,
            read_only_root=True,
            drop_capabilities="ALL",
            no_new_privileges=True,
        )
        runner = DockerExecutionRunner(security_config=config)
        cmd = runner.build_docker_command("C:/fake/path")

        assert "docker" in cmd
        assert "run" in cmd
        assert "--network" in cmd and "none" in cmd
        assert "--cpus=0.5" in cmd
        assert "--memory=256m" in cmd
        assert "--memory-swap=256m" in cmd
        assert "--pids-limit=64" in cmd
        assert "--cap-drop=ALL" in cmd
        assert "--security-opt=no-new-privileges:true" in cmd
        assert "--read-only" in cmd
        assert any(arg.endswith(":/workspace:ro") for arg in cmd)


class TestDockerExecutionScenarios:
    def test_successful_container_execution(self, assignment):
        fake_stdout = f"""
Student print output: Hello world
{_START_SENTINEL}
[
  {{"test_case_id": "test_1", "passed": true, "message": null}},
  {{"test_case_id": "test_2", "passed": true, "message": null}}
]
{_END_SENTINEL}
"""
        def fake_executor(cmd, **kwargs):
            # Verify clean env without host secrets
            env = kwargs.get("env", {})
            assert "GEMINI_API_KEY" not in env
            return FakeSubprocessResult(returncode=0, stdout=fake_stdout, stderr="")

        runner = DockerExecutionRunner(command_executor=fake_executor)
        results = runner.run(assignment, "def add(a, b): return a + b")

        assert len(results) == 2
        assert all(r.passed for r in results)

        # Verify integration with grading engine
        report = grade_submission(assignment, results)
        assert report.earned_points == 10
        assert report.percentage == 100.0

        # Verify audit record
        audit = runner.last_audit_record
        assert audit is not None
        assert audit.exit_code == 0
        assert audit.timed_out is False
        assert audit.oom_killed is False
        assert "Hello world" in audit.stdout

    def test_timeout_expiration_handling(self, assignment):
        def timeout_executor(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=5.0, output="partial", stderr="timeout")

        runner = DockerExecutionRunner(command_executor=timeout_executor)
        results = runner.run(assignment, "while True: pass")

        assert len(results) == 2
        assert all(not r.passed for r in results)
        assert "timed out after" in results[0].message

        audit = runner.last_audit_record
        assert audit.timed_out is True
        assert audit.exit_code == 124

    def test_oom_killed_handling(self, assignment):
        # Exit code 137 indicates SIGKILL from Linux kernel (OOM)
        def oom_executor(cmd, **kwargs):
            return FakeSubprocessResult(returncode=137, stdout="", stderr="Killed")

        runner = DockerExecutionRunner(command_executor=oom_executor)
        results = runner.run(assignment, "big_arr = [0] * 10**9")

        assert len(results) == 2
        assert all(not r.passed for r in results)
        assert "OOM: Out of Memory" in results[0].message

        audit = runner.last_audit_record
        assert audit.oom_killed is True
        assert audit.exit_code == 137

    def test_container_crash_handling(self, assignment):
        def crash_executor(cmd, **kwargs):
            return FakeSubprocessResult(returncode=1, stdout="", stderr="SyntaxError: invalid syntax")

        runner = DockerExecutionRunner(command_executor=crash_executor)
        results = runner.run(assignment, "def broken_syntax(::")

        assert len(results) == 2
        assert all(not r.passed for r in results)
        assert "Worker crashed: SyntaxError" in results[0].message
