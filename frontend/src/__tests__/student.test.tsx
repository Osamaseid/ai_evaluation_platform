import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ToastProvider } from '../context/ToastContext';
import { AuthProvider } from '../context/AuthContext';
import { StudentOverview } from '../components/student/StudentOverview';
import { AssignmentList } from '../components/student/AssignmentList';
import { SubmitAssignmentModal } from '../components/student/SubmitAssignmentModal';
import { EvaluationDetailView } from '../components/student/EvaluationDetailView';
import { EvaluationReport } from '../types/api';
import { api } from '../services/api';

describe('Student Dashboard Components', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('renders EvaluationDetailView with deterministic score, test cases, and Gemini AI review', () => {
    const mockReport: EvaluationReport = {
      evaluation_id: 'eval_123456',
      submission_id: 'sub_987654',
      student_id: 'student_ada',
      task_id: 'binary_search_hw',
      status: 'completed',
      deterministic_score: 90,
      max_score: 100,
      grading_report: {
        earned_points: 90,
        max_score: 100,
        passed_tests: 2,
        total_tests: 2,
        score_percentage: 90,
        test_case_results: [
          {
            test_case_id: 'tc1_sorted_array',
            passed: true,
            execution_time_ms: 12,
            message: 'Target element located at index 4',
          },
          {
            test_case_id: 'tc2_empty_and_single',
            passed: true,
            execution_time_ms: 8,
            message: 'Boundary condition handled',
          },
        ],
      },
      ai_review: {
        summary: 'Excellent binary search implementation with clean O(log n) complexity.',
        strengths: ['Optimal mid calculation avoiding integer overflow', 'Consistent variable naming'],
        weaknesses: ['Could document edge case returns in docstrings'],
        observations: [
          {
            category: 'code_quality',
            title: 'Overflow-safe midpoint computation',
            description: 'Used low + (high - low) // 2 which prevents arithmetic overflow.',
            severity: 'low',
            suggestion: 'Maintain this pattern throughout numerical algorithms.',
          },
        ],
      },
      rubric_evaluations: {
        code_style: {
          criterion_id: 'code_style',
          score: 20,
          comment: 'Follows PEP8 conventions faithfully.',
        },
      },
      instructor_notes: 'Well done Ada! Solid algorithm structure.',
      manual_override_score: 95,
      reviewed_by: 'prof_turing',
      reviewed_at: '2026-11-01T10:00:00Z',
      started_at: '2026-11-01T09:59:00Z',
      completed_at: '2026-11-01T09:59:05Z',
    };

    render(<EvaluationDetailView report={mockReport} />);

    // Score Banner
    expect(screen.getByText('Assignment: binary_search_hw')).toBeInTheDocument();
    expect(screen.getByText('Instructor Overridden')).toBeInTheDocument();
    expect(screen.getAllByText('95').length).toBeGreaterThanOrEqual(1); // Manual override score

    // Instructor feedback
    expect(screen.getByText(/Well done Ada!/)).toBeInTheDocument();

    // Automated Test Results tab
    expect(screen.getByText('tc1_sorted_array')).toBeInTheDocument();
    expect(screen.getByText('tc2_empty_and_single')).toBeInTheDocument();

    // Switch to Gemini AI tab
    const aiTabBtn = screen.getByText(/Gemini AI Pedagogical Review/);
    fireEvent.click(aiTabBtn);

    expect(screen.getByText(/Excellent binary search implementation/)).toBeInTheDocument();
    expect(screen.getByText('Optimal mid calculation avoiding integer overflow')).toBeInTheDocument();
    expect(screen.getByText('Overflow-safe midpoint computation')).toBeInTheDocument();
  });

  it('renders SubmitAssignmentModal with GitHub and File Upload tabs', () => {
    const mockAssignment = {
      task_id: 'algo_hw1',
      title: 'Sorting Algorithms',
      max_score: 100,
      test_cases: [],
    };

    render(
      <ToastProvider>
        <AuthProvider>
          <SubmitAssignmentModal
            isOpen={true}
            onClose={() => {}}
            assignment={mockAssignment}
          />
        </AuthProvider>
      </ToastProvider>
    );

    expect(screen.getByText('Submit Solution: Sorting Algorithms')).toBeInTheDocument();
    expect(screen.getByText('GitHub Repository URL')).toBeInTheDocument();
    expect(screen.getByText('Direct File Upload (.py / .zip)')).toBeInTheDocument();

    // Switch to File Upload tab
    const uploadTab = screen.getByText('Direct File Upload (.py / .zip)');
    fireEvent.click(uploadTab);

    expect(
      screen.getByText(/Click or drag & drop source code file here/)
    ).toBeInTheDocument();
  });
});

