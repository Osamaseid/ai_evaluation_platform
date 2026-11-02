import React, { useState, useEffect, useCallback } from 'react';
import { EvaluationReport, Submission } from '../../types/api';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Badge } from '../common/Badge';
import { Modal } from '../common/Modal';
import { LoadingSpinner, ErrorAlert, EmptyState } from '../common/FeedbackStates';
import { EvaluationDetailView } from './EvaluationDetailView';
import {
  History,
  FileCode,
  Github,
  Play,
  Eye,
  CheckCircle2,
  Clock,
  RotateCw,
} from 'lucide-react';

export const SubmissionHistory: React.FC = () => {
  const { user } = useAuth();
  const { success, error: showError, info } = useToast();

  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected evaluation for detail modal
  const [selectedEvaluation, setSelectedEvaluation] = useState<EvaluationReport | null>(null);
  const [isEvaluationLoading, setIsEvaluationLoading] = useState(false);
  const [evaluatingSubId, setEvaluatingSubId] = useState<string | null>(null);

  const studentId = user?.user_id || 'student_ada';

  const fetchHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const resp = await api.getStudentSubmissions(studentId, 50, 0);
      setSubmissions(resp.items || []);
    } catch (err: any) {
      setError(err.message || 'Could not load your submission history.');
    } finally {
      setIsLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleViewEvaluation = async (submissionId: string) => {
    setIsEvaluationLoading(true);
    try {
      const report = await api.getEvaluationBySubmission(submissionId);
      setSelectedEvaluation(report);
    } catch (err: any) {
      showError('Evaluation Not Found', 'This submission may not have finished evaluating yet.');
    } finally {
      setIsEvaluationLoading(false);
    }
  };

  const handleRunEvaluation = async (submissionId: string) => {
    setEvaluatingSubId(submissionId);
    info('Evaluating Submission', 'Running tests and generating Gemini AI code review...');
    try {
      const report = await api.runEvaluation(submissionId);
      success('Evaluation Complete', `Score: ${report.deterministic_score}/${report.max_score}`);
      await fetchHistory();
      setSelectedEvaluation(report);
    } catch (err: any) {
      showError('Evaluation Failed', err.message || 'Error executing evaluation.');
    } finally {
      setEvaluatingSubId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
      case 'evaluated':
        return <Badge variant="success">Evaluated</Badge>;
      case 'running_tests':
      case 'validating':
      case 'reviewing_code':
        return <Badge variant="warning">Evaluating</Badge>;
      case 'failed':
        return <Badge variant="danger">Failed</Badge>;
      default:
        return <Badge variant="info">Submitted</Badge>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)' }}>
            Submission History & Evaluation Reports
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Review past submissions, test case breakdowns, and Gemini AI feedback.
          </p>
        </div>

        <button onClick={fetchHistory} className="btn btn-outline btn-sm" style={{ gap: '0.35rem' }}>
          <RotateCw size={14} /> Refresh
        </button>
      </div>

      {error && <ErrorAlert message={error} onRetry={fetchHistory} />}

      {isLoading ? (
        <LoadingSpinner message="Loading your submission history..." />
      ) : submissions.length === 0 ? (
        <EmptyState
          title="No submissions recorded"
          description="You haven't submitted any code assignments yet. Pick an available assignment and submit your solution."
          icon={<History size={48} />}
        />
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Submission ID</th>
                <th>Task ID</th>
                <th>Source Type</th>
                <th>Reference</th>
                <th>Status</th>
                <th>Submitted At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {submissions.map((sub) => (
                <tr key={sub.submission_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary)' }}>
                    {sub.submission_id}
                  </td>
                  <td>
                    <strong style={{ color: 'var(--text-main)' }}>{sub.task_id}</strong>
                  </td>
                  <td>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', textTransform: 'capitalize' }}>
                      {sub.source_type === 'github' ? <Github size={14} /> : <FileCode size={14} />}
                      {sub.source_type}
                    </span>
                  </td>
                  <td
                    style={{
                      maxWidth: '220px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.8rem',
                      color: 'var(--text-muted)',
                    }}
                    title={sub.source_reference}
                  >
                    {sub.source_reference}
                  </td>
                  <td>{getStatusBadge(sub.status)}</td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                    {new Date(sub.created_at).toLocaleString()}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      {sub.status === 'evaluated' || sub.status === 'completed' ? (
                        <button
                          onClick={() => handleViewEvaluation(sub.submission_id)}
                          disabled={isEvaluationLoading}
                          className="btn btn-outline btn-sm"
                          style={{ gap: '0.3rem' }}
                        >
                          <Eye size={14} /> View Report
                        </button>
                      ) : (
                        <button
                          onClick={() => handleRunEvaluation(sub.submission_id)}
                          disabled={evaluatingSubId === sub.submission_id}
                          className="btn btn-primary btn-sm"
                          style={{ gap: '0.3rem' }}
                        >
                          <Play size={14} />
                          {evaluatingSubId === sub.submission_id ? 'Evaluating...' : 'Evaluate'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Evaluation Report Modal */}
      <Modal
        isOpen={!!selectedEvaluation}
        onClose={() => setSelectedEvaluation(null)}
        title="Comprehensive Evaluation Report"
        size="large"
      >
        {selectedEvaluation && <EvaluationDetailView report={selectedEvaluation} />}
      </Modal>
    </div>
  );
};

