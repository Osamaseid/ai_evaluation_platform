import React, { useState, useEffect, useCallback } from 'react';
import { Student } from '../../types/api';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Modal } from '../common/Modal';
import { LoadingSpinner, ErrorAlert, EmptyState } from '../common/FeedbackStates';
import { Users, UserPlus, Mail, RotateCw, Calendar } from 'lucide-react';

export const StudentManagement: React.FC = () => {
  const { user } = useAuth();
  const { success, error: showError } = useToast();
  const [students, setStudents] = useState<Student[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Enroll modal
  const [isEnrollOpen, setIsEnrollOpen] = useState(false);
  const [studentId, setStudentId] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchStudents = useCallback(async () => {
    if (!user || (user.role !== 'instructor' && user.role !== 'admin')) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const resp = await api.listStudents(100, 0);
      setStudents(resp.items || []);
    } catch (err: any) {
      setError(err.message || 'Could not load student roster.');
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  const handleEnroll = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId.trim() || !name.trim() || !email.trim()) {
      showError('Validation Error', 'All student fields are required.');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.enrollStudent({
        student_id: studentId.trim(),
        name: name.trim(),
        email: email.trim(),
      });

      success('Student Enrolled', `${name} (${studentId}) was registered in the course.`);
      setIsEnrollOpen(false);
      setStudentId('');
      setName('');
      setEmail('');
      fetchStudents();
    } catch (err: any) {
      showError('Enrollment Failed', err.message || 'Could not enroll student.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)' }}>
            Student Roster & Enrollment
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Manage registered students, track enrollment, and review student progress.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={fetchStudents} className="btn btn-outline btn-sm" style={{ gap: '0.35rem' }}>
            <RotateCw size={14} /> Refresh
          </button>
          <button onClick={() => setIsEnrollOpen(true)} className="btn btn-primary" style={{ gap: '0.4rem' }}>
            <UserPlus size={16} /> Enroll New Student
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={fetchStudents} />}

      {isLoading ? (
        <LoadingSpinner message="Loading course students..." />
      ) : students.length === 0 ? (
        <EmptyState
          title="No students enrolled"
          description="Click 'Enroll New Student' to add students to this evaluation platform."
          icon={<Users size={48} />}
          action={{
            label: 'Enroll First Student',
            onClick: () => setIsEnrollOpen(true),
          }}
        />
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Full Name</th>
                <th>Email Address</th>
                <th>Enrolled Date</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                <tr key={student.student_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary)' }}>
                    {student.student_id}
                  </td>
                  <td>
                    <strong style={{ color: 'var(--text-main)' }}>{student.name}</strong>
                  </td>
                  <td style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Mail size={14} color="var(--text-dim)" /> {student.email}
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                    {new Date(student.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Enroll Student Modal */}
      <Modal
        isOpen={isEnrollOpen}
        onClose={() => setIsEnrollOpen(false)}
        title="Enroll New Student"
        size="normal"
      >
        <form onSubmit={handleEnroll} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="form-group">
            <label className="form-label">Student ID *</label>
            <input
              type="text"
              placeholder="e.g. student_alan"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              required
              className="form-input"
            />
            <p className="form-helper">Unique student identifier (alphanumeric, underscores, hyphens).</p>
          </div>

          <div className="form-group">
            <label className="form-label">Full Name *</label>
            <input
              type="text"
              placeholder="e.g. Alan Turing"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Email Address *</label>
            <input
              type="email"
              placeholder="e.g. alan@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="form-input"
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <button type="button" onClick={() => setIsEnrollOpen(false)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={isSubmitting} className="btn btn-primary">
              {isSubmitting ? 'Enrolling...' : 'Enroll Student'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

