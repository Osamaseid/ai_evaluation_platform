import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Code2, Lock, User, GraduationCap, Shield } from 'lucide-react';

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
        maxWidth: '440px',
        width: '100%',
        margin: '3rem auto',
        padding: '2rem',
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-color)',
        boxShadow: 'var(--shadow-lg)',
      }}
    >
      <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
        <div
          style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, var(--primary), var(--ai-purple))',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            margin: '0 auto 1rem auto',
          }}
        >
          <Code2 size={28} />
        </div>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)' }}>
          Sign In to AutoGrade <span style={{ color: 'var(--primary)' }}>AI</span>
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
          Deterministic Evaluation & Pedagogical Code Review Platform
        </p>
      </div>

      {/* Quick Demo Access Bar */}
      <div
        style={{
          padding: '0.85rem',
          backgroundColor: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          marginBottom: '1.5rem',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
          1-Click Instant Demo Login:
        </span>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <button
            type="button"
            onClick={() => quickLogin('student')}
            disabled={isLoading}
            className="btn btn-outline btn-sm"
            style={{ fontSize: '0.775rem', gap: '0.3rem' }}
          >
            <GraduationCap size={14} /> Student Demo
          </button>
          <button
            type="button"
            onClick={() => quickLogin('instructor')}
            disabled={isLoading}
            className="btn btn-primary btn-sm"
            style={{ fontSize: '0.775rem', gap: '0.3rem' }}
          >
            <Shield size={14} /> Instructor Demo
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div className="form-group">
          <label className="form-label">Email or User ID</label>
          <div style={{ position: 'relative' }}>
            <User size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="student_ada or email"
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
            <Lock size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
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

        <button type="submit" disabled={isLoading} className="btn btn-primary" style={{ padding: '0.75rem', marginTop: '0.5rem' }}>
          {isLoading ? 'Signing In...' : 'Sign In'}
        </button>

        <p style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          Don't have an account yet?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontWeight: 600 }}
          >
            Create account
          </button>
        </p>
      </form>
    </div>
  );
};

