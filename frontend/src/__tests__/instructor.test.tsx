import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ToastProvider } from '../context/ToastContext';
import { AuthProvider } from '../context/AuthContext';
import { ManualReviewModal } from '../components/instructor/ManualReviewModal';
import { AssignmentCreateEditModal } from '../components/instructor/AssignmentCreateEditModal';
import { RubricConfigurationModal } from '../components/instructor/RubricConfigurationModal';
import { EvaluationReport } from '../types/api';

describe('Instructor Dashboard Components', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('renders ManualReviewModal and permits grade override and notes input', () => {
    const mockEval: EvaluationReport = {
      evaluation_id: 'eval_rev_001',
      submission_id: 'sub_001',
      student_id: 'student_ada',
      task_id: 'tree_traversal',
      status: 'completed',
      deterministic_score: 75,
      max_score: 100,
      started_at: '2026-11-01T10:00:00Z',
    };

    render(
      <ToastProvider>
        <AuthProvider>
          <ManualReviewModal
            isOpen={true}
            onClose={() => {}}
            evaluation={mockEval}
            onReviewSaved={() => {}}
          />
        </AuthProvider>
      </ToastProvider>
    );

    expect(screen.getByText('Manual Review: student_ada (tree_traversal)')).toBeInTheDocument();
    expect(screen.getByText('75 / 100 pts')).toBeInTheDocument();

    const scoreInput = screen.getByRole('spinbutton');
    expect(scoreInput).toHaveValue(75);

    fireEvent.change(scoreInput, { target: { value: '88' } });
    expect(scoreInput).toHaveValue(88);

    const notesTextarea = screen.getByPlaceholderText(/Provide personalized commentary/);
    fireEvent.change(notesTextarea, {
      target: { value: 'Good recursion handling; awarded extra points for clean helper method.' },
    });
    expect(notesTextarea).toHaveValue(
      'Good recursion handling; awarded extra points for clean helper method.'
    );

    expect(screen.getByText('Save Manual Review')).toBeInTheDocument();
  });

  it('renders AssignmentCreateEditModal with dynamic test case addition', () => {
    render(
      <ToastProvider>
        <AuthProvider>
          <AssignmentCreateEditModal
            isOpen={true}
            onClose={() => {}}
            assignment={null}
            onSaved={() => {}}
          />
        </AuthProvider>
      </ToastProvider>
    );

    expect(screen.getByText('Create New Programming Assignment')).toBeInTheDocument();

    // Verify initial test cases
    expect(screen.getByDisplayValue('tc1_correctness')).toBeInTheDocument();
    expect(screen.getByDisplayValue('tc2_edge_case')).toBeInTheDocument();

    // Add another test case
    const addTestBtn = screen.getByText('Add Test Case');
    fireEvent.click(addTestBtn);

    expect(screen.getByDisplayValue('tc3')).toBeInTheDocument();
  });

  it('renders RubricConfigurationModal with criteria inputs', () => {
    const mockAssignment = {
      task_id: 'algo_hw1',
      title: 'Sorting Algorithms',
      max_score: 100,
      test_cases: [],
    };

    render(
      <ToastProvider>
        <AuthProvider>
          <RubricConfigurationModal
            isOpen={true}
            onClose={() => {}}
            assignment={mockAssignment}
            onSaved={() => {}}
          />
        </AuthProvider>
      </ToastProvider>
    );

    expect(screen.getByText('Configure Grading Rubric: Sorting Algorithms')).toBeInTheDocument();
    expect(screen.getByText('Add Criterion')).toBeInTheDocument();
    expect(screen.getByText('Save Rubric')).toBeInTheDocument();
  });
});

