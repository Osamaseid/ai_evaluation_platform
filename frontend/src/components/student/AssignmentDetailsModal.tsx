import React, { useEffect, useState } from 'react';
import { Assignment, GradingRubric } from '../../types/api';
import { api } from '../../services/api';
import { Modal } from '../common/Modal';
import { Badge } from '../common/Badge';
import { BookOpen, CheckSquare, Sliders, Calendar, UploadCloud } from 'lucide-react';

interface AssignmentDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  assignment: Assignment | null;
  onOpenSubmit: (assignment: Assignment) => void;
}

export const AssignmentDetailsModal: React.FC<AssignmentDetailsModalProps> = ({
  isOpen,
  onClose,
  assignment,
  onOpenSubmit,
}) => {
  const [rubric, setRubric] = useState<GradingRubric | null>(null);

  useEffect(() => {
    if (isOpen && assignment) {
      api
        .getRubric(assignment.task_id)
        .then((r) => setRubric(r))
        .catch(() => setRubric(null));
    }
  }, [isOpen, assignment]);

  if (!assignment) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={assignment.title}
      size="large"
      footer={
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Max Score: <strong style={{ color: 'var(--text-main)' }}>{assignment.max_score} pts</strong>
          </span>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button onClick={onClose} className="btn btn-secondary">
              Close
            </button>
            <button
              onClick={() => {
                onClose();
                onOpenSubmit(assignment);
              }}
              className="btn btn-primary"
            >
              <UploadCloud size={16} /> Submit Solution
            </button>
          </div>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Metadata bar */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '1rem',
            padding: '1rem',
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
          }}
        >
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Task Identifier
            </span>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--text-main)', fontWeight: 600 }}>
              {assignment.task_id}
            </p>
          </div>
          {assignment.deadline && (
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                Deadline
              </span>
              <p style={{ fontSize: '0.9rem', color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Calendar size={14} /> {new Date(assignment.deadline).toLocaleString()}
              </p>
            </div>
          )}
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Test Suites
            </span>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', fontWeight: 600 }}>
              {assignment.test_cases ? assignment.test_cases.length : 0} automated tests
            </p>
          </div>
        </div>

        {/* Description & Problem Statement */}
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <BookOpen size={16} color="var(--primary)" /> Assignment Instructions
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
            {assignment.description ||
              'Implement the required functionality in Python adhering to algorithm constraints and edge-case requirements.'}
          </p>
        </div>

        {/* Test Cases Specification */}
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.65rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <CheckSquare size={16} color="var(--success)" /> Automated Evaluation Test Cases
          </h3>
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Test ID</th>
                  <th>Description</th>
                  <th>Weight (Points)</th>
                </tr>
              </thead>
              <tbody>
                {assignment.test_cases && assignment.test_cases.length > 0 ? (
                  assignment.test_cases.map((tc) => (
                    <tr key={tc.test_case_id}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                        {tc.test_case_id}
                      </td>
                      <td>{tc.description || 'Deterministic verification test'}</td>
                      <td>
                        <Badge variant="neutral">{tc.points} pts</Badge>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
                      No test cases specified yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Grading Rubric (If present) */}
        {rubric && rubric.criteria && rubric.criteria.length > 0 && (
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.65rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Sliders size={16} color="var(--ai-purple)" /> Instructor Grading Rubric
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
              {rubric.criteria.map((c) => (
                <div
                  key={c.criterion_id}
                  style={{
                    backgroundColor: 'var(--bg-card-subtle)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.85rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <strong style={{ fontSize: '0.85rem', color: 'var(--text-main)' }}>{c.name}</strong>
                    <Badge variant="purple">{c.max_points} pts</Badge>
                  </div>
                  <p style={{ fontSize: '0.775rem', color: 'var(--text-muted)' }}>{c.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

