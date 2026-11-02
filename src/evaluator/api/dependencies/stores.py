"""Shared persistent store and storage singletons for the FastAPI runtime."""

from datetime import datetime, timezone
from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.auth.models import UserAccount, UserRole
from evaluator.auth.security import PasswordHasher
from evaluator.rubric import GradingRubric, RubricCriterion
from evaluator.storage.submission_storage import ControlledFileStorage
from evaluator.stores.assignment_store import InMemoryAssignmentStore
from evaluator.stores.evaluation_store import InMemoryEvaluationStore
from evaluator.stores.instructor_store import InMemoryInstructorStore
from evaluator.stores.rubric_store import InMemoryRubricStore
from evaluator.stores.student_store import InMemoryStudentStore
from evaluator.stores.submission_store import InMemorySubmissionStore
from evaluator.stores.user_store import InMemoryUserStore
from evaluator.users import Instructor, Student

# Shared singleton instances across all HTTP route handlers
shared_user_store = InMemoryUserStore()
shared_student_store = InMemoryStudentStore()
shared_instructor_store = InMemoryInstructorStore()
shared_assignment_store = InMemoryAssignmentStore()
shared_rubric_store = InMemoryRubricStore()
shared_submission_store = InMemorySubmissionStore()
shared_evaluation_store = InMemoryEvaluationStore()
shared_file_storage = ControlledFileStorage()


def seed_initial_data() -> None:
    """Pre-seed sample students, instructors, and assignments for immediate out-of-the-box use."""
    # 1. Student Demo Account
    student_pw = PasswordHasher.hash_password("studentPassword123")
    student_user = UserAccount(
        user_id="student_ada",
        email="ada@university.edu",
        hashed_password=student_pw,
        role=UserRole.STUDENT,
        name="Ada Lovelace",
    )
    shared_user_store.save(student_user)
    shared_student_store.save(
        Student(student_id="student_ada", name="Ada Lovelace", email="ada@university.edu")
    )

    # 2. Instructor Demo Account
    instructor_pw = PasswordHasher.hash_password("instructorPassword123")
    instructor_user = UserAccount(
        user_id="prof_turing",
        email="turing@university.edu",
        hashed_password=instructor_pw,
        role=UserRole.INSTRUCTOR,
        name="Prof. Alan Turing",
    )
    shared_user_store.save(instructor_user)
    shared_instructor_store.save(
        Instructor(instructor_id="prof_turing", name="Prof. Alan Turing", email="turing@university.edu")
    )

    # 3. Seed Sample Assignments
    asgn1 = AssignmentDefinition(
        task_id="binary_search_hw",
        title="Binary Search Algorithm Implementation",
        test_cases=(
            TestCaseDefinition(
                test_case_id="tc1_sorted_array",
                description="Find element in middle, start, and end of sorted array",
                points=30,
            ),
            TestCaseDefinition(
                test_case_id="tc2_element_not_found",
                description="Return -1 when target is absent from array",
                points=30,
            ),
            TestCaseDefinition(
                test_case_id="tc3_edge_cases",
                description="Handle empty lists and single-element lists without IndexError",
                points=40,
            ),
        ),
        instructor_id="prof_turing",
    )
    shared_assignment_store.save(asgn1)

    asgn2 = AssignmentDefinition(
        task_id="palindrome_check",
        title="Palindrome String Verifier",
        test_cases=(
            TestCaseDefinition(
                test_case_id="tc1_simple_words",
                description="Check standard palindromes like 'racecar' and 'level'",
                points=50,
            ),
            TestCaseDefinition(
                test_case_id="tc2_alphanumeric_phrase",
                description="Check sentences ignoring spaces and casing like 'A man a plan a canal Panama'",
                points=50,
            ),
        ),
        instructor_id="prof_turing",
    )
    shared_assignment_store.save(asgn2)

    # 4. Seed Rubric for binary_search_hw
    rubric1 = GradingRubric(
        rubric_id="binary_search_hw",
        title="Binary Search Rubric",
        criteria=(
            RubricCriterion(
                criterion_id="algorithmic_correctness",
                name="Algorithmic Logic",
                description="O(log n) divide-and-conquer implementation without infinite loops",
                max_points=40,
            ),
            RubricCriterion(
                criterion_id="code_style_pep8",
                name="PEP8 Cleanliness",
                description="Descriptive variable naming, type hints, and clean structure",
                max_points=30,
            ),
            RubricCriterion(
                criterion_id="boundary_handling",
                name="Boundary Defenses",
                description="Zero division, empty array, and integer overflow precautions",
                max_points=30,
            ),
        ),
    )
    shared_rubric_store.save(rubric1)


# Seed upon module load
seed_initial_data()


