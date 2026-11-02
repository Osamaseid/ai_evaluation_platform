import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { Badge } from './Badge';
import {
  Code2,
  LogOut,
  User,
  GraduationCap,
  Shield,
  Menu,
  Sparkles,
} from 'lucide-react';

interface NavbarProps {
  onToggleSidebar: () => void;
  activeRoleView: 'student' | 'instructor';
  onSwitchRoleView: (role: 'student' | 'instructor') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onToggleSidebar,
  activeRoleView,
  onSwitchRoleView,
}) => {
  const { user, logout, quickLogin } = useAuth();

  const handleRoleSwitch = async (targetRole: 'student' | 'instructor') => {
    onSwitchRoleView(targetRole);
    // If the active user isn't in that role, perform quickLogin
    if (user?.role !== targetRole) {
      await quickLogin(targetRole);
    }
  };

  return (
    <header className="navbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button
          className="btn btn-outline btn-sm"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation menu"
          style={{ display: 'flex', padding: '0.4rem' }}
        >
          <Menu size={18} />
        </button>

        <a href="#" className="navbar-brand">
          <div className="logo-icon">
            <Code2 size={20} />
          </div>
          <span>AutoGrade <span style={{ color: 'var(--primary)' }}>AI</span></span>
        </a>
      </div>

      <div className="navbar-actions">
        {/* Role View Toggle Pill */}
        <div
          style={{
            display: 'flex',
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '9999px',
            padding: '3px',
          }}
        >
          <button
            onClick={() => handleRoleSwitch('student')}
            className={`btn btn-sm ${
              activeRoleView === 'student' ? 'btn-primary' : 'btn-outline'
            }`}
            style={{
              border: 'none',
              borderRadius: '9999px',
              padding: '0.3rem 0.85rem',
              fontSize: '0.8rem',
            }}
          >
            <GraduationCap size={14} style={{ marginRight: '4px' }} />
            Student View
          </button>
          <button
            onClick={() => handleRoleSwitch('instructor')}
            className={`btn btn-sm ${
              activeRoleView === 'instructor' ? 'btn-primary' : 'btn-outline'
            }`}
            style={{
              border: 'none',
              borderRadius: '9999px',
              padding: '0.3rem 0.85rem',
              fontSize: '0.8rem',
            }}
          >
            <Shield size={14} style={{ marginRight: '4px' }} />
            Instructor View
          </button>
        </div>

        {/* User Profile Info */}
        {user ? (
          <div className="user-profile-badge">
            <div className="user-avatar">
              {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div style={{ lineHeight: 1.2 }}>
              <span style={{ fontWeight: 600, display: 'block' }}>{user.name}</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                {user.user_id}
              </span>
            </div>
            <Badge
              variant={user.role === 'instructor' ? 'purple' : 'info'}
              className="role-badge"
            >
              {user.role}
            </Badge>
            <button
              onClick={() => logout()}
              className="btn btn-outline btn-sm"
              style={{ border: 'none', padding: '0.2rem', color: 'var(--text-muted)' }}
              title="Sign Out"
              aria-label="Sign Out"
            >
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => quickLogin('student')}
              className="btn btn-outline btn-sm"
            >
              Student Demo
            </button>
            <button
              onClick={() => quickLogin('instructor')}
              className="btn btn-primary btn-sm"
            >
              Instructor Demo
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

