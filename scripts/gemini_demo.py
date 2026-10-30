"""Quick demo: send student code to Gemini for review."""

from dotenv import load_dotenv

from evaluator.ai_reviewer import GeminiCodeReviewer, GeminiReviewError

# Load .env so GEMINI_API_KEY and GEMINI_MODEL are available
# to GeminiCodeReviewer via os.getenv().
load_dotenv()


student_code = """
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)


print(calculate_average([10, 20, 30]))
"""

reviewer = GeminiCodeReviewer()

try:
    feedback = reviewer.review(student_code)

    print("\n========== GEMINI CODE REVIEW ==========\n")
    print(feedback)
    print("\n========================================")

except GeminiReviewError as exc:
    print(f"\nReview failed: {exc}")
    if exc.__cause__:
        print(f"Underlying error: {type(exc.__cause__).__name__}: {exc.__cause__}")
