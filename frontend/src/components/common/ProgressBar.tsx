import React from 'react';

interface ProgressBarProps {
  percentage: number;
  maxScore?: number;
  earnedPoints?: number;
  variant?: 'success' | 'warning' | 'danger' | 'auto';
  showLabel?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  percentage,
  maxScore,
  earnedPoints,
  variant = 'auto',
  showLabel = true,
}) => {
  const clamped = Math.max(0, Math.min(100, Math.round(percentage)));

  let fillClass = 'progress-fill-success';
  if (variant === 'auto') {
    if (clamped < 50) {
      fillClass = 'progress-fill-danger';
    } else if (clamped < 75) {
      fillClass = 'progress-fill-warning';
    } else {
      fillClass = 'progress-fill-success';
    }
  } else {
    fillClass = `progress-fill-${variant}`;
  }

  return (
    <div className="progress-component">
      {showLabel && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.8rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>Score</span>
          <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
            {earnedPoints !== undefined && maxScore !== undefined
              ? `${earnedPoints}/${maxScore} (${clamped}%)`
              : `${clamped}%`}
          </span>
        </div>
      )}
      <div
        className="progress-bar-container"
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className={`progress-bar-fill ${fillClass}`} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
};

