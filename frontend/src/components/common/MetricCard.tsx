import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  subtitle?: string;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  icon,
  subtitle,
  trend,
}) => {
  return (
    <div className="metric-card">
      <div className="metric-info">
        <p className="metric-label">{label}</p>
        <p className="metric-value">{value}</p>
        {subtitle && (
          <p style={{ fontSize: '0.775rem', color: 'var(--text-dim)', marginTop: '0.35rem' }}>
            {subtitle}
          </p>
        )}
        {trend && (
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              color: trend.isPositive ? 'var(--success)' : 'var(--danger)',
              display: 'inline-block',
              marginTop: '0.3rem',
            }}
          >
            {trend.value}
          </span>
        )}
      </div>
      <div className="metric-icon-box">{icon}</div>
    </div>
  );
};

