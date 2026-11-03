import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { Badge } from './Badge';
import {
  LogOut,
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
  const [isSwitching, setIsSwitching] = React.useState(false);

  const handleRoleSwitch = async (targetRole: 'student' | 'instructor') => {
    if (isSwitching) return;
    setIsSwitching(true);
    try {
      if (user?.role !== targetRole) {
        await quickLogin(targetRole);
      }
      onSwitchRoleView(targetRole);
    } finally {
      setIsSwitching(false);
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
          <img
            src="/brand/akiba-logo.png"
            alt="Akiba Technologies"
            className="brand-logo-img"
          />
          <span className="brand-divider" />
          <span className="brand-subtitle-badge">
            <Sparkles size={13} />
            CodeGrade AI
          </span>
        </a>
      </div>

      <div className="navbar-actions">
        {/* Role View Toggle Pill */}
        <div className="role-switcher-pill">
          <button
            onClick={() => handleRoleSwitch('student')}
            className={`role-switcher-btn ${
              activeRoleView === 'student' ? 'active' : ''
            }`}
          >
            <GraduationCap size={15} />
            Student Portal
          </button>
          <button
            onClick={() => handleRoleSwitch('instructor')}
            className={`role-switcher-btn ${
              activeRoleView === 'instructor' ? 'active' : ''
            }`}
          >
            <Shield size={15} />
            Instructor Portal
          </button>
        </div>

        {/* User Profile Info */}
        {user ? (
          <div className="user-profile-badge">
            <div className="user-avatar">
              {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div style={{ lineHeight: 1.2 }}>
              <span style={{ fontWeight: 700, display: 'block', fontSize: '0.85rem' }}>
                {user.name}
              </span>
              <span style={{ fontSize: '0.725rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                {user.user_id}
              </span>
            </div>
            <Badge
              variant={user.role === 'instructor' ? 'purple' : 'success'}
              className="role-badge"
            >
              {user.role}
            </Badge>
            <button
              onClick={() => logout()}
              className="btn btn-outline btn-sm"
              style={{ border: 'none', padding: '0.25rem', color: 'var(--text-muted)' }}
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
