import React, { useState } from 'react';
import { EvaluationReport } from '../../types/api';
import { Badge } from '../common/Badge';
import { ProgressBar } from '../common/ProgressBar';
import {
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  AlertTriangle,
  Lightbulb,
  FileCode,
  Award,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface EvaluationDetailViewProps {
  report: EvaluationReport;
}

export const EvaluationDetailView: React.FC<EvaluationDetailViewProps> = ({ report }) => {
  const [activeTab, setActiveTab] = useState<'tests' | 'ai' | 'rubric'>('tests');
  const [expandedTest, setExpandedTest] = useState<string | null>(null);

  const grading = report.grading_report;
  const ai = report.ai_review;
  const isReviewed = report.reviewed_by || report.manual_override_score !== null;
  const finalScore = report.manual_override_score ?? report.deterministic_score;
  const percentage = report.max_score > 0 ? (finalScore / report.max_score) * 100 : 0;

  return (
    <div className="evaluation-detail-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Summary Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9))',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-lg)',
          padding: '1.5rem',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1.25rem',
        }}
      >
        <div style={{ flex: '1 1 300px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Evaluation ID: <span style={{ fontFamily: 'var(--font-mono)' }}>{report.evaluation_id}</span>
            </span>
            <Badge variant={report.status === 'completed' ? 'success' : report.status === 'failed' ? 'danger' : 'warning'}>
              {report.status}
            </Badge>
            {report.manual_override_score !== null && (
              <Badge variant="purple" icon={<Award size={12} />}>
                Instructor Overridden
              </Badge>
            )}
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)' }}>
            Assignment: {report.task_id}
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            Student: <strong style={{ color: 'var(--text-main)' }}>{report.student_id}</strong> &bull; Completed:{' '}
            {report.completed_at ? new Date(report.completed_at).toLocaleString() : 'N/A'}
          </p>
        </div>

        {/* Score Pill */}
        <div
          style={{
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.5rem',
            textAlign: 'center',
            minWidth: '180px',
          }}
        >
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Final Score
          </span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: percentage >= 70 ? 'var(--success)' : 'var(--warning)' }}>
            {finalScore} <span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>/ {report.max_score}</span>
          </div>
          <div style={{ marginTop: '0.35rem' }}>
            <ProgressBar percentage={percentage} showLabel={false} />
          </div>
        </div>
      </div>

      {/* Instructor Review & Score Override Alert (If present) */}
      {isReviewed && (
        <div
          style={{
            padding: '1.25rem',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'rgba(139, 92, 246, 0.1)',
            border: '1px solid rgba(139, 92, 246, 0.3)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
            <Award size={18} color="#c084fc" />
            <strong style={{ color: '#c084fc', fontSize: '0.95rem' }}>Instructor Manual Review Override</strong>
            {report.reviewed_by && (
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                by {report.reviewed_by} on {report.reviewed_at ? new Date(report.reviewed_at).toLocaleDateString() : ''}
              </span>
            )}
          </div>
          {report.manual_override_score !== null && (
            <p style={{ fontSize: '0.875rem', marginBottom: '0.4rem' }}>
              Original Automated Score: <strong>{report.deterministic_score}</strong> &rarr; Final Adjusted Score:{' '}
              <strong style={{ color: 'var(--success)' }}>{report.manual_override_score}</strong>
            </p>
          )}
          {report.instructor_notes && (
            <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginTop: '0.4rem', whiteSpace: 'pre-wrap' }}>
              <strong>Feedback Notes:</strong> {report.instructor_notes}
            </div>
          )}
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="tabs-nav">
        <button
          onClick={() => setActiveTab('tests')}
          className={`tab-btn ${activeTab === 'tests' ? 'active' : ''}`}
        >
          Automated Test Results ({grading ? `${grading.passed_tests}/${grading.total_tests}` : '0'})
        </button>
        <button
          onClick={() => setActiveTab('ai')}
          className={`tab-btn ${activeTab === 'ai' ? 'active' : ''}`}
          style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
        >
          <Sparkles size={16} color="#a855f7" />
          Gemini AI Pedagogical Review
        </button>
        <button
          onClick={() => setActiveTab('rubric')}
          className={`tab-btn ${activeTab === 'rubric' ? 'active' : ''}`}
        >
          Rubric Criteria
        </button>
      </div>

      {/* Tab 1: Test Results Breakdown */}
      {activeTab === 'tests' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {grading && grading.test_case_results && grading.test_case_results.length > 0 ? (
            grading.test_case_results.map((tc, idx) => {
              const isExpanded = expandedTest === tc.test_case_id;
              return (
                <div
                  key={tc.test_case_id || idx}
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    onClick={() => setExpandedTest(isExpanded ? null : tc.test_case_id)}
                    style={{
                      padding: '1rem 1.25rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      backgroundColor: isExpanded ? 'var(--bg-card-hover)' : 'transparent',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                      {tc.passed ? (
                        <CheckCircle2 size={20} color="var(--success)" />
                      ) : (
                        <XCircle size={20} color="var(--danger)" />
                      )}
                      <div>
                        <strong style={{ fontSize: '0.925rem', color: 'var(--text-main)' }}>
                          {tc.test_case_id}
                        </strong>
                        {tc.message && (
                          <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {tc.message}
                          </span>
                        )}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      {tc.execution_time_ms !== undefined && (
                        <span style={{ fontSize: '0.775rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <Clock size={12} /> {tc.execution_time_ms} ms
                        </span>
                      )}
                      <Badge variant={tc.passed ? 'success' : 'danger'}>
                        {tc.passed ? 'Passed' : 'Failed'}
                      </Badge>
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </div>

                  {/* Expanded Execution Details */}
                  {isExpanded && (
                    <div
                      style={{
                        padding: '1.25rem',
                        borderTop: '1px solid var(--border-color)',
                        backgroundColor: 'var(--bg-card-subtle)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.75rem',
                      }}
                    >
                      {tc.stdout && (
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Standard Output (stdout):</span>
                          <pre className="code-block" style={{ marginTop: '0.35rem' }}>{tc.stdout}</pre>
                        </div>
                      )}
                      {tc.stderr && (
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--danger)', fontWeight: 600 }}>Standard Error (stderr):</span>
                          <pre className="code-block" style={{ marginTop: '0.35rem', borderColor: 'var(--danger-border)' }}>{tc.stderr}</pre>
                        </div>
                      )}
                      {!tc.stdout && !tc.stderr && (
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                          No output captured during execution.
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
              No detailed test case results recorded for this submission.
            </p>
          )}
        </div>
      )}

      {/* Tab 2: Gemini AI Pedagogical Review */}
      {activeTab === 'ai' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {ai ? (
            <>
              {/* Executive Summary */}
              {ai.summary && (
                <div
                  style={{
                    backgroundColor: 'rgba(139, 92, 246, 0.08)',
                    border: '1px solid rgba(139, 92, 246, 0.25)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1.25rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Sparkles size={18} color="#c084fc" />
                    <strong style={{ color: '#c084fc', fontSize: '0.95rem' }}>Pedagogical Overview</strong>
                  </div>
                  <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-main)' }}>
                    {ai.summary}
                  </p>
                </div>
              )}

              {/* Strengths & Weaknesses Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                {ai.strengths && ai.strengths.length > 0 && (
                  <div className="card" style={{ padding: '1rem' }}>
                    <h4 style={{ fontSize: '0.9rem', color: 'var(--success)', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <CheckCircle2 size={16} /> Key Strengths
                    </h4>
                    <ul style={{ paddingLeft: '1.2rem', fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                      {ai.strengths.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {ai.weaknesses && ai.weaknesses.length > 0 && (
                  <div className="card" style={{ padding: '1rem' }}>
                    <h4 style={{ fontSize: '0.9rem', color: 'var(--warning)', marginBottom: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <AlertTriangle size={16} /> Areas for Improvement
                    </h4>
                    <ul style={{ paddingLeft: '1.2rem', fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                      {ai.weaknesses.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Specific Observations */}
              {ai.observations && ai.observations.length > 0 && (
                <div style={{ marginTop: '0.5rem' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.85rem' }}>
                    Detailed Observations ({ai.observations.length})
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    {ai.observations.map((obs, idx) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: 'var(--bg-card)',
                          border: '1px solid var(--border-color)',
                          borderRadius: 'var(--radius-md)',
                          padding: '1.25rem',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                          <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.925rem' }}>
                            {obs.title}
                          </span>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <Badge variant="purple">{obs.category.replace('_', ' ')}</Badge>
                            <Badge variant={obs.severity === 'critical' || obs.severity === 'high' ? 'danger' : 'warning'}>
                              {obs.severity}
                            </Badge>
                          </div>
                        </div>

                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.6rem', lineHeight: 1.5 }}>
                          {obs.description}
                        </p>

                        {obs.code_evidence && (
                          <div style={{ marginBottom: '0.6rem' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600 }}>Code Evidence:</span>
                            <pre className="code-block" style={{ marginTop: '0.25rem', fontSize: '0.8rem' }}>
                              {obs.code_evidence}
                            </pre>
                          </div>
                        )}

                        {obs.suggestion && (
                          <div
                            style={{
                              backgroundColor: 'rgba(59, 130, 246, 0.08)',
                              borderLeft: '3px solid var(--primary)',
                              padding: '0.6rem 0.85rem',
                              borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                              fontSize: '0.825rem',
                              color: 'var(--text-main)',
                            }}
                          >
                            <span style={{ color: 'var(--primary)', fontWeight: 600 }}>Suggested Solution: </span>
                            {obs.suggestion}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
              Gemini AI pedagogical review is not yet generated for this report.
            </p>
          )}
        </div>
      )}

      {/* Tab 3: Rubric Criteria Evaluation */}
      {activeTab === 'rubric' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {report.rubric_evaluations && Object.keys(report.rubric_evaluations).length > 0 ? (
            Object.entries(report.rubric_evaluations).map(([critId, evalItem]) => (
              <div
                key={critId}
                style={{
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.25rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                  <strong style={{ fontSize: '0.95rem', color: 'var(--text-main)' }}>Criterion: {critId}</strong>
                  <Badge variant="purple">Score: {evalItem.score}</Badge>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  {evalItem.comment || 'No specific comments provided.'}
                </p>
              </div>
            ))
          ) : (
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
              No custom rubric criteria evaluations attached.
            </p>
          )}
        </div>
      )}
    </div>
  );
};

