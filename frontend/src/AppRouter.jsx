import { useState } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/Dashboard.jsx';
import VisualDayPage from './pages/VisualDayPage';
import CompletedTasksPage from './pages/CompletedTasksPage';
import NotesPage from './pages/NotesPage';
import RemindersPage from './pages/RemindersPage';
import FloatingAuraButton from './components/FloatingAuraButton';
import AuraChatPanel from './components/AuraChatPanel';

function AppRouter() {
  const location = useLocation();
  const [isAuraOpen, setIsAuraOpen] = useState(false);

  // Check if current route is a post-login view
  const isPostLoginView = 
    location.pathname !== '/' && 
    location.pathname !== '/login';

  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/completed" element={<CompletedTasksPage />} />
        <Route path="/day-view" element={<VisualDayPage />} />
        <Route path="/notes" element={<NotesPage />} />
        <Route path="/reminders" element={<RemindersPage />} />
      </Routes>

      {isPostLoginView && (
        <>
          <FloatingAuraButton 
            isOpen={isAuraOpen} 
            onClick={() => setIsAuraOpen(!isAuraOpen)} 
          />
          <AuraChatPanel 
            isOpen={isAuraOpen} 
            onClose={() => setIsAuraOpen(false)} 
          />
        </>
      )}
    </>
  );
}

export default AppRouter;