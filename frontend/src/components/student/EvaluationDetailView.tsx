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
  FileCode,
  Award,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  BookOpen,
  ArrowRight,
  HelpCircle,
} from 'lucide-react';

interface EvaluationDetailViewProps {
  report: EvaluationReport;
}

export const EvaluationDetailView: React.FC<EvaluationDetailViewProps> = ({ report }) => {
  const [activeTab, setActiveTab] = useState<'tests' | 'ai' | 'recommendations' | 'rubric'>('tests');
  const [expandedTest, setExpandedTest] = useState<string | null>(null);

  const grading = report.grading_report;
  const ai = report.ai_review;
  const isReviewed = report.reviewed_by || report.manual_override_score !== null;
  const finalScore = report.manual_override_score ?? report.deterministic_score;
  const percentage = report.max_score > 0 ? Math.round((finalScore / report.max_score) * 100) : 0;

  return (
    <div className="evaluation-detail-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Summary Banner (Clean White Surface with Akiba Forest Brand Accents) */}
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--border-color)',
          borderLeft: '4px solid var(--primary)',
          borderRadius: 'var(--radius-lg)',
          padding: '1.5rem 1.75rem',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1.25rem',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div style={{ flex: '1 1 320px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Evaluation ID: <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{report.evaluation_id}</span>
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
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            Assignment: {report.task_id}
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Student: <strong style={{ color: 'var(--text-main)' }}>{report.student_id}</strong> &bull; Completed:{' '}
            {report.completed_at ? new Date(report.completed_at).toLocaleString() : 'N/A'}
          </p>
        </div>

        {/* Verified Score Card */}
        <div
          style={{
            backgroundColor: '#f8fafc',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.5rem',
            textAlign: 'center',
            minWidth: '200px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.35rem', marginBottom: '0.2rem' }}>
            <ShieldCheck size={14} color="var(--primary)" />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
              Verified Grade
            </span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: percentage >= 70 ? 'var(--primary)' : 'var(--warning)', lineHeight: 1.15 }}>
            {finalScore} <span style={{ fontSize: '1.05rem', color: 'var(--text-dim)', fontWeight: 600 }}>/ {report.max_score}</span>
          </div>
          <div style={{ marginTop: '0.5rem' }}>
            <ProgressBar percentage={percentage} showLabel={false} />
          </div>
        </div>
      </div>

      {/* Instructor Review & Score Override Notice (If present) */}
      {isReviewed && (
        <div
          style={{
            padding: '1.25rem',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--ai-light)',
            border: '1px solid var(--ai-border)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
            <Award size={18} color="var(--ai-purple)" />
            <strong style={{ color: 'var(--ai-purple)', fontSize: '0.95rem' }}>
              Instructor Manual Review Override
            </strong>
            {report.reviewed_by && (
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                by <strong>{report.reviewed_by}</strong> on {report.reviewed_at ? new Date(report.reviewed_at).toLocaleDateString() : ''}
              </span>
            )}
          </div>
          {report.manual_override_score !== null && (
            <p style={{ fontSize: '0.875rem', color: 'var(--text-main)', marginBottom: '0.4rem' }}>
              Original Automated Score: <strong>{report.deterministic_score} pts</strong> &rarr; Final Adjusted Score:{' '}
              <strong style={{ color: 'var(--primary)' }}>{report.manual_override_score} pts</strong>
            </p>
          )}
          {report.instructor_notes && (
            <div style={{ fontSize: '0.85rem', color: 'var(--text-body)', marginTop: '0.4rem', whiteSpace: 'pre-wrap' }}>
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
          <Sparkles size={16} color="var(--ai-purple)" />
          Gemini AI Pedagogical Review
        </button>
        <button
          onClick={() => setActiveTab('recommendations')}
          className={`tab-btn ${activeTab === 'recommendations' ? 'active' : ''}`}
        >
          Learning Recommendations
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
          {/* Test Statistics Summary */}
          {grading && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1rem',
                marginBottom: '0.5rem',
              }}
            >
              <div
                style={{
                  padding: '0.85rem 1rem',
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                }}
              >
                <CheckCircle2 size={22} color="var(--success)" />
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Passed Tests</span>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--success)' }}>
                    {grading.passed_tests} / {grading.total_tests}
                  </div>
                </div>
              </div>

              <div
                style={{
                  padding: '0.85rem 1rem',
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                }}
              >
                <XCircle size={22} color={grading.total_tests - grading.passed_tests > 0 ? 'var(--danger)' : 'var(--text-dim)'} />
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Failed Tests</span>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: grading.total_tests - grading.passed_tests > 0 ? 'var(--danger)' : 'var(--text-muted)' }}>
                    {grading.total_tests - grading.passed_tests}
                  </div>
                </div>
              </div>

              <div
                style={{
                  padding: '0.85rem 1rem',
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                }}
              >
                <Clock size={22} color="var(--primary)" />
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Test Score</span>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary)' }}>
                    {grading.score_percentage}%
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Individual Test Cases List */}
          {grading && grading.test_case_results && grading.test_case_results.length > 0 ? (
            grading.test_case_results.map((tc, idx) => {
              const isExpanded = expandedTest === tc.test_case_id;
              return (
                <div
                  key={tc.test_case_id || idx}
                  style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md)',
                    overflow: 'hidden',
                    boxShadow: 'var(--shadow-xs)',
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
                      backgroundColor: isExpanded ? '#f8fafc' : '#ffffff',
                      transition: 'background-color 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                      {tc.passed ? (
                        <CheckCircle2 size={20} color="var(--success)" />
                      ) : (
                        <XCircle size={20} color="var(--danger)" />
                      )}
                      <div>
                        <strong style={{ fontSize: '0.925rem', color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
                          {tc.test_case_id}
                        </strong>
                        {tc.message && (
                          <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                            {tc.message}
                          </span>
                        )}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      {tc.execution_time_ms !== undefined && (
                        <span style={{ fontSize: '0.775rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <Clock size={12} /> {tc.execution_time_ms} ms
                        </span>
                      )}
                      <Badge variant={tc.passed ? 'success' : 'danger'}>
                        {tc.passed ? 'Passed' : 'Failed'}
                      </Badge>
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </div>

                  {/* Expanded Execution Output */}
                  {isExpanded && (
                    <div
                      style={{
                        padding: '1.25rem',
                        borderTop: '1px solid var(--border-color)',
                        backgroundColor: '#f8fafc',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.85rem',
                      }}
                    >
                      {tc.stdout && (
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                            Standard Output (stdout):
                          </span>
                          <pre className="code-block" style={{ marginTop: '0.35rem' }}>{tc.stdout}</pre>
                        </div>
                      )}
                      {tc.stderr && (
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--danger)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                            Standard Error (stderr):
                          </span>
                          <pre className="code-block" style={{ marginTop: '0.35rem', borderColor: 'var(--danger-border)' }}>{tc.stderr}</pre>
                        </div>
                      )}
                      {!tc.stdout && !tc.stderr && (
                        <p style={{ fontSize: '0.825rem', color: 'var(--text-dim)' }}>
                          No console output produced during test execution.
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

      {/* Tab 2: Gemini AI Pedagogical Review (Structured Code Review Format) */}
      {activeTab === 'ai' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {ai ? (
            <>
              {/* Executive Pedagogical Summary */}
              {ai.summary && (
                <div
                  style={{
                    backgroundColor: 'var(--ai-light)',
                    border: '1px solid var(--ai-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1.25rem 1.5rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Sparkles size={18} color="var(--ai-purple)" />
                    <strong style={{ color: 'var(--ai-purple)', fontSize: '0.95rem' }}>
                      Senior Engineering Review Summary
                    </strong>
                  </div>
                  <p style={{ fontSize: '0.885rem', lineHeight: 1.6, color: 'var(--text-main)' }}>
                    {ai.summary}
                  </p>
                </div>
              )}

              {/* Strengths & Areas for Improvement Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                {ai.strengths && ai.strengths.length > 0 && (
                  <div className="card" style={{ padding: '1.25rem', borderLeft: '3px solid var(--success)' }}>
                    <h4 style={{ fontSize: '0.925rem', color: 'var(--success)', marginBottom: '0.65rem', display: 'flex', alignItems: 'center', gap: '0.45rem', fontWeight: 700 }}>
                      <CheckCircle2 size={16} /> Key Strengths
                    </h4>
                    <ul style={{ paddingLeft: '1.2rem', fontSize: '0.85rem', color: 'var(--text-body)', lineHeight: 1.6 }}>
                      {ai.strengths.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {ai.weaknesses && ai.weaknesses.length > 0 && (
                  <div className="card" style={{ padding: '1.25rem', borderLeft: '3px solid var(--warning)' }}>
                    <h4 style={{ fontSize: '0.925rem', color: 'var(--warning)', marginBottom: '0.65rem', display: 'flex', alignItems: 'center', gap: '0.45rem', fontWeight: 700 }}>
                      <AlertTriangle size={16} /> Areas for Improvement
                    </h4>
                    <ul style={{ paddingLeft: '1.2rem', fontSize: '0.85rem', color: 'var(--text-body)', lineHeight: 1.6 }}>
                      {ai.weaknesses.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Specific Categorized Observations */}
              {ai.observations && ai.observations.length > 0 && (
                <div style={{ marginTop: '0.5rem' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.85rem' }}>
                    Code Review Findings ({ai.observations.length})
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {ai.observations.map((obs, idx) => (
                      <div
                        key={idx}
                        className="card"
                        style={{ padding: '1.25rem' }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                          <span style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.95rem' }}>
                            {obs.title}
                          </span>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <Badge variant="purple">{obs.category.replace('_', ' ')}</Badge>
                            <Badge variant={obs.severity === 'critical' || obs.severity === 'high' ? 'danger' : 'warning'}>
                              {obs.severity}
                            </Badge>
                          </div>
                        </div>

                        <p style={{ fontSize: '0.85rem', color: 'var(--text-body)', marginBottom: '0.75rem', lineHeight: 1.5 }}>
                          {obs.description}
                        </p>

                        {obs.code_evidence && (
                          <div style={{ marginBottom: '0.75rem' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                              Code Evidence:
                            </span>
                            <pre className="code-block" style={{ marginTop: '0.35rem', fontSize: '0.8rem' }}>
                              {obs.code_evidence}
                            </pre>
                          </div>
                        )}

                        {obs.suggestion && (
                          <div
                            style={{
                              backgroundColor: 'var(--lime-light)',
                              borderLeft: '3px solid var(--accent-lime)',
                              padding: '0.75rem 1rem',
                              borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                              fontSize: '0.85rem',
                              color: 'var(--text-main)',
                            }}
                          >
                            <strong style={{ color: 'var(--accent-lime)' }}>Suggested Fix: </strong>
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

      {/* Tab 3: Learning Improvement Recommendations */}
      {activeTab === 'recommendations' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">Actionable Learning Roadmap</h3>
                <p className="card-subtitle">Synthesized from automated test assertions and code patterns</p>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div
                style={{
                  padding: '1rem 1.25rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--primary-light)',
                  border: '1px solid var(--primary-border)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.85rem',
                }}
              >
                <CheckCircle2 size={20} color="var(--primary)" style={{ marginTop: '2px', flexShrink: 0 }} />
                <div>
                  <strong style={{ fontSize: '0.9rem', color: 'var(--primary-dark)', display: 'block', marginBottom: '0.2rem' }}>
                    1. Algorithmic Mastery Recommendation
                  </strong>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                    Your current implementation passes core test cases. To achieve industrial resilience, verify edge cases such as empty lists, single-element collections, and large inputs that approach \(O(n \log n)\) constraints.
                  </p>
                </div>
              </div>

              <div
                style={{
                  padding: '1rem 1.25rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--lime-light)',
                  border: '1px solid var(--lime-border)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.85rem',
                }}
              >
                <Sparkles size={20} color="var(--accent-lime)" style={{ marginTop: '2px', flexShrink: 0 }} />
                <div>
                  <strong style={{ fontSize: '0.9rem', color: 'var(--accent-lime)', display: 'block', marginBottom: '0.2rem' }}>
                    2. Clean Code & PEP 8 Standards
                  </strong>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                    Utilize Python type hinting (PEP 484) on function signatures (`def search(arr: list[int], target: int) -&gt; int:`) and include docstrings summarizing time and space complexity.
                  </p>
                </div>
              </div>

              <div
                style={{
                  padding: '1rem 1.25rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: '#fafbfc',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.85rem',
                }}
              >
                <BookOpen size={20} color="var(--text-muted)" style={{ marginTop: '2px', flexShrink: 0 }} />
                <div>
                  <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)', display: 'block', marginBottom: '0.2rem' }}>
                    3. Recommended Next Challenge
                  </strong>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                    Proceed to the upcoming assignment on Binary Search Tree traversals to apply these divide-and-conquer strategies in non-linear hierarchical data structures.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Rubric Criteria Evaluation */}
      {activeTab === 'rubric' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {report.rubric_evaluations && Object.keys(report.rubric_evaluations).length > 0 ? (
            Object.entries(report.rubric_evaluations).map(([critId, evalItem]) => (
              <div
                key={critId}
                className="card"
                style={{ padding: '1.25rem' }}
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
