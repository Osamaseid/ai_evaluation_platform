import React, { useState, useEffect } from 'react';
import { Assignment, GradingRubric } from '../../types/api';
import { api } from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { Modal } from '../common/Modal';
import { Plus, Trash2, Sliders } from 'lucide-react';

interface RubricConfigurationModalProps {
  isOpen: boolean;
  onClose: () => void;
  assignment: Assignment | null;
  onSaved: () => void;
}

export const RubricConfigurationModal: React.FC<RubricConfigurationModalProps> = ({
  isOpen,
  onClose,
  assignment,
  onSaved,
}) => {
  const { success, error: showError } = useToast();
  const [criteria, setCriteria] = useState<
    Array<{ criterion_id: string; name: string; description: string; max_points: number; weight: number }>
  >([
    { criterion_id: 'algorithm_correctness', name: 'Algorithmic Logic', description: 'Correct algorithm design and boundary case handling', max_points: 30, weight: 1.0 },
    { criterion_id: 'code_readability', name: 'Code Style & Formatting', description: 'Clean PEP8 formatting, descriptive naming, clean structure', max_points: 20, weight: 1.0 },
    { criterion_id: 'time_complexity', name: 'Time & Space Efficiency', description: 'Optimal asymptotic complexity', max_points: 25, weight: 1.0 },
    { criterion_id: 'robustness', name: 'Robustness & Error Handling', description: 'Defensive validations and handling of unexpected inputs', max_points: 25, weight: 1.0 },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen && assignment) {
      api
        .getRubric(assignment.task_id)
        .then((r) => {
          if (r && r.criteria && r.criteria.length > 0) {
            setCriteria(r.criteria);
          }
        })
        .catch(() => {
          // Use default criteria set
        });
    }
  }, [isOpen, assignment]);

  if (!assignment) return null;

  const handleAddCriterion = () => {
    const nextId = `crit_${criteria.length + 1}`;
    setCriteria([
      ...criteria,
      { criterion_id: nextId, name: 'New Criterion', description: 'Evaluation criteria details', max_points: 20, weight: 1.0 },
    ]);
  };

  const handleRemoveCriterion = (idx: number) => {
    setCriteria(criteria.filter((_, i) => i !== idx));
  };

  const handleUpdateCriterion = (idx: number, field: string, value: any) => {
    const updated = [...criteria];
    updated[idx] = { ...updated[idx], [field]: value };
    setCriteria(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (criteria.length === 0) {
      showError('Validation Error', 'At least one criterion is required.');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.createRubric({
        task_id: assignment.task_id,
        criteria: criteria.map((c) => ({
          criterion_id: c.criterion_id.trim(),
          name: c.name.trim(),
          description: c.description.trim(),
          max_points: Number(c.max_points),
          weight: Number(c.weight || 1.0),
        })),
      });

      success('Rubric Saved', `Grading rubric for ${assignment.task_id} successfully updated.`);
      onSaved();
      onClose();
    } catch (err: any) {
      showError('Rubric Save Failed', err.message || 'Could not update rubric.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Configure Grading Rubric: ${assignment.title}`}
      size="large"
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Define structured criteria for subjective scoring and manual review rubrics.
          </p>
          <button type="button" onClick={handleAddCriterion} className="btn btn-outline btn-sm" style={{ gap: '0.35rem' }}>
            <Plus size={14} /> Add Criterion
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {criteria.map((c, idx) => (
            <div
              key={idx}
              style={{
                padding: '1rem',
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.65rem',
              }}
            >
              <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr 100px 40px', gap: '0.75rem', alignItems: 'center' }}>
                <input
                  type="text"
                  placeholder="ID (e.g. style)"
                  value={c.criterion_id}
                  onChange={(e) => handleUpdateCriterion(idx, 'criterion_id', e.target.value)}
                  required
                  className="form-input"
                  style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}
                />
                <input
                  type="text"
                  placeholder="Criterion Name (e.g. Readability)"
                  value={c.name}
                  onChange={(e) => handleUpdateCriterion(idx, 'name', e.target.value)}
                  required
                  className="form-input"
                  style={{ fontSize: '0.85rem', fontWeight: 600 }}
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <input
                    type="number"
                    min="1"
                    placeholder="Points"
                    value={c.max_points}
                    onChange={(e) => handleUpdateCriterion(idx, 'max_points', Number(e.target.value))}
                    required
                    className="form-input"
                    style={{ fontSize: '0.85rem' }}
                  />
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>pts</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveCriterion(idx)}
                  disabled={criteria.length <= 1}
                  className="btn btn-outline btn-sm"
                  style={{ border: 'none', color: 'var(--danger)', padding: '0.35rem' }}
                  title="Remove Criterion"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              <input
                type="text"
                placeholder="Description of standards expected for maximum score..."
                value={c.description}
                onChange={(e) => handleUpdateCriterion(idx, 'description', e.target.value)}
                className="form-input"
                style={{ fontSize: '0.825rem' }}
              />
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={isSubmitting} className="btn btn-primary">
            {isSubmitting ? 'Saving Rubric...' : 'Save Rubric'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

