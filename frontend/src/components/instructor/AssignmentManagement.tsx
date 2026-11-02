import React, { useState, useEffect, useCallback } from 'react';
import { Assignment } from '../../types/api';
import { api } from '../../services/api';
import { Badge } from '../common/Badge';
import { LoadingSpinner, ErrorAlert, EmptyState } from '../common/FeedbackStates';
import { AssignmentCreateEditModal } from './AssignmentCreateEditModal';
import { RubricConfigurationModal } from './RubricConfigurationModal';
import {
  BookOpen,
  Plus,
  Edit3,
  Sliders,
  Calendar,
  Layers,
  RotateCw,
} from 'lucide-react';

export const AssignmentManagement: React.FC = () => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [isCreateEditOpen, setIsCreateEditOpen] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState<Assignment | null>(null);
  const [isRubricOpen, setIsRubricOpen] = useState(false);
  const [rubricAssignment, setRubricAssignment] = useState<Assignment | null>(null);

  const fetchAssignments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listInstructorAssignments();
      setAssignments(data);
    } catch (err: any) {
      setError(err.message || 'Could not load assignments.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAssignments();
  }, [fetchAssignments]);

  const handleCreateNew = () => {
    setEditingAssignment(null);
    setIsCreateEditOpen(true);
  };

  const handleEdit = (asgn: Assignment) => {
    setEditingAssignment(asgn);
    setIsCreateEditOpen(true);
  };

  const handleConfigureRubric = (asgn: Assignment) => {
    setRubricAssignment(asgn);
    setIsRubricOpen(true);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)' }}>
            Assignment & Test Case Management
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Design course programming challenges, configure test suites, and set up grading rubrics.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={fetchAssignments} className="btn btn-outline btn-sm" style={{ gap: '0.35rem' }}>
            <RotateCw size={14} /> Refresh
          </button>
          <button onClick={handleCreateNew} className="btn btn-primary" style={{ gap: '0.4rem' }}>
            <Plus size={16} /> Create Assignment
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={fetchAssignments} />}

      {isLoading ? (
        <LoadingSpinner message="Loading course assignments..." />
      ) : assignments.length === 0 ? (
        <EmptyState
          title="No assignments created yet"
          description="Click 'Create Assignment' to publish your first programming task with isolated test cases."
          icon={<BookOpen size={48} />}
          action={{
            label: 'Create First Assignment',
            onClick: handleCreateNew,
          }}
        />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1.25rem' }}>
          {assignments.map((asgn) => (
            <div
              key={asgn.task_id}
              className="card"
              style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '1rem' }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.75rem',
                      color: 'var(--primary)',
                      backgroundColor: 'rgba(59, 130, 246, 0.1)',
                      padding: '0.2rem 0.5rem',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    {asgn.task_id}
                  </span>
                  <Badge variant="purple">{asgn.max_score} pts</Badge>
                </div>

                <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.35rem' }}>
                  {asgn.title}
                </h3>

                <p
                  style={{
                    fontSize: '0.85rem',
                    color: 'var(--text-muted)',
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    lineHeight: 1.5,
                  }}
                >
                  {asgn.description || 'No description provided.'}
                </p>
              </div>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.8rem',
                    color: 'var(--text-dim)',
                    marginBottom: '0.85rem',
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Layers size={14} /> {asgn.test_cases ? asgn.test_cases.length : 0} Test Cases
                  </span>
                  {asgn.deadline && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--warning)' }}>
                      <Calendar size={14} /> {new Date(asgn.deadline).toLocaleDateString()}
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '0.65rem' }}>
                  <button
                    onClick={() => handleEdit(asgn)}
                    className="btn btn-outline btn-sm"
                    style={{ flex: 1, gap: '0.3rem' }}
                  >
                    <Edit3 size={14} /> Edit Tests
                  </button>
                  <button
                    onClick={() => handleConfigureRubric(asgn)}
                    className="btn btn-secondary btn-sm"
                    style={{ flex: 1, gap: '0.3rem' }}
                  >
                    <Sliders size={14} /> Rubric
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      <AssignmentCreateEditModal
        isOpen={isCreateEditOpen}
        onClose={() => setIsCreateEditOpen(false)}
        assignment={editingAssignment}
        onSaved={fetchAssignments}
      />

      {/* Rubric Configuration Modal */}
      <RubricConfigurationModal
        isOpen={isRubricOpen}
        onClose={() => setIsRubricOpen(false)}
        assignment={rubricAssignment}
        onSaved={fetchAssignments}
      />
    </div>
  );
};

