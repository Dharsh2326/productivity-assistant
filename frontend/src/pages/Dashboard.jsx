import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import InputBox from '../components/InputBox';
import ItemList from '../components/ItemList';
import SearchBar from '../components/SearchBar';
import { 
  getItemsGrouped, 
  getItems,
  syncExternalData, 
  parseInput, 
  deleteItem, 
  updateItem,
  searchItems
} from '../services/api';
import '../styles/Dashboard.css';

function DashboardPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeView, setActiveView] = useState('today');
  
  // Lists
  const [items, setItems] = useState([]);
  const [todayItems, setTodayItems] = useState([]);
  const [overdueItems, setOverdueItems] = useState([]);
  
  // Stats
  const [stats, setStats] = useState({
    todaysTasks: 0,
    activeReminders: 0,
    totalNotes: 0,
    completedToday: 0
  });

  const [loading, setLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchMode, setSearchMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Handle cross-page navigation view setting
  useEffect(() => {
    if (location.state?.view) {
      setActiveView(location.state.view);
      // Clear location state
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  useEffect(() => {
    if (!searchMode) {
      loadItems();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeView, searchMode]);

  const handleSearch = async (query) => {
    setLoading(true);
    setError(null);
    setSearchQuery(query);
    try {
      const response = await searchItems(query);
      setItems(response.items || []);
      setSearchMode(true);
    } catch (error) {
      setError(error.error || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleClearSearch = () => {
    setSearchMode(false);
    setSearchQuery('');
    loadItems();
  };

  const loadItems = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch both grouped and all items to calculate stats and list views in parallel
      const [groupedResponse, allItemsResponse] = await Promise.all([
        getItemsGrouped('all'),
        getItems()
      ]);
      
      const allItems = allItemsResponse.items || [];
      const todayStr = new Date().toISOString().split('T')[0];

      // 2. Compute Statistics locally
      const computedStats = {
        todaysTasks: allItems.filter(item => {
          const isTask = item.type === 'task';
          const isIncomplete = !item.completed;
          const itemDateStr = item.datetime ? item.datetime.split('T')[0] : '';
          return isTask && isIncomplete && itemDateStr === todayStr;
        }).length,
        
        activeReminders: allItems.filter(item => {
          return item.type === 'reminder' && !item.completed;
        }).length,
        
        totalNotes: allItems.filter(item => {
          return item.type === 'note';
        }).length,
        
        completedToday: allItems.filter(item => {
          const isCompleted = item.completed;
          const updatedAtStr = item.updated_at ? item.updated_at.split('T')[0] : '';
          return isCompleted && updatedAtStr === todayStr;
        }).length
      };
      
      setStats(computedStats);

      // 3. Load items depending on activeView
      if (activeView === 'today') {
        const overdue = (groupedResponse.items.overdue || []).filter(item => !item.completed);
        const today = (groupedResponse.items.today || []).filter(item => !item.completed);
        setOverdueItems(overdue);
        setTodayItems(today);
      } else if (activeView === 'tomorrow') {
        const tomorrow = (groupedResponse.items.tomorrow || []).filter(item => !item.completed);
        setItems(tomorrow);
      } else if (activeView === 'upcoming') {
        const upcoming = (groupedResponse.items.upcoming || []).filter(item => !item.completed);
        setItems(upcoming);
      }
    } catch (error) {
      setError('Error: Unable to load tasks');
      console.error('Load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncLoading(true);
    try {
      const result = await syncExternalData();
      alert(` Synced ${result.synced.calendar} calendar events + ${result.synced.email} emails`);
      loadItems();
    } catch (error) {
      alert(' Sync failed. Make sure backend is running.');
    } finally {
      setSyncLoading(false);
    }
  };

  const handleAddInput = async (input) => {
    setError(null);
    try {
      const result = await parseInput(input);
      if (result.success) {
        loadItems();
      } else {
        setError(result.error || 'Failed to add item. Check if Ollama is running.');
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.message || 'Failed to add item';
      setError(errorMsg);
      throw error;
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this item? Deletion is permanent.')) return;
    
    try {
      await deleteItem(id);
      loadItems();
    } catch (error) {
      setError('Failed to delete item');
    }
  };

  const handleToggle = async (id, completed) => {
    try {
      await updateItem(id, { completed });
      loadItems();
    } catch (error) {
      setError('Failed to update item');
    }
  };

  const handleUpdate = async (id, updates) => {
    try {
      await updateItem(id, updates);
      loadItems();
    } catch (error) {
      setError('Failed to update item');
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/');
  };

  return (
    <div className="dashboard-layout">
      <Sidebar
        activeView={activeView}
        onViewChange={setActiveView}
        onSync={handleSync}
        syncLoading={syncLoading}
        onLogout={handleLogout}
      />

      <main className="dashboard-main">
        {error && (
          <div className="error-banner">
            <span> {error}</span>
            <button onClick={() => setError(null)}>✖</button>
          </div>
        )}

        <div className="dashboard-header">
          <div>
            <h1>
              {activeView === 'today' ? ' Today' : 
               activeView === 'tomorrow' ? ' Tomorrow' : 
               ' Upcoming'}
            </h1>
            <p className="view-subtitle">
              {activeView === 'today' ? (todayItems.length + overdueItems.length) : items.length} active {items.length === 1 ? 'item' : 'items'}
            </p>
          </div>
          <div className="header-search">
            <SearchBar 
              onSearch={handleSearch} 
              onClear={handleClearSearch}
              isSearchMode={searchMode}
              query={searchQuery}
            />
          </div>
        </div>

        {/* Lightweight Stats Header */}
        <section className="stats-header">
          <div className="stats-card">
            <div className="stats-icon tasks">📋</div>
            <div className="stats-info">
              <span className="stats-value">{stats.todaysTasks}</span>
              <span className="stats-label">Today's Tasks</span>
            </div>
          </div>
          <div className="stats-card">
            <div className="stats-icon reminders">⏰</div>
            <div className="stats-info">
              <span className="stats-value">{stats.activeReminders}</span>
              <span className="stats-label">Active Reminders</span>
            </div>
          </div>
          <div className="stats-card">
            <div className="stats-icon notes">📝</div>
            <div className="stats-info">
              <span className="stats-value">{stats.totalNotes}</span>
              <span className="stats-label">Total Notes</span>
            </div>
          </div>
          <div className="stats-card">
            <div className="stats-icon completed">✓</div>
            <div className="stats-info">
              <span className="stats-value">{stats.completedToday}</span>
              <span className="stats-label">Completed Today</span>
            </div>
          </div>
        </section>

        <section className="input-section">
          <h2> Add New Task</h2>
          <InputBox onSubmit={handleAddInput} />
        </section>

        {searchMode ? (
          <section className="items-section">
            <h2 className="section-subtitle">🔍 Search Results</h2>
            <ItemList
              items={items}
              onDelete={handleDelete}
              onToggle={handleToggle}
              onUpdate={handleUpdate}
              loading={loading}
            />
          </section>
        ) : activeView === 'today' ? (
          <>
            {overdueItems.length > 0 && (
              <section className="items-section">
                <h2 className="section-subtitle">⚠️ Overdue</h2>
                <ItemList
                  items={overdueItems}
                  onDelete={handleDelete}
                  onToggle={handleToggle}
                  onUpdate={handleUpdate}
                  loading={loading}
                />
              </section>
            )}

            <section className="items-section">
              <h2 className="section-subtitle">📅 Today</h2>
              <ItemList
                items={todayItems}
                onDelete={handleDelete}
                onToggle={handleToggle}
                onUpdate={handleUpdate}
                loading={loading}
              />
            </section>
          </>
        ) : (
          <section className="items-section">
            <ItemList
              items={items}
              onDelete={handleDelete}
              onToggle={handleToggle}
              onUpdate={handleUpdate}
              loading={loading}
            />
          </section>
        )}
      </main>
    </div>
  );
}

export default DashboardPage;