import { Calendar, Clock, List, Image, RefreshCw, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

function Sidebar({ activeView, onViewChange, onSync, syncLoading, onLogout }) {
  const navigate = useNavigate();

  const views = [
    { id: 'today', label: 'Today', icon: Calendar },
    { id: 'tomorrow', label: 'Tomorrow', icon: Clock },
    { id: 'upcoming', label: 'Upcoming', icon: List },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>🚀 TaskMaster Pro</h2>
      </div>

      <nav className="sidebar-nav">
        {views.map((view) => {
          const Icon = view.icon;
          return (
            <button
              key={view.id}
              className={`nav-item ${activeView === view.id ? 'active' : ''}`}
              onClick={() => onViewChange(view.id)}
            >
              <Icon size={20} />
              <span>{view.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Sync Button - Moved here under Upcoming */}
      <div className="sync-section">
        <p className="sync-label">External Data Sync</p>
        <button
          className={`sync-btn ${syncLoading ? 'loading' : ''}`}
          onClick={onSync}
          disabled={syncLoading}
          title="Sync calendar and email (Feature in development)"
        >
          <RefreshCw size={18} className={syncLoading ? 'spinning' : ''} />
          {syncLoading ? 'Syncing...' : 'Sync Data'}
        </button>
        <p className="sync-note">Calendar & Email sync coming soon!</p>
      </div>

      <div className="sidebar-footer">
        <button className="visual-day-btn" onClick={() => navigate('/day-view')}>
          <Image size={18} />
          Visual Day View
        </button>

        <button className="logout-btn" onClick={onLogout}>
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </div>
  );
}

export default Sidebar;