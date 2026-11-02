import React, { useState, useEffect } from 'react';
import { EvaluationReport, GradingRubric } from '../../types/api';
import { api } from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { Modal } from '../common/Modal';
import { Badge } from '../common/Badge';
import { Award, FileText, CheckCircle2, AlertCircle } from 'lucide-react';

interface ManualReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  evaluation: EvaluationReport | null;
  onReviewSaved: () => void;
}

export const ManualReviewModal: React.FC<ManualReviewModalProps> = ({
  isOpen,
  onClose,
  evaluation,
  onReviewSaved,
}) => {
  const { success, error: showError } = useToast();
  const [overrideScore, setOverrideScore] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [rubric, setRubric] = useState<GradingRubric | null>(null);
  const [rubricScores, setRubricScores] = useState<Record<string, { score: number; comment: string }>>({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen && evaluation) {
      setOverrideScore(
        evaluation.manual_override_score !== null && evaluation.manual_override_score !== undefined
          ? String(evaluation.manual_override_score)
          : String(evaluation.deterministic_score)
      );
      setNotes(evaluation.instructor_notes || '');

      // Load rubric for the assignment
      api
        .getRubric(evaluation.task_id)
        .then((r) => {
          setRubric(r);
          if (r && r.criteria) {
            const initialScores: Record<string, { score: number; comment: string }> = {};
            r.criteria.forEach((c) => {
              const existing = evaluation.rubric_evaluations?.[c.criterion_id];
              initialScores[c.criterion_id] = {
                score: existing ? existing.score : c.max_points,
                comment: existing ? existing.comment : '',
              };
            });
            setRubricScores(initialScores);
          }
        })
        .catch(() => setRubric(null));
    }
  }, [isOpen, evaluation]);

  if (!evaluation) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);

    try {
      const parsedOverride = overrideScore.trim() !== '' ? Number(overrideScore) : null;
      if (parsedOverride !== null && (isNaN(parsedOverride) || parsedOverride < 0)) {
        showError('Invalid Score', 'Score override must be a positive number.');
        setIsSaving(false);
        return;
      }

      // Format rubric evaluations
      const rubricMap: Record<string, { criterion_id: string; score: number; comment: string }> = {};
      Object.entries(rubricScores).forEach(([critId, val]) => {
        rubricMap[critId] = {
          criterion_id: critId,
          score: val.score,
          comment: val.comment,
        };
      });

      await api.applyManualReview(evaluation.evaluation_id, {
        manual_override_score: parsedOverride,
        instructor_notes: notes.trim() || undefined,
        rubric_evaluations: Object.keys(rubricMap).length > 0 ? rubricMap : undefined,
      });

      success('Manual Review Saved', `Score updated to ${parsedOverride ?? evaluation.deterministic_score}`);
      onReviewSaved();
      onClose();
    } catch (err: any) {
      showError('Review Update Failed', err.message || 'Could not save instructor review.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Manual Review: ${evaluation.student_id} (${evaluation.task_id})`}
      size="large"
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Baseline Evaluation Summary */}
        <div
          style={{
            padding: '1rem',
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Deterministic Test Score
            </span>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>
              {evaluation.deterministic_score} / {evaluation.max_score} pts
            </div>
          </div>
          <Badge variant={evaluation.status === 'completed' ? 'success' : 'warning'}>
            Status: {evaluation.status}
          </Badge>
        </div>

        {/* Override Score Input */}
        <div className="form-group">
          <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Award size={16} color="var(--primary)" /> Final Score Override
          </label>
          <input
            type="number"
            step="0.5"
            min="0"
            max={evaluation.max_score}
            value={overrideScore}
            onChange={(e) => setOverrideScore(e.target.value)}
            className="form-input"
            style={{ width: '180px' }}
            required
          />
          <p className="form-helper">
            Adjust the final grade if manual inspection or edge-case adjustments warrant it.
          </p>
        </div>

        {/* Instructor Notes */}
        <div className="form-group">
          <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <FileText size={16} color="var(--ai-purple)" /> Instructor Pedagogical Feedback
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Provide personalized commentary, algorithm advice, or suggestions for the student..."
            className="form-textarea"
            rows={4}
          />
          <p className="form-helper">
            These notes will be displayed directly on the student's evaluation report.
          </p>
        </div>

        {/* Rubric Criteria Scoring (if applicable) */}
        {rubric && rubric.criteria && rubric.criteria.length > 0 && (
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.75rem' }}>
              Rubric Assessment Criteria
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {rubric.criteria.map((c) => {
                const current = rubricScores[c.criterion_id] || { score: c.max_points, comment: '' };
                return (
                  <div
                    key={c.criterion_id}
                    style={{
                      padding: '1rem',
                      backgroundColor: 'var(--bg-card-subtle)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-md)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>{c.name}</strong>
                        <p style={{ fontSize: '0.775rem', color: 'var(--text-muted)' }}>{c.description}</p>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Points:</span>
                        <input
                          type="number"
                          min="0"
                          max={c.max_points}
                          value={current.score}
                          onChange={(e) =>
                            setRubricScores({
                              ...rubricScores,
                              [c.criterion_id]: { ...current, score: Number(e.target.value) },
                            })
                          }
                          className="form-input"
                          style={{ width: '80px', padding: '0.35rem 0.5rem' }}
                        />
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>/ {c.max_points}</span>
                      </div>
                    </div>

                    <input
                      type="text"
                      placeholder="Comment for this criterion (optional)..."
                      value={current.comment}
                      onChange={(e) =>
                        setRubricScores({
                          ...rubricScores,
                          [c.criterion_id]: { ...current, comment: e.target.value },
                        })
                      }
                      className="form-input"
                      style={{ fontSize: '0.825rem' }}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={isSaving} className="btn btn-primary">
            {isSaving ? 'Saving Review...' : 'Save Manual Review'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

