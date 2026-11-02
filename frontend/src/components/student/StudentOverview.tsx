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

  const studentId = user?.user_id || 'student_ada';

  useEffect(() => {
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
  }, [studentId]);

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
      {/* Welcome Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.15), rgba(139, 92, 246, 0.15))',
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
              color: 'var(--primary)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Student Learning Dashboard
          </span>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '0.2rem' }}>
            Welcome back, {user?.name || 'Student'}!
          </h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', maxWidth: '580px', marginTop: '0.35rem' }}>
            Submit programming assignments via GitHub URLs or direct code uploads. Get immediate deterministic grading and detailed Gemini AI code explanations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={() => onNavigateTab('assignments')} className="btn btn-primary" style={{ gap: '0.4rem' }}>
            <BookOpen size={16} /> View Assignments
          </button>
          <button onClick={() => onNavigateTab('history')} className="btn btn-outline" style={{ gap: '0.4rem' }}>
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
              subtitle="Total submissions recorded"
            />
            <MetricCard
              label="Evaluations Complete"
              value={completedEvals.length}
              icon={<CheckCircle2 size={24} />}
              subtitle="Graded by automated suite"
            />
            <MetricCard
              label="Average Grade"
              value={`${avgScore}%`}
              icon={<Award size={24} />}
              subtitle="Overall class performance"
              trend={{ value: avgScore >= 70 ? 'Proficient' : 'Needs practice', isPositive: avgScore >= 70 }}
            />
          </div>

          {/* Quick Split Section */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
            {/* Recent Submissions */}
            <div className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Recent Submissions</h3>
                  <p className="card-subtitle">Your latest code submissions</p>
                </div>
                <button
                  onClick={() => onNavigateTab('history')}
                  className="btn btn-outline btn-sm"
                  style={{ border: 'none', color: 'var(--primary)' }}
                >
                  View All
                </button>
              </div>

              {submissions.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', padding: '1rem 0' }}>
                  No submissions recorded yet. Pick an assignment to begin!
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {submissions.slice(0, 4).map((sub) => (
                    <div
                      key={sub.submission_id}
                      style={{
                        padding: '0.75rem 1rem',
                        backgroundColor: 'var(--bg-secondary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-md)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div>
                        <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)', display: 'block' }}>
                          {sub.task_id}
                        </strong>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                          {sub.submission_id} &bull; {new Date(sub.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <Badge variant={sub.status === 'evaluated' || sub.status === 'completed' ? 'success' : 'info'}>
                        {sub.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* AI Review Highlight */}
            <div className="card" style={{ background: 'linear-gradient(145deg, var(--bg-card), rgba(139, 92, 246, 0.05))' }}>
              <div className="card-header">
                <div>
                  <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Sparkles size={18} color="#c084fc" /> Gemini AI Feedback
                  </h3>
                  <p className="card-subtitle">Pedagogical insights & code analysis</p>
                </div>
              </div>

              {evaluations.length > 0 && evaluations[0].ai_review ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                    "{evaluations[0].ai_review.summary}"
                  </p>
                  <button
                    onClick={() => setSelectedReport(evaluations[0])}
                    className="btn btn-outline btn-sm"
                    style={{ alignSelf: 'flex-start' }}
                  >
                    Read Full AI Code Review
                  </button>
                </div>
              ) : (
                <div style={{ padding: '1.5rem 0', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <Sparkles size={32} color="var(--text-dim)" style={{ margin: '0 auto 0.5rem auto' }} />
                  <p style={{ fontSize: '0.85rem' }}>
                    Once you submit code and run evaluation, Google Gemini AI analyzes code quality, edge cases, and maintainability.
                  </p>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Evaluation Report Modal */}
      <Modal
        isOpen={!!selectedReport}
        onClose={() => setSelectedReport(null)}
        title="Evaluation Report & AI Analysis"
        size="large"
      >
        {selectedReport && <EvaluationDetailView report={selectedReport} />}
      </Modal>
    </div>
  );
};

