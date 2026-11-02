import React, { useState, useEffect } from 'react';
import { Assignment, TestCase } from '../../types/api';
import { api } from '../../services/api';
import { useToast } from '../../context/ToastContext';
import { Modal } from '../common/Modal';
import { Plus, Trash2, BookOpen, Layers } from 'lucide-react';

interface AssignmentCreateEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  assignment: Assignment | null;
  onSaved: () => void;
}

export const AssignmentCreateEditModal: React.FC<AssignmentCreateEditModalProps> = ({
  isOpen,
  onClose,
  assignment,
  onSaved,
}) => {
  const { success, error: showError } = useToast();
  const isEditing = !!assignment;

  const [taskId, setTaskId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [maxScore, setMaxScore] = useState<number>(100);
  const [testCases, setTestCases] = useState<
    Array<{ test_case_id: string; description: string; points: number }>
  >([
    { test_case_id: 'tc1_basic_test', description: 'Validate standard inputs and boundary handling', points: 50 },
    { test_case_id: 'tc2_edge_cases', description: 'Validate empty collections and large integers', points: 50 },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (assignment) {
        setTaskId(assignment.task_id);
        setTitle(assignment.title);
        setDescription(assignment.description || '');
        setMaxScore(assignment.max_score);
        setTestCases(
          assignment.test_cases && assignment.test_cases.length > 0
            ? assignment.test_cases.map((tc) => ({
                test_case_id: tc.test_case_id,
                description: tc.description,
                points: tc.points,
              }))
            : [{ test_case_id: 'tc1', description: 'Default correctness test', points: 100 }]
        );
      } else {
        setTaskId('');
        setTitle('');
        setDescription('');
        setMaxScore(100);
        setTestCases([
          { test_case_id: 'tc1_correctness', description: 'Verify expected output on standard input', points: 50 },
          { test_case_id: 'tc2_edge_case', description: 'Verify handling of empty or negative arguments', points: 50 },
        ]);
      }
    }
  }, [isOpen, assignment]);

  const handleAddTestCase = () => {
    const nextId = `tc${testCases.length + 1}`;
    setTestCases([...testCases, { test_case_id: nextId, description: '', points: 25 }]);
  };

  const handleRemoveTestCase = (index: number) => {
    setTestCases(testCases.filter((_, i) => i !== index));
  };

  const handleUpdateTestCase = (index: number, field: string, value: any) => {
    const updated = [...testCases];
    updated[index] = { ...updated[index], [field]: value };
    setTestCases(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskId.trim() || !title.trim()) {
      showError('Validation Error', 'Task identifier and title are required.');
      return;
    }

    if (testCases.length === 0) {
      showError('Validation Error', 'At least one automated test case definition is required.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        task_id: taskId.trim(),
        title: title.trim(),
        description: description.trim() || undefined,
        max_score: Number(maxScore),
        test_cases: testCases.map((tc) => ({
          test_case_id: tc.test_case_id.trim(),
          description: tc.description.trim() || 'Automated verification test',
          points: Number(tc.points),
        })),
      };

      if (isEditing) {
        await api.updateInstructorAssignment(taskId, payload);
        success('Assignment Updated', `Changes to "${title}" were saved.`);
      } else {
        await api.createInstructorAssignment(payload);
        success('Assignment Created', `Assignment "${title}" is now available to students.`);
      }

      onSaved();
      onClose();
    } catch (err: any) {
      showError('Operation Failed', err.message || 'Could not save assignment.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? `Edit Assignment: ${assignment?.task_id}` : 'Create New Programming Assignment'}
      size="large"
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Task Identifier *</label>
            <input
              type="text"
              placeholder="e.g. data_struct_hw1"
              value={taskId}
              onChange={(e) => setTaskId(e.target.value)}
              disabled={isEditing}
              required
              className="form-input"
            />
            <p className="form-helper">Unique machine ID (alphanumeric, underscores, hyphens).</p>
          </div>

          <div className="form-group">
            <label className="form-label">Maximum Total Points *</label>
            <input
              type="number"
              min="1"
              max="1000"
              value={maxScore}
              onChange={(e) => setMaxScore(Number(e.target.value))}
              required
              className="form-input"
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Assignment Title *</label>
          <input
            type="text"
            placeholder="e.g. Binary Search Tree Implementation"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Description & Problem Statement</label>
          <textarea
            placeholder="Detailed instructions, requirements, runtime constraints, and specifications for students..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="form-textarea"
            rows={4}
          />
        </div>

        {/* Test Case Definitions Builder */}
        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Layers size={16} color="var(--primary)" /> Automated Verification Test Cases
              </h4>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Test cases executed deterministically in isolated worker sandbox.
              </p>
            </div>
            <button type="button" onClick={handleAddTestCase} className="btn btn-outline btn-sm" style={{ gap: '0.3rem' }}>
              <Plus size={14} /> Add Test Case
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {testCases.map((tc, idx) => (
              <div
                key={idx}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '150px 1fr 100px 40px',
                  gap: '0.75rem',
                  alignItems: 'center',
                  backgroundColor: 'var(--bg-secondary)',
                  padding: '0.75rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <div>
                  <input
                    type="text"
                    placeholder="Test ID"
                    value={tc.test_case_id}
                    onChange={(e) => handleUpdateTestCase(idx, 'test_case_id', e.target.value)}
                    required
                    className="form-input"
                    style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}
                  />
                </div>
                <div>
                  <input
                    type="text"
                    placeholder="Description / expectation"
                    value={tc.description}
                    onChange={(e) => handleUpdateTestCase(idx, 'description', e.target.value)}
                    required
                    className="form-input"
                    style={{ fontSize: '0.85rem' }}
                  />
                </div>
                <div>
                  <input
                    type="number"
                    placeholder="Points"
                    min="1"
                    value={tc.points}
                    onChange={(e) => handleUpdateTestCase(idx, 'points', Number(e.target.value))}
                    required
                    className="form-input"
                    style={{ fontSize: '0.85rem' }}
                  />
                </div>
                <div>
                  <button
                    type="button"
                    onClick={() => handleRemoveTestCase(idx)}
                    disabled={testCases.length <= 1}
                    className="btn btn-outline btn-sm"
                    style={{ border: 'none', color: 'var(--danger)', padding: '0.4rem' }}
                    title="Delete Test Case"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.25rem' }}>
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={isSubmitting} className="btn btn-primary">
            {isSubmitting ? 'Saving Assignment...' : isEditing ? 'Save Changes' : 'Publish Assignment'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

