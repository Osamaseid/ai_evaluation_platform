"""Shared persistent store and storage singletons for the FastAPI runtime."""

from datetime import datetime, timezone
from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.auth.models import UserAccount, UserRole
from evaluator.auth.security import PasswordHasher
from evaluator.evaluation import EvaluationReport, EvaluationStatus
from evaluator.grading import GradingReport, TestCaseResult
from evaluator.metadata import SubmissionMetadata
from evaluator.rubric import GradingRubric, RubricCriterion, RubricEvaluation
from evaluator.storage.submission_storage import ControlledFileStorage
from evaluator.stores.assignment_store import InMemoryAssignmentStore
from evaluator.stores.evaluation_store import InMemoryEvaluationStore
from evaluator.stores.instructor_store import InMemoryInstructorStore
from evaluator.stores.rubric_store import InMemoryRubricStore
from evaluator.stores.student_store import InMemoryStudentStore
from evaluator.stores.submission_store import InMemorySubmissionStore
from evaluator.stores.user_store import InMemoryUserStore
from evaluator.submission import SubmissionRecord, SubmissionSource, SubmissionStatus
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
    """Pre-seed sample students, instructors, assignments, rubrics, submissions, and evaluations."""
    now = datetime.now(timezone.utc)
    student_pw = PasswordHasher.hash_password("studentPassword123")
    instructor_pw = PasswordHasher.hash_password("instructorPassword123")

    # -----------------------------------------------------------------------
    # 1. Instructors
    # -----------------------------------------------------------------------
    instructors_data = [
        ("prof_turing", "Prof. Alan Turing", "turing@university.edu"),
        ("prof_neumann", "Prof. John von Neumann", "neumann@university.edu"),
    ]
    for uid, name, email in instructors_data:
        shared_user_store.save(
            UserAccount(
                user_id=uid,
                email=email,
                hashed_password=instructor_pw,
                role=UserRole.INSTRUCTOR,
                name=name,
            )
        )
        shared_instructor_store.save(
            Instructor(instructor_id=uid, name=name, email=email)
        )

    # -----------------------------------------------------------------------
    # 2. Students
    # -----------------------------------------------------------------------
    students_data = [
        ("student_ada", "Ada Lovelace", "ada@university.edu"),
        ("student_grace", "Grace Hopper", "hopper@university.edu"),
        ("student_linus", "Linus Torvalds", "linus@university.edu"),
        ("student_margaret", "Margaret Hamilton", "hamilton@university.edu"),
        ("student_donald", "Donald Knuth", "knuth@university.edu"),
        ("student_shannon", "Claude Shannon", "shannon@university.edu"),
        ("student_katherine", "Katherine Johnson", "johnson@university.edu"),
        ("student_alan", "Alan Turing Jr.", "turing_jr@university.edu"),
    ]
    for sid, name, email in students_data:
        shared_user_store.save(
            UserAccount(
                user_id=sid,
                email=email,
                hashed_password=student_pw,
                role=UserRole.STUDENT,
                name=name,
            )
        )
        shared_student_store.save(
            Student(student_id=sid, name=name, email=email)
        )

    # -----------------------------------------------------------------------
    # 3. Assignments
    # -----------------------------------------------------------------------
    asgn_binary = AssignmentDefinition(
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
    shared_assignment_store.save(asgn_binary)

    asgn_palindrome = AssignmentDefinition(
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
    shared_assignment_store.save(asgn_palindrome)

    asgn_twosum = AssignmentDefinition(
        task_id="two_sum_hash",
        title="Two Sum with Linear Hash Map",
        test_cases=(
            TestCaseDefinition(
                test_case_id="tc1_standard_pair",
                description="Locate two indices summing to target in standard array",
                points=40,
            ),
            TestCaseDefinition(
                test_case_id="tc2_duplicate_elements",
                description="Handle duplicate values like [3, 3] target 6",
                points=30,
            ),
            TestCaseDefinition(
                test_case_id="tc3_negative_integers",
                description="Handle positive and negative combinations like [-1, -2, -3, -4, -5] target -8",
                points=30,
            ),
        ),
        instructor_id="prof_turing",
    )
    shared_assignment_store.save(asgn_twosum)

    asgn_linked = AssignmentDefinition(
        task_id="linked_list_reversal",
        title="Singly Linked List In-Place Reversal",
        test_cases=(
            TestCaseDefinition(
                test_case_id="tc1_multi_node_list",
                description="Reverse standard linked list of length 5",
                points=40,
            ),
            TestCaseDefinition(
                test_case_id="tc2_single_and_empty",
                description="Handle empty list and 1-element list",
                points=30,
            ),
            TestCaseDefinition(
                test_case_id="tc3_memory_no_copies",
                description="Verify O(1) memory usage by checking pointer mutations",
                points=30,
            ),
        ),
        instructor_id="prof_turing",
    )
    shared_assignment_store.save(asgn_linked)

    asgn_intervals = AssignmentDefinition(
        task_id="merge_intervals",
        title="Interval Scheduling & Merge Overlaps",
        test_cases=(
            TestCaseDefinition(
                test_case_id="tc1_overlapping_pairs",
                description="Merge overlapping pairs [[1,3],[2,6],[8,10],[15,18]]",
                points=35,
            ),
            TestCaseDefinition(
                test_case_id="tc2_already_disjoint",
                description="Keep non-overlapping intervals untouched [[1,2],[3,4]]",
                points=35,
            ),
            TestCaseDefinition(
                test_case_id="tc3_contained_subinterval",
                description="Merge nested interval [[1,4],[2,3]] -> [[1,4]]",
                points=30,
            ),
        ),
        instructor_id="prof_neumann",
    )
    shared_assignment_store.save(asgn_intervals)

    # -----------------------------------------------------------------------
    # 4. Grading Rubrics
    # -----------------------------------------------------------------------
    shared_rubric_store.save(
        GradingRubric(
            rubric_id="binary_search_hw",
            title="Binary Search Evaluation Rubric",
            criteria=(
                RubricCriterion(
                    criterion_id="algorithmic_correctness",
                    name="Algorithmic Logic (O(log n))",
                    description="O(log n) divide-and-conquer implementation without infinite loops",
                    max_points=40,
                ),
                RubricCriterion(
                    criterion_id="code_style_pep8",
                    name="PEP 8 & Clean Code",
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
    )

    shared_rubric_store.save(
        GradingRubric(
            rubric_id="palindrome_check",
            title="Palindrome Verifier Rubric",
            criteria=(
                RubricCriterion(
                    criterion_id="normalization_logic",
                    name="Punctuation & Case Normalization",
                    description="Proper alphanumeric filtering using isalnum() and lower()",
                    max_points=50,
                ),
                RubricCriterion(
                    criterion_id="space_efficiency",
                    name="Two-Pointer Space Efficiency",
                    description="O(1) auxiliary memory using left/right pointers",
                    max_points=50,
                ),
            ),
        )
    )

    # -----------------------------------------------------------------------
    # 5. Submissions & Evaluations
    # -----------------------------------------------------------------------
    # Sub 1: Ada Lovelace - binary_search_hw (Score 100 deterministic, override 95)
    sub1 = SubmissionRecord(
        submission_id="sub_ada_001",
        metadata=SubmissionMetadata(student_id="student_ada", task_id="binary_search_hw"),
        source_type=SubmissionSource.GITHUB,
        source_reference="https://github.com/ada-lovelace/algorithms-hw",
        status=SubmissionStatus.COMPLETED,
        submitted_at=now,
        source_code="def search(nums: list[int], target: int) -> int:\n    low, high = 0, len(nums) - 1\n    while low <= high:\n        mid = low + (high - low) // 2\n        if nums[mid] == target:\n            return mid\n        elif nums[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n",
    )
    shared_submission_store.save(sub1)

    eval1 = EvaluationReport(
        evaluation_id="eval_ada_001",
        submission_id="sub_ada_001",
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=100,
            max_score=100,
            passed_tests=3,
            total_tests=3,
        ),
        test_results=(
            TestCaseResult(test_case_id="tc1_sorted_array", passed=True, message="Target element located at index 4"),
            TestCaseResult(test_case_id="tc2_element_not_found", passed=True, message="Returned -1 for absent value"),
            TestCaseResult(test_case_id="tc3_edge_cases", passed=True, message="Empty list and boundary handled safely"),
        ),
        manual_override_score=95,
        instructor_notes="Exceptional divide-and-conquer implementation! Midpoint calculation prevents overflow. Awarded bonus points for clean PEP 484 type annotations.",
        reviewed_by="prof_turing",
        reviewed_at=now,
        structured_feedback={
            "summary": "Outstanding binary search implementation demonstrating O(log n) algorithmic efficiency and defensive programming.",
            "strengths": [
                "Used low + (high - low) // 2 avoiding arithmetic overflow",
                "PEP 8 clean naming and explicit PEP 484 type hints",
                "Clean termination handling on empty arrays",
            ],
            "weaknesses": [
                "Could document time complexity in function docstrings",
            ],
            "observations": [
                {
                    "category": "code_quality",
                    "severity": "info",
                    "title": "Overflow-Safe Midpoint Calculation",
                    "description": "Used low + (high - low) // 2 which prevents arithmetic overflow on large arrays.",
                    "code_evidence": "mid = low + (high - low) // 2",
                    "suggestion": "Maintain this defensive pattern throughout numerical algorithms.",
                },
                {
                    "category": "maintainability",
                    "severity": "info",
                    "title": "PEP 484 Type Annotations",
                    "description": "Adding explicit list[int] and int types improves IDE autocomplete and static verification.",
                    "code_evidence": "def search(nums: list[int], target: int) -> int:",
                    "suggestion": "Include Google-style or Sphinx docstring annotations.",
                },
            ],
        },
        ai_review="Outstanding binary search implementation with clean O(log n) complexity.",
        evaluated_at=now,
    )
    shared_evaluation_store.save(eval1)

    # Sub 2: Ada Lovelace - palindrome_check (Score 100)
    sub2 = SubmissionRecord(
        submission_id="sub_ada_002",
        metadata=SubmissionMetadata(student_id="student_ada", task_id="palindrome_check"),
        source_type=SubmissionSource.FILE_UPLOAD,
        source_reference="palindrome_solution.py",
        status=SubmissionStatus.COMPLETED,
        submitted_at=now,
        source_code="def is_palindrome(s: str) -> bool:\n    left, right = 0, len(s) - 1\n    while left < right:\n        while left < right and not s[left].isalnum():\n            left += 1\n        while left < right and not s[right].isalnum():\n            right -= 1\n        if s[left].lower() != s[right].lower():\n            return False\n        left += 1\n        right -= 1\n    return True\n",
    )
    shared_submission_store.save(sub2)

    eval2 = EvaluationReport(
        evaluation_id="eval_ada_002",
        submission_id="sub_ada_002",
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=100,
            max_score=100,
            passed_tests=2,
            total_tests=2,
        ),
        test_results=(
            TestCaseResult(test_case_id="tc1_simple_words", passed=True, message="Verified racecar and level"),
            TestCaseResult(test_case_id="tc2_alphanumeric_phrase", passed=True, message="Handled sentence punctuation correctly"),
        ),
        structured_feedback={
            "summary": "Clean two-pointer approach achieving true O(1) auxiliary space without creating duplicate strings.",
            "strengths": [
                "Two-pointer traversal skipping non-alphanumeric characters in-place",
                "O(1) memory allocation",
            ],
            "weaknesses": [],
            "observations": [
                {
                    "category": "performance",
                    "severity": "info",
                    "title": "In-place Two Pointer Traversal",
                    "description": "Checking characters in-place avoids extra string allocation in memory.",
                    "code_evidence": "while left < right and not s[left].isalnum():",
                    "suggestion": "Optimal approach for large stream inputs.",
                }
            ],
        },
        ai_review="Clean two-pointer approach achieving O(1) auxiliary space.",
        evaluated_at=now,
    )
    shared_evaluation_store.save(eval2)

    # Sub 3: Ada Lovelace - two_sum_hash (Score 100)
    sub3 = SubmissionRecord(
        submission_id="sub_ada_003",
        metadata=SubmissionMetadata(student_id="student_ada", task_id="two_sum_hash"),
        source_type=SubmissionSource.GITHUB,
        source_reference="https://github.com/ada-lovelace/two-sum",
        status=SubmissionStatus.COMPLETED,
        submitted_at=now,
        source_code="def two_sum(nums: list[int], target: int) -> list[int]:\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []\n",
    )
    shared_submission_store.save(sub3)

    eval3 = EvaluationReport(
        evaluation_id="eval_ada_003",
        submission_id="sub_ada_003",
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=100,
            max_score=100,
            passed_tests=3,
            total_tests=3,
        ),
        test_results=(
            TestCaseResult(test_case_id="tc1_standard_pair", passed=True, message="Found pair summing to 9"),
            TestCaseResult(test_case_id="tc2_duplicate_elements", passed=True, message="Handled duplicate numbers [3,3]"),
            TestCaseResult(test_case_id="tc3_negative_integers", passed=True, message="Negative values verified"),
        ),
        structured_feedback={
            "summary": "Optimal single-pass dictionary lookup with O(n) runtime and clean index resolution.",
            "strengths": ["Single-pass hash table lookup", "Handles duplicates seamlessly"],
            "weaknesses": [],
            "observations": [],
        },
        ai_review="Optimal single-pass dictionary lookup with O(n) runtime.",
        evaluated_at=now,
    )
    shared_evaluation_store.save(eval3)

    # Sub 4: Grace Hopper - binary_search_hw (Score 100)
    sub4 = SubmissionRecord(
        submission_id="sub_grace_001",
        metadata=SubmissionMetadata(student_id="student_grace", task_id="binary_search_hw"),
        source_type=SubmissionSource.GITHUB,
        source_reference="https://github.com/grace-hopper/binary-search",
        status=SubmissionStatus.COMPLETED,
        submitted_at=now,
    )
    shared_submission_store.save(sub4)

    eval4 = EvaluationReport(
        evaluation_id="eval_grace_001",
        submission_id="sub_grace_001",
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=100,
            max_score=100,
            passed_tests=3,
            total_tests=3,
        ),
        test_results=(
            TestCaseResult(test_case_id="tc1_sorted_array", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc2_element_not_found", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc3_edge_cases", passed=True, message="Passed"),
        ),
        evaluated_at=now,
    )
    shared_evaluation_store.save(eval4)

    # Sub 5: Grace Hopper - linked_list_reversal (Score 100)
    sub5 = SubmissionRecord(
        submission_id="sub_grace_002",
        metadata=SubmissionMetadata(student_id="student_grace", task_id="linked_list_reversal"),
        source_type=SubmissionSource.FILE_UPLOAD,
        source_reference="linked_list.py",
        status=SubmissionStatus.COMPLETED,
        submitted_at=now,
    )
    shared_submission_store.save(sub5)

    eval5 = EvaluationReport(
        evaluation_id="eval_grace_002",
        submission_id="sub_grace_002",
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=100,
            max_score=100,
            passed_tests=3,
            total_tests=3,
        ),
        test_results=(
            TestCaseResult(test_case_id="tc1_multi_node_list", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc2_single_and_empty", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc3_memory_no_copies", passed=True, message="Passed"),
        ),
        evaluated_at=now,
    )
    shared_evaluation_store.save(eval5)

    # Sub 6: Linus Torvalds - binary_search_hw (Score 60 deterministic, override 70)
    sub6 = SubmissionRecord(
        submission_id="sub_linus_001",
        metadata=SubmissionMetadata(student_id="student_linus", task_id="binary_search_hw"),
        source_type=SubmissionSource.GITHUB,
        source_reference="https://github.com/torvalds/binary-search-c",
        status=SubmissionStatus.COMPLETED,
        submitted_at=now,
    )
    shared_submission_store.save(sub6)

    eval6 = EvaluationReport(
        evaluation_id="eval_linus_001",
        submission_id="sub_linus_001",
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=60,
            max_score=100,
            passed_tests=2,
            total_tests=3,
        ),
        test_results=(
            TestCaseResult(test_case_id="tc1_sorted_array", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc2_element_not_found", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc3_edge_cases", passed=False, message="IndexError on empty array len=0"),
        ),
        manual_override_score=70,
        instructor_notes="Clean core algorithm; partial credit awarded for recursion, but remember to validate empty arrays.",
        reviewed_by="prof_turing",
        reviewed_at=now,
        evaluated_at=now,
    )
    shared_evaluation_store.save(eval6)

    # Sub 7: Linus Torvalds - merge_intervals (Score 100)
    sub7 = SubmissionRecord(
        submission_id="sub_linus_002",
        metadata=SubmissionMetadata(student_id="student_linus", task_id="merge_intervals"),
        source_type=SubmissionSource.FILE_UPLOAD,
        source_reference="intervals.py",
        status=SubmissionStatus.COMPLETED,
        submitted_at=now,
    )
    shared_submission_store.save(sub7)

    eval7 = EvaluationReport(
        evaluation_id="eval_linus_002",
        submission_id="sub_linus_002",
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=100,
            max_score=100,
            passed_tests=3,
            total_tests=3,
        ),
        test_results=(
            TestCaseResult(test_case_id="tc1_overlapping_pairs", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc2_already_disjoint", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc3_contained_subinterval", passed=True, message="Passed"),
        ),
        evaluated_at=now,
    )
    shared_evaluation_store.save(eval7)

    # Sub 8: Margaret Hamilton - binary_search_hw (Score 100)
    sub8 = SubmissionRecord(
        submission_id="sub_margaret_001",
        metadata=SubmissionMetadata(student_id="student_margaret", task_id="binary_search_hw"),
        source_type=SubmissionSource.FILE_UPLOAD,
        source_reference="apollo_binary_search.py",
        status=SubmissionStatus.COMPLETED,
        submitted_at=now,
    )
    shared_submission_store.save(sub8)

    eval8 = EvaluationReport(
        evaluation_id="eval_margaret_001",
        submission_id="sub_margaret_001",
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=100,
            max_score=100,
            passed_tests=3,
            total_tests=3,
        ),
        test_results=(
            TestCaseResult(test_case_id="tc1_sorted_array", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc2_element_not_found", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc3_edge_cases", passed=True, message="Passed"),
        ),
        evaluated_at=now,
    )
    shared_evaluation_store.save(eval8)

    # Sub 9: Donald Knuth - binary_search_hw (Score 70 deterministic, override 75)
    sub9 = SubmissionRecord(
        submission_id="sub_donald_001",
        metadata=SubmissionMetadata(student_id="student_donald", task_id="binary_search_hw"),
        source_type=SubmissionSource.GITHUB,
        source_reference="https://github.com/knuth/art-of-programming",
        status=SubmissionStatus.COMPLETED,
        submitted_at=now,
    )
    shared_submission_store.save(sub9)

    eval9 = EvaluationReport(
        evaluation_id="eval_donald_001",
        submission_id="sub_donald_001",
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=70,
            max_score=100,
            passed_tests=2,
            total_tests=3,
        ),
        test_results=(
            TestCaseResult(test_case_id="tc1_sorted_array", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc2_element_not_found", passed=False, message="Returned 0 instead of -1"),
            TestCaseResult(test_case_id="tc3_edge_cases", passed=True, message="Passed"),
        ),
        manual_override_score=75,
        instructor_notes="Careful with return values on missing items; awarded +5 points for mathematical rigor.",
        reviewed_by="prof_turing",
        reviewed_at=now,
        evaluated_at=now,
    )
    shared_evaluation_store.save(eval9)

    # Sub 10: Katherine Johnson - palindrome_check (Score 100)
    sub10 = SubmissionRecord(
        submission_id="sub_katherine_001",
        metadata=SubmissionMetadata(student_id="student_katherine", task_id="palindrome_check"),
        source_type=SubmissionSource.FILE_UPLOAD,
        source_reference="orbital_palindrome.py",
        status=SubmissionStatus.COMPLETED,
        submitted_at=now,
    )
    shared_submission_store.save(sub10)

    eval10 = EvaluationReport(
        evaluation_id="eval_katherine_001",
        submission_id="sub_katherine_001",
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=100,
            max_score=100,
            passed_tests=2,
            total_tests=2,
        ),
        test_results=(
            TestCaseResult(test_case_id="tc1_simple_words", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc2_alphanumeric_phrase", passed=True, message="Passed"),
        ),
        evaluated_at=now,
    )
    shared_evaluation_store.save(eval10)

    # Sub 11: Claude Shannon - two_sum_hash (Score 90)
    sub11 = SubmissionRecord(
        submission_id="sub_shannon_001",
        metadata=SubmissionMetadata(student_id="student_shannon", task_id="two_sum_hash"),
        source_type=SubmissionSource.GITHUB,
        source_reference="https://github.com/shannon/information-theory",
        status=SubmissionStatus.COMPLETED,
        submitted_at=now,
    )
    shared_submission_store.save(sub11)

    eval11 = EvaluationReport(
        evaluation_id="eval_shannon_001",
        submission_id="sub_shannon_001",
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=90,
            max_score=100,
            passed_tests=3,
            total_tests=3,
        ),
        test_results=(
            TestCaseResult(test_case_id="tc1_standard_pair", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc2_duplicate_elements", passed=True, message="Passed"),
            TestCaseResult(test_case_id="tc3_negative_integers", passed=True, message="Passed"),
        ),
        evaluated_at=now,
    )
    shared_evaluation_store.save(eval11)

    # Sub 12: Alan Turing Jr. - In-flight submission (VALIDATED / EVALUATING)
    sub12 = SubmissionRecord(
        submission_id="sub_alan_001",
        metadata=SubmissionMetadata(student_id="student_alan", task_id="binary_search_hw"),
        source_type=SubmissionSource.GITHUB,
        source_reference="https://github.com/turing-jr/enigma-search",
        status=SubmissionStatus.VALIDATED,
        submitted_at=now,
    )
    shared_submission_store.save(sub12)


# Seed upon module load
seed_initial_data()
