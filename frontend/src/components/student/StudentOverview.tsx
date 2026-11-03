import React, { useState, useEffect } from 'react';
import { Assignment, EvaluationReport, Submission } from '../../types/api';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { MetricCard } from '../common/MetricCard';
import { Badge } from '../common/Badge';
import { ProgressBar } from '../common/ProgressBar';
import { Modal } from '../common/Modal';
import { LoadingSpinner, ErrorAlert } from '../common/FeedbackStates';
import { EvaluationDetailView } from './EvaluationDetailView';
import {
  BookOpen,
  UploadCloud,
  CheckCircle2,
  Clock,
  Sparkles,
  Award,
  ArrowRight,
  TrendingUp,
  FileCode,
} from 'lucide-react';

interface StudentOverviewProps {
  onNavigateTab: (tab: string) => void;
}

export const StudentOverview: React.FC<StudentOverviewProps> = ({ onNavigateTab }) => {
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal report view
  const [selectedReport, setSelectedReport] = useState<EvaluationReport | null>(null);

  const studentId = user?.user_id;

  useEffect(() => {
    if (!studentId || user?.role !== 'student') {
      setIsLoading(false);
      return;
    }

    const loadOverviewData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [asgns, subs, evals] = await Promise.allSettled([
          api.listAssignments(),
          api.getStudentSubmissions(studentId, 10, 0),
          api.getStudentEvaluations(studentId, 10, 0),
        ]);

        if (asgns.status === 'fulfilled') setAssignments(asgns.value || []);
        if (subs.status === 'fulfilled') setSubmissions(subs.value.items || []);
        if (evals.status === 'fulfilled') setEvaluations(evals.value.items || []);
      } catch (err: any) {
        setError(err.message || 'Could not load student overview metrics.');
      } finally {
        setIsLoading(false);
      }
    };

    loadOverviewData();
  }, [studentId, user?.role]);

  // Derived metrics
  const totalSubmissions = submissions.length;
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
      {/* Welcome Hero Banner (Akiba Technologies Clean SaaS Brand Style) */}
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
              Akiba Technologies &bull; Student Engineering Academy
            </span>
          </div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            Welcome back, {user?.name || 'Student Ada'}!
          </h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', maxWidth: '620px', marginTop: '0.35rem' }}>
            Submit programming assignments via GitHub repository URLs or direct source-code archives. Receive immediate deterministic grading and actionable Gemini AI code reviews.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={() => onNavigateTab('assignments')} className="btn btn-primary" style={{ gap: '0.45rem' }}>
            <BookOpen size={16} /> Explore Assignments
          </button>
          <button onClick={() => onNavigateTab('history')} className="btn btn-secondary" style={{ gap: '0.45rem' }}>
            Submission History <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} />}

      {isLoading ? (
        <LoadingSpinner message="Calculating your assignment performance metrics..." />
      ) : (
        <>
          {/* Metrics Overview */}
          <div className="metrics-grid">
            <MetricCard
              label="Available Tasks"
              value={assignments.length}
              icon={<BookOpen size={24} />}
              subtitle="Active assignments in course"
            />
            <MetricCard
              label="Submissions"
              value={totalSubmissions}
              icon={<UploadCloud size={24} />}
              subtitle="Code submissions processed"
            />
            <MetricCard
              label="Completed Reviews"
              value={completedEvals.length}
              icon={<CheckCircle2 size={24} />}
              subtitle="Deterministic & AI feedback ready"
            />
            <MetricCard
              label="Average Score"
              value={`${avgScore}%`}
              icon={<TrendingUp size={24} />}
              subtitle="Cumulative evaluation score"
            />
          </div>

          {/* Quick Action Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            {/* Recent Submissions Card */}
            <div className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Recent Submissions</h3>
                  <p className="card-subtitle">Latest automated test runs & grades</p>
                </div>
                <button
                  onClick={() => onNavigateTab('history')}
                  className="btn btn-outline btn-sm"
                  style={{ gap: '0.3rem' }}
                >
                  View All <ArrowRight size={14} />
                </button>
              </div>

              {submissions.length === 0 ? (
                <div className="empty-state" style={{ padding: '2rem 1rem' }}>
                  <UploadCloud className="empty-state-icon" />
                  <h4 className="empty-state-title">No submissions yet</h4>
                  <p className="empty-state-desc">
                    Pick an assignment from the catalog to submit your repository or files.
                  </p>
                  <button onClick={() => onNavigateTab('assignments')} className="btn btn-primary btn-sm">
                    Browse Assignments
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {submissions.slice(0, 4).map((sub) => {
                    const matchedEval = evaluations.find((e) => e.submission_id === sub.submission_id);
                    const finalScore = matchedEval
                      ? (matchedEval.manual_override_score ?? matchedEval.deterministic_score)
                      : null;
                    const maxScore = matchedEval ? matchedEval.max_score : 100;

                    return (
                      <div
                        key={sub.submission_id}
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
                            {sub.task_id}
                          </strong>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {sub.source_type === 'github' ? 'GitHub URL' : 'File Upload'} &bull;{' '}
                            {new Date(sub.created_at).toLocaleDateString()}
                          </span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          {finalScore !== null ? (
                            <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--primary)' }}>
                              {finalScore} / {maxScore} pts
                            </span>
                          ) : (
                            <Badge variant={sub.status === 'completed' ? 'success' : 'warning'}>
                              {sub.status}
                            </Badge>
                          )}

                          {matchedEval && (
                            <button
                              onClick={() => setSelectedReport(matchedEval)}
                              className="btn btn-outline btn-sm"
                              style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}
                            >
                              Report
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Active Assignments Card */}
            <div className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Available Assignments</h3>
                  <p className="card-subtitle">Ready for submission & testing</p>
                </div>
                <button
                  onClick={() => onNavigateTab('assignments')}
                  className="btn btn-outline btn-sm"
                  style={{ gap: '0.3rem' }}
                >
                  Catalog <ArrowRight size={14} />
                </button>
              </div>

              {assignments.length === 0 ? (
                <div className="empty-state" style={{ padding: '2rem 1rem' }}>
                  <BookOpen className="empty-state-icon" />
                  <h4 className="empty-state-title">No assignments published</h4>
                  <p className="empty-state-desc">Your instructor has not yet released any assignments.</p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {assignments.slice(0, 4).map((asgn) => (
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
                          Max Score: {asgn.max_score} pts &bull; {asgn.test_cases?.length || 0} Test Cases
                        </span>
                      </div>

                      <button
                        onClick={() => onNavigateTab('assignments')}
                        className="btn btn-primary btn-sm"
                        style={{ padding: '0.35rem 0.75rem' }}
                      >
                        Submit
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Modal Report View */}
      {selectedReport && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedReport(null)}
          title={`Evaluation Report: ${selectedReport.task_id}`}
          size="large"
        >
          <EvaluationDetailView report={selectedReport} />
        </Modal>
      )}
    </div>
  );
};
