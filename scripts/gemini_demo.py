
from evaluator.ai_reviewer import GeminiCodeReviewer


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

except Exception as error:
    print(f"Review failed: {error}")
g