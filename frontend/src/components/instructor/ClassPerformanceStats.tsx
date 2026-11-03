import React, { useState, useEffect } from 'react';
import { EvaluationReport } from '../../types/api';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { MetricCard } from '../common/MetricCard';
import { ProgressBar } from '../common/ProgressBar';
import { LoadingSpinner, ErrorAlert, EmptyState } from '../common/FeedbackStates';
import { BarChart3, TrendingUp, Award, CheckCircle2, XCircle } from 'lucide-react';

export const ClassPerformanceStats: React.FC = () => {
  const { user } = useAuth();
  const [evaluations, setEvaluations] = useState<EvaluationReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || (user.role !== 'instructor' && user.role !== 'admin')) {
      setIsLoading(false);
      return;
    }
    const fetchStats = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const evals = await api.listInstructorEvaluations();
        setEvaluations(evals || []);
      } catch (err: any) {
        setError(err.message || 'Could not load class performance metrics.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, [user]);

  // Compute metrics
  const completed = evaluations.filter((e) => e.status === 'completed');
  const scores = completed.map((e) => {
    const final = e.manual_override_score ?? e.deterministic_score;
    return e.max_score > 0 ? (final / e.max_score) * 100 : 0;
  });

  const avg = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
  const highest = scores.length > 0 ? Math.round(Math.max(...scores)) : 0;
  const lowest = scores.length > 0 ? Math.round(Math.min(...scores)) : 0;
  const passedCount = scores.filter((s) => s >= 60).length;
  const passRate = scores.length > 0 ? Math.round((passedCount / scores.length) * 100) : 0;

  // Grade distributions
  const gradeBuckets = {
    A: scores.filter((s) => s >= 90).length,
    B: scores.filter((s) => s >= 80 && s < 90).length,
    C: scores.filter((s) => s >= 70 && s < 80).length,
    D: scores.filter((s) => s >= 60 && s < 70).length,
    F: scores.filter((s) => s < 60).length,
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)' }}>
          Class Performance Analytics & Statistics
        </h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Aggregate grading metrics, score distribution curves, and evaluation analytics.
        </p>
      </div>

      {error && <ErrorAlert message={error} />}

      {isLoading ? (
        <LoadingSpinner message="Aggregating class performance data..." />
      ) : completed.length === 0 ? (
        <EmptyState
          title="No evaluation data yet"
          description="Evaluation statistics will populate automatically once student submissions are evaluated."
          icon={<BarChart3 size={48} />}
        />
      ) : (
        <>
          <div className="metrics-grid">
            <MetricCard
              label="Class Average"
              value={`${avg}%`}
              icon={<TrendingUp size={24} />}
              subtitle="Mean student score"
            />
            <MetricCard
              label="Passing Rate"
              value={`${passRate}%`}
              icon={<CheckCircle2 size={24} />}
              subtitle={`${passedCount} of ${scores.length} submissions passed`}
            />
            <MetricCard
              label="Highest Score"
              value={`${highest}%`}
              icon={<Award size={24} />}
              subtitle="Top submission score"
            />
            <MetricCard
              label="Lowest Score"
              value={`${lowest}%`}
              icon={<XCircle size={24} />}
              subtitle="Lowest submission score"
            />
          </div>

          {/* Grade Distribution Breakdown */}
          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">Grade Distribution (Letter Grades)</h3>
                <p className="card-subtitle">Distribution of scores across standard academic brackets</p>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem' }}>
              {(
                [
                  { grade: 'A (90% - 100%)', count: gradeBuckets.A, color: 'var(--success)' },
                  { grade: 'B (80% - 89%)', count: gradeBuckets.B, color: 'var(--info)' },
                  { grade: 'C (70% - 79%)', count: gradeBuckets.C, color: 'var(--warning)' },
                  { grade: 'D (60% - 69%)', count: gradeBuckets.D, color: '#fb923c' },
                  { grade: 'F (< 60%)', count: gradeBuckets.F, color: 'var(--danger)' },
                ] as const
              ).map((bucket) => {
                const pct = scores.length > 0 ? (bucket.count / scores.length) * 100 : 0;
                return (
                  <div key={bucket.grade}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
                      <strong style={{ color: 'var(--text-main)' }}>{bucket.grade}</strong>
                      <span style={{ color: 'var(--text-muted)' }}>
                        {bucket.count} students ({Math.round(pct)}%)
                      </span>
                    </div>
                    <div className="progress-bar-container">
                      <div
                        className="progress-bar-fill"
                        style={{ width: `${pct}%`, backgroundColor: bucket.color }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

