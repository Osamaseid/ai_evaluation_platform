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
  Sparkles,
  Award,
} from 'lucide-react';

export type StudentTab = 'overview' | 'assignments' | 'submit' | 'history';
export type InstructorTab =
  | 'overview'
  | 'students'
  | 'assignments'
  | 'rubrics'
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
    { id: 'submit', label: 'Submit Assignment', icon: <UploadCloud size={18} /> },
    { id: 'history', label: 'Submission History', icon: <History size={18} /> },
  ];

  const instructorNavItems = [
    { id: 'overview', label: 'Analytics Overview', icon: <LayoutDashboard size={18} /> },
    { id: 'students', label: 'Student Directory', icon: <Users size={18} /> },
    { id: 'assignments', label: 'Assignments & Tests', icon: <BookOpen size={18} /> },
    { id: 'rubrics', label: 'Grading Rubrics', icon: <Sliders size={18} /> },
    { id: 'monitoring', label: 'Submissions & Review', icon: <FileCheck2 size={18} /> },
    { id: 'analytics', label: 'Performance Stats', icon: <BarChart3 size={18} /> },
  ];

  const currentNavItems = roleView === 'student' ? studentNavItems : instructorNavItems;

  return (
    <>
      {isOpen && <div className="sidebar-overlay" onClick={onClose} />}

      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span
              style={{
                fontSize: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                fontWeight: 700,
                color: 'var(--text-dim)',
              }}
            >
              {roleView === 'student' ? 'Student Workspace' : 'Instructor Portal'}
            </span>
          </div>
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
          <div
            style={{
              padding: '0.75rem',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(139, 92, 246, 0.1)',
              border: '1px solid rgba(139, 92, 246, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.65rem',
            }}
          >
            <Sparkles size={20} color="#a855f7" />
            <div style={{ fontSize: '0.75rem' }}>
              <strong style={{ display: 'block', color: '#c084fc' }}>Gemini AI Review</strong>
              <span style={{ color: 'var(--text-muted)' }}>Deterministic + AI Feedback</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

