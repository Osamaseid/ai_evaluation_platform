/**
 * Fully typed HTTP client integrating with the FastAPI backend.
 */

import {
  Assignment,
  EvaluationReport,
  GradingRubric,
  Instructor,
  PaginatedResponse,
  Student,
  Submission,
  SubmissionStatusResponse,
  TokenResponse,
  UserAccount,
} from '../types/api';

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || '';

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('autograde_token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('autograde_token', token);
    } else {
      localStorage.removeItem('autograde_token');
      localStorage.removeItem('autograde_user');
    }
  }

  getToken(): string | null {
    return this.token || localStorage.getItem('autograde_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = new Headers(options.headers || {});

    // Attach Bearer token if available
    const activeToken = this.getToken();
    if (activeToken && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${activeToken}`);
    }

    // Default JSON Content-Type unless FormData
    if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 204) {
      return {} as T;
    }

    let data: any;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      let message = 'An unexpected API error occurred.';
      if (typeof data === 'object' && data !== null) {
        if (data.error && data.error.message) {
          message = data.error.message;
        } else if (data.detail) {
          if (Array.isArray(data.detail)) {
            message = data.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
          } else {
            message = String(data.detail);
          }
        }
      } else if (typeof data === 'string' && data) {
        message = data;
      }

      if (response.status === 401 && !endpoint.includes('/auth/login')) {
        this.setToken(null);
      }

      const error = new Error(message) as Error & { status: number; data: any };
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data as T;
  }

  // -------------------------------------------------------------------------
  // Authentication & User Profile
  // -------------------------------------------------------------------------

  async register(payload: {
    user_id: string;
    email: string;
    password: string;
    role: 'student' | 'instructor';
    name: string;
  }): Promise<UserAccount> {
    return this.request<UserAccount>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async login(payload: {
    email_or_user_id: string;
    password: string;
  }): Promise<TokenResponse> {
    const res = await this.request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    this.setToken(res.access_token);
    localStorage.setItem('autograde_user', JSON.stringify(res));
    return res;
  }

  async logout(): Promise<void> {
    try {
      await this.request<void>('/auth/logout', { method: 'POST' });
    } finally {
      this.setToken(null);
    }
  }

  async getCurrentUser(): Promise<UserAccount> {
    return this.request<UserAccount>('/auth/me');
  }

  async changePassword(payload: {
    old_password: string;
    new_password: string;
  }): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/password', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // -------------------------------------------------------------------------
  // Students
  // -------------------------------------------------------------------------

  async getMyStudentProfile(): Promise<Student> {
    return this.request<Student>('/students/me');
  }

  async getStudent(studentId: string): Promise<Student> {
    return this.request<Student>(`/students/${encodeURIComponent(studentId)}`);
  }

  async getStudentSubmissions(
    studentId: string,
    limit = 10,
    offset = 0
  ): Promise<PaginatedResponse<Submission>> {
    return this.request<PaginatedResponse<Submission>>(
      `/students/${encodeURIComponent(studentId)}/submissions?limit=${limit}&offset=${offset}`
    );
  }

  async getStudentEvaluations(
    studentId: string,
    limit = 10,
    offset = 0
  ): Promise<PaginatedResponse<EvaluationReport>> {
    return this.request<PaginatedResponse<EvaluationReport>>(
      `/students/${encodeURIComponent(studentId)}/evaluations?limit=${limit}&offset=${offset}`
    );
  }

  // -------------------------------------------------------------------------
  // Instructors
  // -------------------------------------------------------------------------

  async getMyInstructorProfile(): Promise<Instructor> {
    return this.request<Instructor>('/instructors/me');
  }

  async getInstructor(instructorId: string): Promise<Instructor> {
    return this.request<Instructor>(`/instructors/${encodeURIComponent(instructorId)}`);
  }

  async listStudents(limit = 50, offset = 0): Promise<PaginatedResponse<Student>> {
    return this.request<PaginatedResponse<Student>>(
      `/instructors/students?limit=${limit}&offset=${offset}`
    );
  }

  async enrollStudent(payload: {
    student_id: string;
    name: string;
    email: string;
  }): Promise<Student> {
    return this.request<Student>('/instructors/students', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listInstructorAssignments(): Promise<Assignment[]> {
    return this.request<Assignment[]>('/instructors/assignments');
  }

  async createInstructorAssignment(payload: {
    task_id: string;
    title: string;
    description?: string;
    test_cases: Array<{
      test_case_id: string;
      description: string;
      points: number;
    }>;
    max_score?: number;
  }): Promise<Assignment> {
    return this.request<Assignment>('/instructors/assignments', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateInstructorAssignment(
    taskId: string,
    payload: {
      task_id?: string;
      title: string;
      description?: string;
      test_cases: Array<{
        test_case_id: string;
        description: string;
        points: number;
      }>;
      max_score?: number;
    }
  ): Promise<Assignment> {
    return this.request<Assignment>(`/instructors/assignments/${encodeURIComponent(taskId)}`, {
      method: 'PUT',
      body: JSON.stringify({ ...payload, task_id: taskId }),
    });
  }

  async createRubric(payload: {
    task_id: string;
    criteria: Array<{
      criterion_id: string;
      name: string;
      description: string;
      max_points: number;
      weight: number;
    }>;
  }): Promise<GradingRubric> {
    return this.request<GradingRubric>('/instructors/rubrics', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getRubric(taskId: string): Promise<GradingRubric> {
    return this.request<GradingRubric>(`/instructors/rubrics/${encodeURIComponent(taskId)}`);
  }

  async listInstructorEvaluations(taskId?: string): Promise<EvaluationReport[]> {
    const query = taskId ? `?task_id=${encodeURIComponent(taskId)}` : '';
    return this.request<EvaluationReport[]>(`/instructors/evaluations${query}`);
  }

  async applyManualReview(
    evaluationId: string,
    payload: {
      manual_override_score?: number | null;
      instructor_notes?: string | null;
      rubric_evaluations?: Record<string, { criterion_id: string; score: number; comment: string }> | null;
    }
  ): Promise<{ message: string; evaluation_id: string; final_score: number }> {
    return this.request<{ message: string; evaluation_id: string; final_score: number }>(
      `/instructors/evaluations/${encodeURIComponent(evaluationId)}/manual-review`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  }

  // -------------------------------------------------------------------------
  // Assignments (Catalog)
  // -------------------------------------------------------------------------

  async listAssignments(): Promise<Assignment[]> {
    return this.request<Assignment[]>('/assignments');
  }

  // -------------------------------------------------------------------------
  // Submissions
  // -------------------------------------------------------------------------

  async submitGitHub(payload: {
    student_id: string;
    task_id: string;
    repo_url: string;
    branch?: string;
    commit_sha?: string;
    github_token?: string;
  }): Promise<Submission> {
    return this.request<Submission>('/submissions/github', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async submitFileUpload(
    file: File,
    studentId: string,
    taskId: string
  ): Promise<Submission> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('student_id', studentId);
    formData.append('task_id', taskId);

    return this.request<Submission>('/submissions/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async getSubmission(submissionId: string): Promise<Submission> {
    return this.request<Submission>(`/submissions/${encodeURIComponent(submissionId)}`);
  }

  async getSubmissionStatus(submissionId: string): Promise<SubmissionStatusResponse> {
    return this.request<SubmissionStatusResponse>(
      `/submissions/${encodeURIComponent(submissionId)}/status`
    );
  }

  async getSubmissionHistory(submissionId: string): Promise<any> {
    return this.request<any>(`/submissions/${encodeURIComponent(submissionId)}/history`);
  }

  // -------------------------------------------------------------------------
  // Evaluations
  // -------------------------------------------------------------------------

  async runEvaluation(submissionId: string): Promise<EvaluationReport> {
    return this.request<EvaluationReport>(
      `/evaluations/run/${encodeURIComponent(submissionId)}`,
      { method: 'POST' }
    );
  }

  async getEvaluation(evaluationId: string): Promise<EvaluationReport> {
    return this.request<EvaluationReport>(`/evaluations/${encodeURIComponent(evaluationId)}`);
  }

  async getEvaluationBySubmission(submissionId: string): Promise<EvaluationReport> {
    return this.request<EvaluationReport>(
      `/evaluations/by-submission/${encodeURIComponent(submissionId)}`
    );
  }

  async getEvaluationStatus(evaluationId: string): Promise<any> {
    return this.request<any>(`/evaluations/${encodeURIComponent(evaluationId)}/status`);
  }

  async getEvaluationTests(evaluationId: string): Promise<any> {
    return this.request<any>(`/evaluations/${encodeURIComponent(evaluationId)}/tests`);
  }

  async getEvaluationAiFeedback(evaluationId: string): Promise<any> {
    return this.request<any>(`/evaluations/${encodeURIComponent(evaluationId)}/ai-feedback`);
  }

  async getEvaluationReport(evaluationId: string): Promise<EvaluationReport> {
    return this.request<EvaluationReport>(`/evaluations/${encodeURIComponent(evaluationId)}/report`);
  }

  async checkHealth(): Promise<{ status: string; service: string }> {
    return this.request<{ status: string; service: string }>('/health');
  }
}

export const api = new ApiClient();
