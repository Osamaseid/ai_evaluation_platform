import React, { useState, useEffect } from 'react';
import { Assignment, EvaluationReport, Student } from '../../types/api';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { MetricCard } from '../common/MetricCard';
import { Badge } from '../common/Badge';
import { Modal } from '../common/Modal';
import { LoadingSpinner, ErrorAlert } from '../common/FeedbackStates';
import { ManualReviewModal } from './ManualReviewModal';
import { EvaluationDetailView } from '../student/EvaluationDetailView';
import {
  Users,
  BookOpen,
  FileCheck2,
  TrendingUp,
  Award,
  Eye,
  Plus,
  UserPlus,
  ArrowRight,
} from 'lucide-react';

interface InstructorOverviewProps {
  onNavigateTab: (tab: string) => void;
}

export const InstructorOverview: React.FC<InstructorOverviewProps> = ({ onNavigateTab }) => {
  const { user } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Review modal
  const [selectedEvaluation, setSelectedEvaluation] = useState<EvaluationReport | null>(null);
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState<EvaluationReport | null>(null);

  const fetchOverviewData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [stuRes, asgRes, evalRes] = await Promise.allSettled([
        api.listStudents(100, 0),
        api.listInstructorAssignments(),
        api.listInstructorEvaluations(),
      ]);

      if (stuRes.status === 'fulfilled') setStudents(stuRes.value.items || []);
      if (asgRes.status === 'fulfilled') setAssignments(asgRes.value || []);
      if (evalRes.status === 'fulfilled') setEvaluations(evalRes.value || []);
    } catch (err: any) {
      setError(err.message || 'Could not load instructor overview.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOverviewData();
  }, []);

  const completedEvals = evaluations.filter((e) => e.status === 'completed');
  const avgScore =
    completedEvals.length > 0
      ? Math.round(
          completedEvals.reduce((acc, curr) => {
            const final = curr.manual_override_score ?? curr.deterministic_score;
            const pct = curr.max_score > 0 ? (final / curr.max_score) * 100 : 0;
            return acc + pct;
          }, 0) / completedEvals.length
        )
      : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Instructor Welcome Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15))',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-lg)',
          padding: '1.75rem 2rem',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1.25rem',
        }}
      >
        <div>
          <span
            style={{
              fontSize: '0.8rem',
              fontWeight: 600,
              color: '#c084fc',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Instructor Administration Portal
          </span>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '0.2rem' }}>
            Course Overview: {user?.name || 'Instructor'}
          </h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', maxWidth: '580px', marginTop: '0.35rem' }}>
            Automate programming assignment verification, inspect deterministic sandbox results, review Google Gemini AI feedback, and override student grades.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button onClick={() => onNavigateTab('assignments')} className="btn btn-primary" style={{ gap: '0.4rem' }}>
            <Plus size={16} /> New Assignment
          </button>
          <button onClick={() => onNavigateTab('students')} className="btn btn-outline" style={{ gap: '0.4rem' }}>
            <UserPlus size={16} /> Enroll Student
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} />}

      {isLoading ? (
        <LoadingSpinner message="Loading course analytics and evaluation records..." />
      ) : (
        <>
          {/* KPI Metrics Grid */}
          <div className="metrics-grid">
            <MetricCard
              label="Enrolled Students"
              value={students.length}
              icon={<Users size={24} />}
              subtitle="Registered course learners"
            />
            <MetricCard
              label="Assignments"
              value={assignments.length}
              icon={<BookOpen size={24} />}
              subtitle="Active programming tasks"
            />
            <MetricCard
              label="Evaluations Complete"
              value={completedEvals.length}
              icon={<FileCheck2 size={24} />}
              subtitle="Deterministic test passes"
            />
            <MetricCard
              label="Class Average"
              value={`${avgScore}%`}
              icon={<TrendingUp size={24} />}
              subtitle="Mean student score"
              trend={{ value: avgScore >= 70 ? 'Satisfactory' : 'Needs attention', isPositive: avgScore >= 70 }}
            />
          </div>

          {/* Recent Evaluations Queue */}
          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">Recent Submissions Queue</h3>
                <p className="card-subtitle">Latest evaluated submissions requiring review</p>
              </div>
              <button
                onClick={() => onNavigateTab('monitoring')}
                className="btn btn-outline btn-sm"
                style={{ border: 'none', color: 'var(--primary)' }}
              >
                View All Submissions <ArrowRight size={14} style={{ marginLeft: '4px' }} />
              </button>
            </div>

            {evaluations.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', padding: '1rem 0' }}>
                No submissions have been evaluated yet.
              </p>
            ) : (
              <div className="table-container">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Submission / Eval ID</th>
                      <th>Student</th>
                      <th>Task</th>
                      <th>Score</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evaluations.slice(0, 5).map((ev) => {
                      const isOverridden = ev.manual_override_score !== null && ev.manual_override_score !== undefined;
                      const finalScore = isOverridden ? ev.manual_override_score : ev.deterministic_score;

                      return (
                        <tr key={ev.evaluation_id}>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                            {ev.evaluation_id}
                          </td>
                          <td>
                            <strong>{ev.student_id}</strong>
                          </td>
                          <td>{ev.task_id}</td>
                          <td>
                            <strong style={{ color: 'var(--text-main)' }}>
                              {finalScore} / {ev.max_score}
                            </strong>
                            {isOverridden && (
                              <Badge variant="purple" style={{ marginLeft: '6px' }}>
                                Adjusted
                              </Badge>
                            )}
                          </td>
                          <td>
                            <Badge variant={ev.status === 'completed' ? 'success' : 'warning'}>
                              {ev.status}
                            </Badge>
                          </td>
                          <td>
                            <div style={{ display: 'flex', gap: '0.4rem' }}>
                              <button
                                onClick={() => setSelectedReport(ev)}
                                className="btn btn-outline btn-sm"
                                style={{ gap: '0.25rem' }}
                              >
                                <Eye size={12} /> View
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedEvaluation(ev);
                                  setIsReviewOpen(true);
                                }}
                                className="btn btn-secondary btn-sm"
                                style={{ gap: '0.25rem' }}
                              >
                                <Award size={12} /> Review
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {/* Manual Review Modal */}
      <ManualReviewModal
        isOpen={isReviewOpen}
        onClose={() => setIsReviewOpen(false)}
        evaluation={selectedEvaluation}
        onReviewSaved={fetchOverviewData}
      />

      {/* Report Modal */}
      <Modal
        isOpen={!!selectedReport}
        onClose={() => setSelectedReport(null)}
        title="Student Evaluation Audit"
        size="large"
      >
        {selectedReport && <EvaluationDetailView report={selectedReport} />}
      </Modal>
    </div>
  );
};

