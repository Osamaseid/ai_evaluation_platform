import React from 'react';
import {
  LayoutDashboard,
  BookOpen,
  UploadCloud,
  History,
  Users,
  Sliders,
  FileCheck2,
  BarChart3,
  UserCheck,
  ShieldCheck,
} from 'lucide-react';

export type StudentTab = 'overview' | 'assignments' | 'history' | 'profile';
export type InstructorTab =
  | 'overview'
  | 'students'
  | 'assignments'
  | 'monitoring'
  | 'analytics';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  roleView: 'student' | 'instructor';
  activeTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  roleView,
  activeTab,
  onSelectTab,
}) => {
  const studentNavItems = [
    { id: 'overview', label: 'Student Overview', icon: <LayoutDashboard size={18} /> },
    { id: 'assignments', label: 'Available Assignments', icon: <BookOpen size={18} /> },
    { id: 'history', label: 'Submission History', icon: <History size={18} /> },
    { id: 'profile', label: 'Student Profile', icon: <UserCheck size={18} /> },
  ];

  const instructorNavItems = [
    { id: 'overview', label: 'Analytics Overview', icon: <LayoutDashboard size={18} /> },
    { id: 'students', label: 'Student Directory', icon: <Users size={18} /> },
    { id: 'assignments', label: 'Assignments & Rubrics', icon: <BookOpen size={18} /> },
    { id: 'monitoring', label: 'Submissions & Review', icon: <FileCheck2 size={18} /> },
    { id: 'analytics', label: 'Performance Stats', icon: <BarChart3 size={18} /> },
  ];

  const currentNavItems = roleView === 'student' ? studentNavItems : instructorNavItems;

  return (
    <>
      {isOpen && <div className="sidebar-overlay" onClick={onClose} />}

      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-workspace-tag">
            {roleView === 'student' ? (
              <>
                <UserCheck size={14} /> Student Workspace
              </>
            ) : (
              <>
                <ShieldCheck size={14} /> Instructor Suite
              </>
            )}
          </span>
        </div>

        <nav className="sidebar-nav">
          {currentNavItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                onSelectTab(item.id);
                onClose();
              }}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-brand-card">
            <img
              src="/brand/akiba-icon.png"
              alt="Akiba Technologies"
              className="sidebar-brand-icon"
            />
            <div style={{ fontSize: '0.75rem', lineHeight: 1.3 }}>
              <strong style={{ display: 'block', color: 'var(--primary-dark)', fontWeight: 700 }}>
                Akiba Evaluator
              </strong>
              <span style={{ color: 'var(--text-muted)' }}>
                Deterministic + Gemini AI
              </span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
