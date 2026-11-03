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
  ShieldCheck,
  CheckCircle2,
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
    if (!user || (user.role !== 'instructor' && user.role !== 'admin')) {
      setIsLoading(false);
      return;
    }
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
  }, [user?.role]);

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
      {/* Instructor Welcome Banner (Clean Akiba SaaS Styling) */}
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--border-color)',
          borderLeft: '4px solid var(--primary)',
          borderRadius: 'var(--radius-lg)',
          padding: '1.75rem 2rem',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1.5rem',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: 'var(--primary)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              Akiba Technologies &bull; Academic Management Suite
            </span>
          </div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            Course Leadership: {user?.name || 'Prof. Turing'}
          </h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', maxWidth: '620px', marginTop: '0.35rem' }}>
            Configure programming assignments and test cases, monitor live submissions, inspect Gemini AI pedagogical reviews, and perform deterministic grade overrides.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button onClick={() => onNavigateTab('assignments')} className="btn btn-primary" style={{ gap: '0.45rem' }}>
            <Plus size={16} /> New Assignment
          </button>
          <button onClick={() => onNavigateTab('students')} className="btn btn-secondary" style={{ gap: '0.45rem' }}>
            <UserPlus size={16} /> Student Directory
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
              label="Evaluations Run"
              value={evaluations.length}
              icon={<FileCheck2 size={24} />}
              subtitle="Automated & reviewed runs"
            />
            <MetricCard
              label="Course Average"
              value={`${avgScore}%`}
              icon={<TrendingUp size={24} />}
              subtitle="Average grade performance"
            />
          </div>

          {/* Quick Monitoring & Review Section */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
            {/* Recent Evaluations Queue */}
            <div className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Recent Student Evaluations</h3>
                  <p className="card-subtitle">Review deterministic results & AI comments</p>
                </div>
                <button
                  onClick={() => onNavigateTab('monitoring')}
                  className="btn btn-outline btn-sm"
                  style={{ gap: '0.3rem' }}
                >
                  All Submissions <ArrowRight size={14} />
                </button>
              </div>

              {evaluations.length === 0 ? (
                <div className="empty-state" style={{ padding: '2rem 1rem' }}>
                  <FileCheck2 className="empty-state-icon" />
                  <h4 className="empty-state-title">No evaluations processed yet</h4>
                  <p className="empty-state-desc">
                    When students submit code, evaluation reports with test logs and Gemini AI reviews appear here.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {evaluations.slice(0, 5).map((ev) => {
                    const finalScore = ev.manual_override_score ?? ev.deterministic_score;
                    return (
                      <div
                        key={ev.evaluation_id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '0.85rem 1rem',
                          backgroundColor: '#f8fafc',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--border-color)',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>
                              {ev.student_id}
                            </strong>
                            <Badge variant={ev.status === 'completed' ? 'success' : 'warning'}>
                              {ev.status}
                            </Badge>
                          </div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            Task: {ev.task_id} &bull; Score:{' '}
                            <strong style={{ color: 'var(--primary)' }}>
                              {finalScore}/{ev.max_score}
                            </strong>
                          </span>
                        </div>

                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button
                            onClick={() => setSelectedReport(ev)}
                            className="btn btn-outline btn-sm"
                            title="Inspect Detailed Report"
                            style={{ padding: '0.3rem 0.6rem' }}
                          >
                            <Eye size={14} />
                          </button>
                          <button
                            onClick={() => {
                              setSelectedEvaluation(ev);
                              setIsReviewOpen(true);
                            }}
                            className="btn btn-primary btn-sm"
                            title="Manual Review / Grade Override"
                            style={{ padding: '0.3rem 0.6rem', gap: '0.3rem' }}
                          >
                            <Award size={14} /> Review
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Course Assignments Roster */}
            <div className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Managed Assignments</h3>
                  <p className="card-subtitle">Test case counts & scoring rubrics</p>
                </div>
                <button
                  onClick={() => onNavigateTab('assignments')}
                  className="btn btn-outline btn-sm"
                  style={{ gap: '0.3rem' }}
                >
                  Manage <ArrowRight size={14} />
                </button>
              </div>

              {assignments.length === 0 ? (
                <div className="empty-state" style={{ padding: '2rem 1rem' }}>
                  <BookOpen className="empty-state-icon" />
                  <h4 className="empty-state-title">No assignments created</h4>
                  <p className="empty-state-desc">Create your first assignment with automated test cases.</p>
                  <button onClick={() => onNavigateTab('assignments')} className="btn btn-primary btn-sm">
                    Create Assignment
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {assignments.slice(0, 5).map((asgn) => (
                    <div
                      key={asgn.task_id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.85rem 1rem',
                        backgroundColor: '#f8fafc',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-color)',
                      }}
                    >
                      <div>
                        <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)', display: 'block' }}>
                          {asgn.title || asgn.task_id}
                        </strong>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          ID: <span style={{ fontFamily: 'var(--font-mono)' }}>{asgn.task_id}</span> &bull; {asgn.test_cases?.length || 0} Test Cases
                        </span>
                      </div>

                      <Badge variant="purple">{asgn.max_score} pts</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Manual Review Modal */}
      <ManualReviewModal
        isOpen={isReviewOpen}
        onClose={() => setIsReviewOpen(false)}
        evaluation={selectedEvaluation}
        onReviewSaved={() => {
          fetchOverviewData();
          setIsReviewOpen(false);
        }}
      />

      {/* Detailed Evaluation Report Modal */}
      {selectedReport && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedReport(null)}
          title={`Evaluation Report: ${selectedReport.task_id} (${selectedReport.student_id})`}
          size="large"
        >
          <EvaluationDetailView report={selectedReport} />
        </Modal>
      )}
    </div>
  );
};
