import { Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/Dashboard.jsx';
import VisualDayPage from './pages/VisualDayPage';
import CompletedTasksPage from './pages/CompletedTasksPage';

function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/completed" element={<CompletedTasksPage />} />
      <Route path="/day-view" element={<VisualDayPage />} />
    </Routes>
  );
}

export default AppRouter;