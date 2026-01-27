import { Calendar, Clock, List } from 'lucide-react';
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
        <h2>AuraPlan</h2>
      </div>

      <nav className="sidebar-nav">
        {views.map((view) => {
          const Icon = view.icon;
          return (
            <button
              key={view.id}
              className={`nav-item ${activeView === view.id ? 'active' : ''}`}
              onClick={() => { navigate('/dashboard');
                navigate('/dashboard');
                onViewChange(view.id);
              }}
            >
              
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
          {syncLoading ? 'Syncing...' : 'Sync Data'}
        </button>
        <p className="sync-note">Calendar & Email sync coming soon!</p>
      </div>
      <div className="sidebar-footer">
         <button className="completed-btn" onClick={() => navigate('/completed')}>
              Completed Tasks
        </button>

        <button className="visual-day-btn" onClick={() => navigate('/day-view')}>
          Visual Day View
        </button>

        <button className="logout-btn" onClick={onLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}

export default Sidebar;