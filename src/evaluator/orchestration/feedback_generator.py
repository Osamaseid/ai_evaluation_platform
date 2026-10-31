"""Student-facing evaluation feedback generator combining deterministic test outcomes and AI observations."""

from typing import Any

from evaluator.assignment import AssignmentDefinition
from evaluator.grading import GradingReport, TestCaseResult


class FeedbackGenerator:
    """Synthesizes human-readable pedagogical markdown feedback for students."""

    @staticmethod
    def generate(
        assignment: AssignmentDefinition,
        test_results: tuple[TestCaseResult, ...],
        grading_report: GradingReport,
        ai_review: str | None = None,
        structured_feedback: Any | None = None,
    ) -> str:
        """Create a structured Markdown feedback report."""
        lines: list[str] = [
            f"# Evaluation Feedback: {assignment.title}",
            "",
            "## 1. Test Results & Score",
            f"- **Score**: {grading_report.earned_points} / {grading_report.max_score} ({grading_report.percentage:.1f}%)",
            f"- **Tests Passed**: {grading_report.passed_tests} / {grading_report.total_tests}",
            "",
            "### Test Case Breakdown",
        ]

        # Map test definition descriptions
        desc_map = {tc.test_case_id: tc.description for tc in assignment.test_cases}

        for tr in test_results:
            desc = desc_map.get(tr.test_case_id, "")
            status_tag = "[PASS]" if tr.passed else "[FAIL]"
            line = f"- {status_tag} **`{tr.test_case_id}`**: {desc}"
            msg = getattr(tr, "message", None) or getattr(tr, "error_message", None)
            if not tr.passed and msg:
                line += f"\n  - *Details*: {msg}"
            lines.append(line)

        lines.extend(["", "## 2. AI Code Review & Pedagogical Guidance", ""])

        if structured_feedback is not None:
            # Feedback from CodeReviewFeedback schema
            summary = getattr(structured_feedback, "summary", "")
            if summary:
                lines.extend([f"**Summary**: {summary}", ""])

            strengths = getattr(structured_feedback, "strengths", [])
            if strengths:
                lines.append("### Strengths")
                for s in strengths:
                    lines.append(f"- {s}")
                lines.append("")

            observations = getattr(structured_feedback, "observations", [])
            if observations:
                lines.append("### Detailed Observations")
                for obs in observations:
                    sev = getattr(obs, "severity", "info").upper() if hasattr(obs, "severity") else "INFO"
                    cat = getattr(obs, "category", "general")
                    title = getattr(obs, "title", "Observation")
                    exp = getattr(obs, "explanation", "")
                    lines.append(f"#### [{sev}] {title} ({cat})")
                    lines.append(f"{exp}")
                    
                    line_no = getattr(obs, "line_number", None)
                    if line_no:
                        lines.append(f"- *Line*: {line_no}")
                    evidence = getattr(obs, "code_evidence", None)
                    if evidence:
                        lines.append(f"```python\n{evidence}\n```")
                    fix = getattr(obs, "suggested_fix", None)
                    if fix:
                        lines.append(f"- *Suggested Fix*: {fix}")
                    lines.append("")

            guidance = getattr(structured_feedback, "pedagogical_guidance", "")
            if guidance:
                lines.extend(["### Next Steps", f"{guidance}", ""])

        elif ai_review:
            lines.extend([ai_review, ""])
        else:
            lines.extend(["*AI code review was not requested or unavailable.*", ""])

        return "\n".join(lines).strip()
