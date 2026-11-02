/**
 * TypeScript API interfaces matching FastAPI backend schemas.
 */

export type UserRole = 'student' | 'instructor' | 'admin';

export interface UserAccount {
  user_id: string;
  email: string;
  role: UserRole;
  name: string;
  is_active: boolean;
  created_at: string;
  last_login_at?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  role: UserRole;
  name: string;
}

export interface Student {
  student_id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface Instructor {
  instructor_id: string;
  name: string;
  email: string;
  department?: string;
  created_at: string;
}

export interface TestCase {
  test_case_id: string;
  description: string;
  points: number;
  input_data?: string;
  expected_output?: string;
  is_hidden?: boolean;
  timeout_seconds?: number;
}

export interface Assignment {
  task_id: string;
  title: string;
  description?: string;
  max_score: number;
  deadline?: string | null;
  test_cases: TestCase[];
}

export interface RubricCriterion {
  criterion_id: string;
  name: string;
  description: string;
  max_points: number;
  weight: number;
}

export interface GradingRubric {
  task_id: string;
  criteria: RubricCriterion[];
}

export interface RubricEvaluation {
  criterion_id: string;
  score: number;
  comment: string;
}

export type SubmissionStatus =
  | 'received'
  | 'submitted'
  | 'validating'
  | 'running_tests'
  | 'reviewing_code'
  | 'grading'
  | 'evaluated'
  | 'completed'
  | 'failed';

export interface Submission {
  submission_id: string;
  student_id: string;
  task_id: string;
  source_type: 'github' | 'upload' | string;
  source_reference: string;
  status: SubmissionStatus;
  created_at: string;
}

export interface SubmissionStatusResponse {
  submission_id: string;
  task_id: string;
  student_id: string;
  status: SubmissionStatus;
  source_type: string;
  created_at: string;
  evaluation_id?: string | null;
}

export interface TestCaseResult {
  test_case_id: string;
  passed: boolean;
  execution_time_ms?: number;
  message?: string;
  stdout?: string;
  stderr?: string;
  return_code?: number;
}

export interface GradingReport {
  earned_points: number;
  max_score: number;
  passed_tests: number;
  total_tests: number;
  score_percentage: number;
  test_case_results: TestCaseResult[];
}

export interface AIObservation {
  category: 'logical_mistake' | 'code_quality' | 'readability' | 'maintainability' | 'potential_bug' | 'edge_case' | 'improvement';
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  code_evidence?: string;
  suggestion?: string;
}

export interface AIReviewReport {
  summary: string;
  strengths: string[];
  weaknesses: string[];
  observations: AIObservation[];
}

export interface EvaluationReport {
  evaluation_id: string;
  submission_id: string;
  student_id: string;
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial_failure';
  deterministic_score: number;
  max_score: number;
  grading_report?: GradingReport | null;
  ai_review?: AIReviewReport | null;
  rubric_evaluations?: Record<string, RubricEvaluation> | null;
  instructor_notes?: string | null;
  manual_override_score?: number | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  started_at: string;
  completed_at?: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    status_code: number;
  };
  detail?: string | Array<{ msg: string; loc: string[] }>;
}

