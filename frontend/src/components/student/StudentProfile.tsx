import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { EvaluationReport } from '../../types/api';
import { MetricCard } from '../common/MetricCard';
import { Badge } from '../common/Badge';
import { ProgressBar } from '../common/ProgressBar';
import { LoadingSpinner, ErrorAlert } from '../common/FeedbackStates';
import { Modal } from '../common/Modal';
import { EvaluationDetailView } from './EvaluationDetailView';
import {
  User,
  Mail,
  GraduationCap,
  Award,
  CheckCircle2,
  BookOpen,
  Calendar,
  Sparkles,
  TrendingUp,
  FileCode,
  ArrowRight,
} from 'lucide-react';

export const StudentProfile: React.FC = () => {
  const { user } = useAuth();
  const [evaluations, setEvaluations] = useState<EvaluationReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<EvaluationReport | null>(null);

  const studentId = user?.user_id;

  useEffect(() => {
    if (!studentId || user?.role !== 'student') {
      setIsLoading(false);
      return;
    }

    const fetchProfileData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await api.getStudentEvaluations(studentId, 20, 0);
        setEvaluations(res.items || []);
      } catch (err: any) {
        setError(err.message || 'Unable to load student evaluation records.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfileData();
  }, [studentId, user?.role]);

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
      {/* Student Profile Header Card */}
      <div
        className="card"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1.5rem',
          borderLeft: '4px solid var(--primary)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div
            style={{
              width: '68px',
              height: '68px',
              borderRadius: '50%',
              backgroundColor: 'var(--primary-light)',
              border: '2px solid var(--primary-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary)',
              fontSize: '1.75rem',
              fontWeight: 800,
            }}
          >
            {user?.name ? user.name.charAt(0).toUpperCase() : 'S'}
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-main)' }}>
                {user?.name || 'Student Ada'}
              </h1>
              <Badge variant="success" icon={<GraduationCap size={12} />}>
                Enrolled Student
              </Badge>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.25rem', marginTop: '0.35rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <User size={14} /> Student ID: <strong style={{ color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>{studentId}</strong>
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Mail size={14} /> {user?.email || `${studentId}@akiba.edu`}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Calendar size={14} /> Academic Year 2026/2027
              </span>
            </div>
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--bg-secondary)',
            padding: '1rem 1.5rem',
            borderRadius: 'var(--radius-md)',
            textAlign: 'center',
            border: '1px solid var(--border-color)',
            minWidth: '160px',
          }}
        >
          <span style={{ fontSize: '0.725rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            Academic Performance
          </span>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: avgScore >= 70 ? 'var(--primary)' : 'var(--warning)', marginTop: '0.15rem' }}>
            {avgScore}%
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Course Grade Average
          </span>
        </div>
      </div>

      {error && <ErrorAlert message={error} />}

      {isLoading ? (
        <LoadingSpinner message="Loading student profile details and evaluation records..." />
      ) : (
        <>
          {/* Metrics Overview */}
          <div className="metrics-grid">
            <MetricCard
              label="Completed Evaluations"
              value={completedEvals.length}
              icon={<CheckCircle2 size={24} />}
              subtitle="Assignments assessed & scored"
            />
            <MetricCard
              label="Cumulative Average"
              value={`${avgScore}%`}
              icon={<TrendingUp size={24} />}
              subtitle="Deterministic & manual average"
            />
            <MetricCard
              label="Submissions Audited"
              value={evaluations.length}
              icon={<FileCode size={24} />}
              subtitle="Full test logs & AI reviews preserved"
            />
            <MetricCard
              label="Skill Mastery"
              value="Level 4"
              icon={<Sparkles size={24} />}
              subtitle="Data Structures & Algorithms"
            />
          </div>

          {/* Academic Profile Details & Learning Plan */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
            {/* Left Card: Core Competencies */}
            <div className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Engineering Competencies</h3>
                  <p className="card-subtitle">Automated assessment breakdown across key competencies</p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                    <span>Algorithmic Correctness & Edge Cases</span>
                    <span style={{ color: 'var(--primary)' }}>92%</span>
                  </div>
                  <ProgressBar percentage={92} showLabel={false} />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                    <span>Runtime Complexity & Memory Efficiency</span>
                    <span style={{ color: 'var(--primary)' }}>88%</span>
                  </div>
                  <ProgressBar percentage={88} showLabel={false} />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                    <span>PEP 8 Clean Code & Naming Conventions</span>
                    <span style={{ color: 'var(--primary)' }}>95%</span>
                  </div>
                  <ProgressBar percentage={95} showLabel={false} />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                    <span>Defensive Programming & Input Validation</span>
                    <span style={{ color: 'var(--primary)' }}>84%</span>
                  </div>
                  <ProgressBar percentage={84} showLabel={false} />
                </div>
              </div>
            </div>

            {/* Right Card: Akiba AI Learning Plan */}
            <div className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Akiba AI Pedagogical Roadmap</h3>
                  <p className="card-subtitle">Personalized learning advice generated from recent evaluations</p>
                </div>
                <Badge variant="purple" icon={<Sparkles size={12} />}>
                  AI Tailored
                </Badge>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <div
                  style={{
                    padding: '0.85rem 1rem',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--primary-light)',
                    border: '1px solid var(--primary-border)',
                  }}
                >
                  <strong style={{ fontSize: '0.875rem', color: 'var(--primary-dark)', display: 'block', marginBottom: '0.2rem' }}>
                    Mastery Highlight: Binary Search & Two-Pointer Patterns
                  </strong>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-body)' }}>
                    Your solutions show strong grasp of divide-and-conquer logic with zero integer overflow vulnerabilities.
                  </p>
                </div>

                <div
                  style={{
                    padding: '0.85rem 1rem',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--lime-light)',
                    border: '1px solid var(--lime-border)',
                  }}
                >
                  <strong style={{ fontSize: '0.875rem', color: 'var(--accent-lime)', display: 'block', marginBottom: '0.2rem' }}>
                    Next Milestone: Dynamic Programming & Memoization
                  </strong>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-body)' }}>
                    Practice bottom-up tabulations on upcoming assignments to master space-optimized Fibonacci and Knapsack problems.
                  </p>
                </div>

                <div
                  style={{
                    padding: '0.85rem 1rem',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: '#fafbfc',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <strong style={{ fontSize: '0.875rem', color: 'var(--text-main)', display: 'block', marginBottom: '0.2rem' }}>
                    Docstrings & Type Hints Recommendation
                  </strong>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Continue annotating parameter types and return contracts to maximize PEP 484 rubric scores.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Evaluations History Table */}
          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">Recent Assignment Evaluations</h3>
                <p className="card-subtitle">Inspect your deterministic test runs and Gemini AI code feedback</p>
              </div>
            </div>

            {evaluations.length === 0 ? (
              <div className="empty-state">
                <BookOpen className="empty-state-icon" />
                <h4 className="empty-state-title">No evaluations recorded yet</h4>
                <p className="empty-state-desc">
                  Submit your programming assignment code to receive verified deterministic scores and AI feedback.
                </p>
              </div>
            ) : (
              <div className="table-container">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Task / Assignment</th>
                      <th>Evaluation ID</th>
                      <th>Automated Score</th>
                      <th>Final Adjusted</th>
                      <th>Status</th>
                      <th>Completed</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evaluations.map((ev) => {
                      const finalScore = ev.manual_override_score ?? ev.deterministic_score;
                      const pct = ev.max_score > 0 ? (finalScore / ev.max_score) * 100 : 0;
                      return (
                        <tr key={ev.evaluation_id}>
                          <td>
                            <strong style={{ color: 'var(--text-main)' }}>{ev.task_id}</strong>
                          </td>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {ev.evaluation_id}
                          </td>
                          <td>
                            <span style={{ fontWeight: 600 }}>{ev.deterministic_score}</span> / {ev.max_score} pts
                          </td>
                          <td>
                            {ev.manual_override_score !== null ? (
                              <span style={{ fontWeight: 700, color: 'var(--primary)' }}>
                                {ev.manual_override_score} / {ev.max_score} pts
                              </span>
                            ) : (
                              <span style={{ color: 'var(--text-dim)' }}>—</span>
                            )}
                          </td>
                          <td>
                            <Badge variant={ev.status === 'completed' ? 'success' : ev.status === 'failed' ? 'danger' : 'warning'}>
                              {ev.status}
                            </Badge>
                          </td>
                          <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {ev.completed_at ? new Date(ev.completed_at).toLocaleDateString() : 'In Progress'}
                          </td>
                          <td>
                            <button
                              onClick={() => setSelectedReport(ev)}
                              className="btn btn-primary btn-sm"
                              style={{ gap: '0.3rem' }}
                            >
                              View Report <ArrowRight size={13} />
                            </button>
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

      {/* Evaluation Report Modal */}
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

