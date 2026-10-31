"""Quick demo: send student code to Gemini for structured and markdown review."""

from dotenv import load_dotenv

from evaluator.ai_reviewer import GeminiCodeReviewer, GeminiReviewError

# Load .env so GEMINI_API_KEY and GEMINI_MODEL are available
load_dotenv()


student_code = """
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)


print(calculate_average([10, 20, 30]))
"""

reviewer = GeminiCodeReviewer()

try:
    print("Requesting structured Gemini code review...")
    feedback = reviewer.review_structured(student_code)

    print("\n========== GEMINI STRUCTURED CODE REVIEW ==========\n")
    print(f"Summary:\n  {feedback.summary}\n")
    if feedback.strengths:
        print("Strengths:")
        for s in feedback.strengths:
            print(f"  + {s}")
        print()

    print(f"Observations ({len(feedback.observations)} found):")
    for obs in feedback.observations:
        line_ref = f" (line {obs.line_number})" if obs.line_number else ""
        print(f"  [{obs.severity.value.upper()}] {obs.category.value}: {obs.title}{line_ref}")
        print(f"    Explanation: {obs.explanation}")
        if obs.suggested_fix:
            print(f"    Remediation: {obs.suggested_fix}")
        print()

    print(f"Pedagogical Guidance:\n  {feedback.pedagogical_guidance}")
    print("\n===================================================")

except GeminiReviewError as exc:
    print(f"\nReview failed: {exc}")
    if exc.__cause__:
        print(f"Underlying error: {type(exc.__cause__).__name__}: {exc.__cause__}")
