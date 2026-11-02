import React, { useState } from 'react';
import { Assignment, EvaluationReport, Submission } from '../../types/api';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Modal } from '../common/Modal';
import { Badge } from '../common/Badge';
import {
  Github,
  Upload,
  FileCode,
  CheckCircle2,
  AlertCircle,
  Play,
  Loader2,
} from 'lucide-react';

interface SubmitAssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  assignment: Assignment | null;
  onSubmissionSuccess?: (submission: Submission, evaluation?: EvaluationReport) => void;
}

export const SubmitAssignmentModal: React.FC<SubmitAssignmentModalProps> = ({
  isOpen,
  onClose,
  assignment,
  onSubmissionSuccess,
}) => {
  const { user } = useAuth();
  const { success, error: showError, info } = useToast();

  const [activeTab, setActiveTab] = useState<'github' | 'upload'>('github');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [completedSubmission, setCompletedSubmission] = useState<Submission | null>(null);

  // GitHub Form State
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [commitSha, setCommitSha] = useState('');
  const [githubToken, setGithubToken] = useState('');

  // File Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const studentId = user?.user_id || 'student_ada';
  const taskId = assignment?.task_id || '';

  const handleGitHubSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) {
      showError('Validation Error', 'Please provide a valid GitHub repository URL.');
      return;
    }

    setIsSubmitting(true);
    try {
      const submission = await api.submitGitHub({
        student_id: studentId,
        task_id: taskId,
        repo_url: repoUrl.trim(),
        branch: branch.trim() || undefined,
        commit_sha: commitSha.trim() || undefined,
        github_token: githubToken.trim() || undefined,
      });

      setCompletedSubmission(submission);
      success('Submission Recorded', `Submission ID: ${submission.submission_id}`);
    } catch (err: any) {
      showError('Submission Failed', err.message || 'Could not record GitHub submission.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      showError('Validation Error', 'Please select a Python (.py) or ZIP (.zip) file.');
      return;
    }

    setIsSubmitting(true);
    try {
      const submission = await api.submitFileUpload(selectedFile, studentId, taskId);
      setCompletedSubmission(submission);
      success('File Uploaded Successfully', `Submission ID: ${submission.submission_id}`);
    } catch (err: any) {
      showError('Upload Failed', err.message || 'Could not upload source code file.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTriggerEvaluation = async () => {
    if (!completedSubmission) return;

    setIsEvaluating(true);
    info('Evaluation Started', 'Executing isolated tests and requesting Gemini AI review...');
    try {
      const report = await api.runEvaluation(completedSubmission.submission_id);
      success(
        'Evaluation Completed!',
        `Deterministic score: ${report.deterministic_score}/${report.max_score}`
      );
      if (onSubmissionSuccess) {
        onSubmissionSuccess(completedSubmission, report);
      }
      handleClose();
    } catch (err: any) {
      showError('Evaluation Failed', err.message || 'Error occurred during test execution.');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleClose = () => {
    setCompletedSubmission(null);
    setRepoUrl('');
    setSelectedFile(null);
    onClose();
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.py') || file.name.endsWith('.zip')) {
        setSelectedFile(file);
      } else {
        showError('Invalid File', 'Only .py and .zip archives are permitted.');
      }
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={`Submit Solution: ${assignment?.title || taskId}`}
      size="normal"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Step indicator or completed banner */}
        {completedSubmission ? (
          <div
            style={{
              padding: '1.5rem',
              backgroundColor: 'var(--lime-light)',
              border: '1px solid var(--lime-border)',
              borderRadius: 'var(--radius-md)',
              textAlign: 'center',
            }}
          >
            <CheckCircle2 size={40} color="var(--success)" style={{ margin: '0 auto 0.75rem auto' }} />
            <h3 style={{ fontSize: '1.15rem', color: 'var(--text-main)', marginBottom: '0.35rem' }}>
              Submission Accepted
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Reference:{' '}
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-main)' }}>
                {completedSubmission.submission_id}
              </span>
            </p>

            <button
              onClick={handleTriggerEvaluation}
              disabled={isEvaluating}
              className="btn btn-primary"
              style={{ width: '100%', gap: '0.5rem', padding: '0.75rem' }}
            >
              {isEvaluating ? (
                <>
                  <Loader2 size={18} className="spinner" /> Evaluating with Tests & Gemini AI...
                </>
              ) : (
                <>
                  <Play size={18} /> Launch Automated Evaluation Now
                </>
              )}
            </button>
          </div>
        ) : (
          <>
            <div className="tabs-nav" style={{ marginBottom: '1rem' }}>
              <button
                onClick={() => setActiveTab('github')}
                className={`tab-btn ${activeTab === 'github' ? 'active' : ''}`}
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <Github size={16} /> GitHub Repository URL
              </button>
              <button
                onClick={() => setActiveTab('upload')}
                className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <Upload size={16} /> Direct File Upload (.py / .zip)
              </button>
            </div>

            {/* GitHub Submission Tab */}
            {activeTab === 'github' && (
              <form onSubmit={handleGitHubSubmit}>
                <div className="form-group">
                  <label className="form-label">GitHub Repository URL *</label>
                  <input
                    type="url"
                    placeholder="https://github.com/student/data-structures-hw"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    required
                    className="form-input"
                  />
                  <p className="form-helper">
                    Public repository URL or private repo with Personal Access Token configured below.
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Branch</label>
                    <input
                      type="text"
                      placeholder="main"
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Commit SHA (Optional)</label>
                    <input
                      type="text"
                      placeholder="e.g. 7f3a9e..."
                      value={commitSha}
                      onChange={(e) => setCommitSha(e.target.value)}
                      className="form-input"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">GitHub Access Token (Optional for Private Repos)</label>
                  <input
                    type="password"
                    placeholder="ghp_..."
                    value={githubToken}
                    onChange={(e) => setGithubToken(e.target.value)}
                    className="form-input"
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.25rem' }}>
                  <button type="button" onClick={handleClose} className="btn btn-secondary">
                    Cancel
                  </button>
                  <button type="submit" disabled={isSubmitting} className="btn btn-primary">
                    {isSubmitting ? 'Validating Repository...' : 'Submit Repository'}
                  </button>
                </div>
              </form>
            )}

            {/* File Upload Tab */}
            {activeTab === 'upload' && (
              <form onSubmit={handleFileUploadSubmit}>
                <div
                  className={`dropzone ${isDragging ? 'active' : ''}`}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragging(true);
                  }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleFileDrop}
                  onClick={() => document.getElementById('file-input-element')?.click()}
                >
                  <input
                    id="file-input-element"
                    type="file"
                    accept=".py,.zip"
                    style={{ display: 'none' }}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSelectedFile(e.target.files[0]);
                      }
                    }}
                  />
                  <Upload size={36} className="dropzone-icon" />
                  <p style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.25rem' }}>
                    Click or drag & drop source code file here
                  </p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Accepted formats: Python script (<strong>.py</strong>) or Zip archive (<strong>.zip</strong>) up to 25MB
                  </p>
                </div>

                {selectedFile && (
                  <div
                    style={{
                      marginTop: '1rem',
                      padding: '0.85rem 1rem',
                      backgroundColor: 'var(--bg-secondary)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-md)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                      <FileCode size={20} color="var(--primary)" />
                      <div>
                        <strong style={{ fontSize: '0.875rem', display: 'block', color: 'var(--text-main)' }}>
                          {selectedFile.name}
                        </strong>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                          {(selectedFile.size / 1024).toFixed(1)} KB
                        </span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSelectedFile(null)}
                      className="btn btn-outline btn-sm"
                      style={{ border: 'none', color: 'var(--danger)' }}
                    >
                      Remove
                    </button>
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                  <button type="button" onClick={handleClose} className="btn btn-secondary">
                    Cancel
                  </button>
                  <button type="submit" disabled={!selectedFile || isSubmitting} className="btn btn-primary">
                    {isSubmitting ? 'Uploading & Scanning...' : 'Upload & Submit'}
                  </button>
                </div>
              </form>
            )}
          </>
        )}
      </div>
    </Modal>
  );
};

