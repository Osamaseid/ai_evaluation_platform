import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { Navbar } from './components/common/Navbar';
import { Sidebar } from './components/common/Sidebar';
import { LoginForm } from './components/auth/LoginForm';
import { RegisterForm } from './components/auth/RegisterForm';
import { StudentOverview } from './components/student/StudentOverview';
import { AssignmentList } from './components/student/AssignmentList';
import { SubmissionHistory } from './components/student/SubmissionHistory';
import { SubmitAssignmentModal } from './components/student/SubmitAssignmentModal';
import { InstructorOverview } from './components/instructor/InstructorOverview';
import { StudentManagement } from './components/instructor/StudentManagement';
import { AssignmentManagement } from './components/instructor/AssignmentManagement';
import { SubmissionMonitoring } from './components/instructor/SubmissionMonitoring';
import { ClassPerformanceStats } from './components/instructor/ClassPerformanceStats';

export const App: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();

  // Active view role ('student' or 'instructor')
  const [roleView, setRoleView] = useState<'student' | 'instructor'>(() => {
    return user?.role === 'instructor' ? 'instructor' : 'student';
  });

  // Active tab within the current role view
  const [activeTab, setActiveTab] = useState<string>('overview');

  // Mobile sidebar drawer
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Auth toggle
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  // Direct submit modal triggered from nav
  const [isDirectSubmitOpen, setIsDirectSubmitOpen] = useState(false);

  // If user role changes, ensure roleView syncs if appropriate
  React.useEffect(() => {
    if (user?.role === 'instructor') {
      setRoleView('instructor');
    } else if (user?.role === 'student') {
      setRoleView('student');
    }
  }, [user]);

  // Tab selection handler
  const handleSelectTab = (tab: string) => {
    if (tab === 'submit') {
      setIsDirectSubmitOpen(true);
      return;
    }
    setActiveTab(tab);
  };

  const handleSwitchRoleView = (targetRole: 'student' | 'instructor') => {
    setRoleView(targetRole);
    setActiveTab('overview');
  };

  // Unauthenticated screen
  if (!isAuthenticated && !isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <header className="navbar" style={{ justifyContent: 'center' }}>
          <div className="navbar-brand">
            <div className="logo-icon">AG</div>
            <span>AutoGrade <span style={{ color: 'var(--primary)' }}>AI</span></span>
          </div>
        </header>
        <main className="content-area" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {authMode === 'login' ? (
            <LoginForm onSwitchToRegister={() => setAuthMode('register')} />
          ) : (
            <RegisterForm onSwitchToLogin={() => setAuthMode('login')} />
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        roleView={roleView}
        activeTab={activeTab}
        onSelectTab={handleSelectTab}
      />

      <div className="main-wrapper">
        {/* Sticky Header */}
        <Navbar
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          activeRoleView={roleView}
          onSwitchRoleView={handleSwitchRoleView}
        />

        {/* Dynamic Workspace Content */}
        <main className="content-area">
          {roleView === 'student' ? (
            <>
              {activeTab === 'overview' && <StudentOverview onNavigateTab={handleSelectTab} />}
              {activeTab === 'assignments' && <AssignmentList />}
              {activeTab === 'history' && <SubmissionHistory />}
            </>
          ) : (
            <>
              {activeTab === 'overview' && <InstructorOverview onNavigateTab={handleSelectTab} />}
              {activeTab === 'students' && <StudentManagement />}
              {activeTab === 'assignments' && <AssignmentManagement />}
              {activeTab === 'rubrics' && <AssignmentManagement />}
              {activeTab === 'monitoring' && <SubmissionMonitoring />}
              {activeTab === 'analytics' && <ClassPerformanceStats />}
            </>
          )}
        </main>
      </div>

      {/* Direct Submit Modal */}
      <SubmitAssignmentModal
        isOpen={isDirectSubmitOpen}
        onClose={() => setIsDirectSubmitOpen(false)}
        assignment={null}
        onSubmissionSuccess={() => {
          setActiveTab('history');
        }}
      />
    </div>
  );
};

