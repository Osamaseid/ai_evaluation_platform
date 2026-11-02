import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types/api';
import { Code2, Lock, User, Mail, Shield, GraduationCap } from 'lucide-react';

interface RegisterFormProps {
  onSwitchToLogin: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSwitchToLogin }) => {
  const { register, isLoading } = useAuth();
  const [userId, setUserId] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'student' | 'instructor'>('student');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId.trim() || !name.trim() || !email.trim() || !password) return;
    try {
      await register({
        user_id: userId.trim(),
        name: name.trim(),
        email: email.trim(),
        password,
        role,
      });
      onSwitchToLogin();
    } catch {
      // Toast handles error display
    }
  };

  return (
    <div
      style={{
        maxWidth: '460px',
        width: '100%',
        margin: '2.5rem auto',
        padding: '2rem',
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-color)',
        boxShadow: 'var(--shadow-lg)',
      }}
    >
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <div
          style={{
            width: '44px',
            height: '44px',
            background: 'linear-gradient(135deg, var(--primary), var(--ai-purple))',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            margin: '0 auto 0.75rem auto',
          }}
        >
          <Code2 size={24} />
        </div>
        <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--text-main)' }}>
          Create an Account
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Join the Automated Programming Assignment Evaluation Platform
        </p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
        {/* Role Selector Pill */}
        <div className="form-group" style={{ marginBottom: '0.5rem' }}>
          <label className="form-label">I am registering as:</label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <button
              type="button"
              onClick={() => setRole('student')}
              className={`btn btn-sm ${role === 'student' ? 'btn-primary' : 'btn-outline'}`}
              style={{ gap: '0.35rem' }}
            >
              <GraduationCap size={16} /> Student
            </button>
            <button
              type="button"
              onClick={() => setRole('instructor')}
              className={`btn btn-sm ${role === 'instructor' ? 'btn-primary' : 'btn-outline'}`}
              style={{ gap: '0.35rem' }}
            >
              <Shield size={16} /> Instructor
            </button>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">User ID *</label>
          <div style={{ position: 'relative' }}>
            <User size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="e.g. ada_lovelace"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              required
              className="form-input"
              style={{ paddingLeft: '2.4rem' }}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Full Name *</label>
          <input
            type="text"
            placeholder="e.g. Ada Lovelace"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Email Address *</label>
          <div style={{ position: 'relative' }}>
            <Mail size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="email"
              placeholder="e.g. ada@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="form-input"
              style={{ paddingLeft: '2.4rem' }}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Password * (Min 6 characters)</label>
          <div style={{ position: 'relative' }}>
            <Lock size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="form-input"
              style={{ paddingLeft: '2.4rem' }}
            />
          </div>
        </div>

        <button type="submit" disabled={isLoading} className="btn btn-primary" style={{ padding: '0.75rem', marginTop: '0.5rem' }}>
          {isLoading ? 'Creating Account...' : 'Complete Registration'}
        </button>

        <p style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontWeight: 600 }}
          >
            Sign in
          </button>
        </p>
      </form>
    </div>
  );
};

