import React from 'react';
import { Inbox, AlertCircle, Loader2 } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
}) => {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">
        {icon || <Inbox size={48} strokeWidth={1.5} />}
      </div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-desc">{description}</p>
      {action && (
        <button onClick={action.onClick} className="btn btn-primary btn-sm">
          {action.label}
        </button>
      )}
    </div>
  );
};

export const LoadingSpinner: React.FC<{ message?: string }> = ({
  message = 'Loading platform data...',
}) => {
  return (
    <div className="loading-container">
      <div className="spinner" />
      <p style={{ fontSize: '0.875rem' }}>{message}</p>
    </div>
  );
};

export const ErrorAlert: React.FC<{
  title?: string;
  message: string;
  onRetry?: () => void;
}> = ({ title = 'Failed to load data', message, onRetry }) => {
  return (
    <div
      style={{
        padding: '1.25rem',
        borderRadius: 'var(--radius-md)',
        backgroundColor: 'var(--danger-bg)',
        border: '1px solid var(--danger-border)',
        color: '#fca5a5',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.85rem',
        marginBottom: '1.25rem',
      }}
      role="alert"
    >
      <AlertCircle size={20} color="var(--danger)" style={{ marginTop: '0.15rem', flexShrink: 0 }} />
      <div style={{ flex: 1 }}>
        <strong style={{ display: 'block', color: 'var(--text-main)', fontSize: '0.9rem', marginBottom: '0.2rem' }}>
          {title}
        </strong>
        <p style={{ fontSize: '0.825rem', opacity: 0.9 }}>{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="btn btn-outline btn-sm"
            style={{
              marginTop: '0.75rem',
              borderColor: 'var(--danger-border)',
              color: 'var(--text-main)',
            }}
          >
            Retry Action
          </button>
        )}
      </div>
    </div>
  );
};

