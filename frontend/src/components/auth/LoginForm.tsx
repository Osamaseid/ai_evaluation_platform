import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Lock, User, GraduationCap, Shield } from 'lucide-react';

interface LoginFormProps {
  onSwitchToRegister: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSwitchToRegister }) => {
  const { login, quickLogin, isLoading } = useAuth();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim() || !password) return;
    try {
      await login(identifier.trim(), password);
    } catch {
      // Toast handles error display
    }
  };

  return (
    <div
      style={{
        maxWidth: '450px',
        width: '100%',
        margin: '2rem auto',
        padding: '2.25rem',
        backgroundColor: '#ffffff',
        borderRadius: 'var(--radius-xl)',
        border: '1px solid var(--border-color)',
        boxShadow: 'var(--shadow-card)',
      }}
    >
      <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
        <img
          src="/brand/akiba-logo.png"
          alt="Akiba Technologies"
          style={{ height: '42px', width: 'auto', objectFit: 'contain', margin: '0 auto 1.25rem auto' }}
        />
        <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
          Sign In to CodeGrade AI
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
          Automated Code Evaluation & Gemini AI Pedagogical Review
        </p>
      </div>

      {/* Quick Demo Access Bar */}
      <div
        style={{
          padding: '1rem',
          backgroundColor: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          marginBottom: '1.5rem',
        }}
      >
        <span
          style={{
            fontSize: '0.725rem',
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            display: 'block',
            marginBottom: '0.6rem',
            fontWeight: 700,
            letterSpacing: '0.05em',
          }}
        >
          1-Click Instant Demo Login:
        </span>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <button
            type="button"
            onClick={() => quickLogin('student')}
            disabled={isLoading}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: '0.775rem', gap: '0.35rem' }}
          >
            <GraduationCap size={15} color="var(--primary)" /> Student Demo
          </button>
          <button
            type="button"
            onClick={() => quickLogin('instructor')}
            disabled={isLoading}
            className="btn btn-primary btn-sm"
            style={{ fontSize: '0.775rem', gap: '0.35rem' }}
          >
            <Shield size={15} /> Instructor Demo
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div className="form-group">
          <label className="form-label">Email or User ID</label>
          <div style={{ position: 'relative' }}>
            <User
              size={16}
              color="var(--text-dim)"
              style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="text"
              placeholder="e.g. student_ada or email"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
              className="form-input"
              style={{ paddingLeft: '2.4rem' }}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Password</label>
          <div style={{ position: 'relative' }}>
            <Lock
              size={16}
              color="var(--text-dim)"
              style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="form-input"
              style={{ paddingLeft: '2.4rem' }}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="btn btn-primary"
          style={{ padding: '0.75rem', marginTop: '0.25rem' }}
        >
          {isLoading ? 'Signing In...' : 'Sign In'}
        </button>

        <p style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          Don't have an account yet?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--primary)',
              cursor: 'pointer',
              fontWeight: 700,
            }}
          >
            Create account
          </button>
        </p>
      </form>
    </div>
  );
};
