import React, { useState, useEffect, useCallback } from 'react';
import { Assignment, EvaluationReport, Submission } from '../../types/api';
import { api } from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { Badge } from '../common/Badge';
import { Modal } from '../common/Modal';
import { LoadingSpinner, ErrorAlert, EmptyState } from '../common/FeedbackStates';
import { ManualReviewModal } from './ManualReviewModal';
import { EvaluationDetailView } from '../student/EvaluationDetailView';
import {
  FileCheck2,
  Award,
  Eye,
  Play,
  RotateCw,
  Filter,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

export const SubmissionMonitoring: React.FC = () => {
  const { success, error: showError, info } = useToast();
  const [evaluations, setEvaluations] = useState<EvaluationReport[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [taskFilter, setTaskFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Modals
  const [reviewEvaluation, setReviewEvaluation] = useState<EvaluationReport | null>(null);
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [reportEvaluation, setReportEvaluation] = useState<EvaluationReport | null>(null);

  const fetchMonitoringData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [evals, asgns] = await Promise.all([
        api.listInstructorEvaluations(taskFilter !== 'all' ? taskFilter : undefined),
        api.listInstructorAssignments(),
      ]);
      setEvaluations(evals || []);
      setAssignments(asgns || []);
    } catch (err: any) {
      setError(err.message || 'Could not load submission evaluations.');
    } finally {
      setIsLoading(false);
    }
  }, [taskFilter]);

  useEffect(() => {
    fetchMonitoringData();
  }, [fetchMonitoringData]);

  const filteredEvaluations = evaluations.filter((ev) => {
    if (statusFilter !== 'all' && ev.status !== statusFilter) return false;
    return true;
  });

  const handleOpenReview = (ev: EvaluationReport) => {
    setReviewEvaluation(ev);
    setIsReviewOpen(true);
  };

  const handleOpenReport = (ev: EvaluationReport) => {
    setReportEvaluation(ev);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)' }}>
            Submission Monitoring & Manual Review
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Monitor student evaluation results, review Gemini AI feedback, and apply manual grade overrides.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {/* Assignment Filter */}
          <select
            value={taskFilter}
            onChange={(e) => setTaskFilter(e.target.value)}
            className="form-select"
            style={{ width: '180px', padding: '0.45rem 0.75rem' }}
          >
            <option value="all">All Assignments</option>
            {assignments.map((a) => (
              <option key={a.task_id} value={a.task_id}>
                {a.task_id}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="form-select"
            style={{ width: '140px', padding: '0.45rem 0.75rem' }}
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
          </select>

          <button onClick={fetchMonitoringData} className="btn btn-outline btn-sm" style={{ gap: '0.35rem' }}>
            <RotateCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={fetchMonitoringData} />}

      {isLoading ? (
        <LoadingSpinner message="Loading evaluated submissions and audit trails..." />
      ) : filteredEvaluations.length === 0 ? (
        <EmptyState
          title="No evaluations found"
          description={
            taskFilter !== 'all' || statusFilter !== 'all'
              ? 'No evaluations match your active filters. Try resetting the filters.'
              : 'No student submissions have been evaluated yet. Once students submit assignments, they will appear here.'
          }
          icon={<FileCheck2 size={48} />}
        />
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Evaluation ID</th>
                <th>Task ID</th>
                <th>Student ID</th>
                <th>Automated Score</th>
                <th>Final Adjusted</th>
                <th>Review Status</th>
                <th>Timestamp</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvaluations.map((ev) => {
                const isOverridden = ev.manual_override_score !== null && ev.manual_override_score !== undefined;
                const finalScore = isOverridden ? ev.manual_override_score : ev.deterministic_score;
                const pct = ev.max_score > 0 ? ((finalScore || 0) / ev.max_score) * 100 : 0;

                return (
                  <tr key={ev.evaluation_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary)' }}>
                      {ev.evaluation_id}
                    </td>
                    <td>
                      <strong style={{ color: 'var(--text-main)' }}>{ev.task_id}</strong>
                    </td>
                    <td>
                      <span style={{ fontWeight: 500, color: 'var(--text-main)' }}>{ev.student_id}</span>
                    </td>
                    <td>
                      <span style={{ color: 'var(--text-muted)' }}>
                        {ev.deterministic_score} / {ev.max_score}
                      </span>
                    </td>
                    <td>
                      <strong style={{ color: pct >= 70 ? 'var(--success)' : 'var(--warning)', fontSize: '0.95rem' }}>
                        {finalScore} <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>({Math.round(pct)}%)</span>
                      </strong>
                    </td>
                    <td>
                      {isOverridden ? (
                        <Badge variant="purple" icon={<Award size={12} />}>
                          Reviewed
                        </Badge>
                      ) : (
                        <Badge variant="neutral">Automated</Badge>
                      )}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                      {ev.completed_at ? new Date(ev.completed_at).toLocaleString() : 'N/A'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          onClick={() => handleOpenReport(ev)}
                          className="btn btn-outline btn-sm"
                          style={{ gap: '0.3rem' }}
                        >
                          <Eye size={14} /> View
                        </button>
                        <button
                          onClick={() => handleOpenReview(ev)}
                          className="btn btn-secondary btn-sm"
                          style={{ gap: '0.3rem' }}
                        >
                          <Award size={14} /> Review & Override
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

      {/* Manual Review Modal */}
      <ManualReviewModal
        isOpen={isReviewOpen}
        onClose={() => setIsReviewOpen(false)}
        evaluation={reviewEvaluation}
        onReviewSaved={fetchMonitoringData}
      />

      {/* Full Evaluation Report View Modal */}
      <Modal
        isOpen={!!reportEvaluation}
        onClose={() => setReportEvaluation(null)}
        title="Student Evaluation Audit & Gemini AI Report"
        size="large"
      >
        {reportEvaluation && <EvaluationDetailView report={reportEvaluation} />}
      </Modal>
    </div>
  );
};

