import { useState } from 'react';
import { Calendar, Clock, List, FileText, Bell, CheckSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { syncExternalData } from '../services/api';

function Sidebar({ activeView, onViewChange, onSync, syncLoading, onLogout }) {
  const navigate = useNavigate();
  const [localSyncLoading, setLocalSyncLoading] = useState(false);

  const views = [
    { id: 'today', label: 'Today', icon: Calendar, path: '/dashboard' },
    { id: 'tomorrow', label: 'Tomorrow', icon: Clock, path: '/dashboard' },
    { id: 'upcoming', label: 'Upcoming', icon: List, path: '/dashboard' },
    { id: 'notes', label: 'Notes', icon: FileText, path: '/notes' },
    { id: 'reminders', label: 'Reminders', icon: Bell, path: '/reminders' },
    { id: 'completed', label: 'Completed Tasks', icon: CheckSquare, path: '/completed' },
    { id: 'day-view', label: 'Visual Day View', icon: Calendar, path: '/day-view' },
  ];

  const handleNavClick = (view) => {
    if (view.path === '/dashboard') {
      navigate('/dashboard', { state: { view: view.id } });
      if (onViewChange) {
        onViewChange(view.id);
      }
    } else {
      navigate(view.path);
    }
  };

  const handleSyncClick = async () => {
    if (onSync) {
      onSync();
      return;
    }
    setLocalSyncLoading(true);
    try {
      const result = await syncExternalData();
      alert(` Synced ${result.synced.calendar} calendar events + ${result.synced.email} emails`);
      if (window.location.pathname === '/dashboard') {
        window.location.reload();
      }
    } catch (error) {
      alert(' Sync failed. Make sure backend is running.');
    } finally {
      setLocalSyncLoading(false);
    }
  };

  const handleLogoutClick = () => {
    if (onLogout) {
      onLogout();
      return;
    }
    localStorage.clear();
    navigate('/');
  };

  const isSyncing = syncLoading || localSyncLoading;

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>AuraPlan</h2>
      </div>

      <nav className="sidebar-nav">
        {views.map((view) => {
          const Icon = view.icon;
          const isActive = activeView === view.id;
          return (
            <button
              key={view.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => handleNavClick(view)}
            >
              <Icon size={18} />
              <span>{view.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Sync Section */}
      <div className="sync-section">
        <p className="sync-label">External Data Sync</p>
        <button
          className={`sync-btn ${isSyncing ? 'loading' : ''}`}
          onClick={handleSyncClick}
          disabled={isSyncing}
          title="Sync calendar and email"
        >
          {isSyncing ? 'Syncing...' : 'Sync Data'}
        </button>
        <p className="sync-note">Calendar & Email sync</p>
      </div>

      <div className="sidebar-footer">
        <button className="logout-btn" onClick={handleLogoutClick}>
          Logout
        </button>
      </div>
    </div>
  );
}

export default Sidebar;