import React, { useState, useEffect } from 'react';
import { Assignment } from '../../types/api';
import { api } from '../../services/api';
import { Badge } from '../common/Badge';
import { LoadingSpinner, ErrorAlert, EmptyState } from '../common/FeedbackStates';
import { AssignmentDetailsModal } from './AssignmentDetailsModal';
import { SubmitAssignmentModal } from './SubmitAssignmentModal';
import {
  BookOpen,
  Search,
  UploadCloud,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowRight,
} from 'lucide-react';

interface AssignmentListProps {
  onOpenSubmit?: (assignment: Assignment) => void;
}

export const AssignmentList: React.FC<AssignmentListProps> = () => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Modals
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [isSubmitOpen, setIsSubmitOpen] = useState(false);

  const fetchAssignments = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listAssignments();
      setAssignments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load assignments catalog from backend.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignments();
  }, []);

  const filtered = assignments.filter(
    (a) =>
      a.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.task_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top action & search bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)' }}>
            Available Programming Assignments
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Browse tasks, inspect test suite requirements, and submit your source code.
          </p>
        </div>

        <div style={{ position: 'relative', width: '280px' }}>
          <Search
            size={16}
            color="var(--text-dim)"
            style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }}
          />
          <input
            type="text"
            placeholder="Search by title or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="form-input"
            style={{ paddingLeft: '2.4rem' }}
          />
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={fetchAssignments} />}

      {isLoading ? (
        <LoadingSpinner message="Fetching active programming assignments from server..." />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No assignments found"
          description={
            searchTerm
              ? `No assignments matching "${searchTerm}". Try another search term.`
              : 'No programming assignments have been published yet. Check back soon or switch to Instructor View to create one.'
          }
          icon={<BookOpen size={48} />}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '1.25rem',
          }}
        >
          {filtered.map((assignment) => (
            <div
              key={assignment.task_id}
              className="card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '1.25rem',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.6rem' }}>
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
                    {assignment.task_id}
                  </span>
                  <Badge variant="purple">{assignment.max_score} pts</Badge>
                </div>

                <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.4rem' }}>
                  {assignment.title}
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
                  {assignment.description || 'Complete the implementation according to test specifications.'}
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
                    <Layers size={14} /> {assignment.test_cases ? assignment.test_cases.length : 0} Tests
                  </span>
                  {assignment.deadline ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--warning)' }}>
                      <Calendar size={14} /> {new Date(assignment.deadline).toLocaleDateString()}
                    </span>
                  ) : (
                    <span>No deadline</span>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '0.65rem' }}>
                  <button
                    onClick={() => {
                      setSelectedAssignment(assignment);
                      setIsDetailsOpen(true);
                    }}
                    className="btn btn-outline btn-sm"
                    style={{ flex: 1 }}
                  >
                    Details
                  </button>
                  <button
                    onClick={() => {
                      setSelectedAssignment(assignment);
                      setIsSubmitOpen(true);
                    }}
                    className="btn btn-primary btn-sm"
                    style={{ flex: 1, gap: '0.35rem' }}
                  >
                    <UploadCloud size={14} /> Submit
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Assignment Details Modal */}
      <AssignmentDetailsModal
        isOpen={isDetailsOpen}
        onClose={() => setIsDetailsOpen(false)}
        assignment={selectedAssignment}
        onOpenSubmit={(asgn) => {
          setSelectedAssignment(asgn);
          setIsSubmitOpen(true);
        }}
      />

      {/* Submit Assignment Modal */}
      <SubmitAssignmentModal
        isOpen={isSubmitOpen}
        onClose={() => setIsSubmitOpen(false)}
        assignment={selectedAssignment}
        onSubmissionSuccess={() => {
          fetchAssignments();
        }}
      />
    </div>
  );
};

