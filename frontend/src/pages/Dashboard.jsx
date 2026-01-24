import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import InputBox from '../components/InputBox';
import ItemList from '../components/ItemList';
import { 
  getItemsGrouped, 
  syncExternalData, 
  parseInput, 
  deleteItem, 
  updateItem,
  searchItems 
} from '../services/api';
import { Search, X } from 'lucide-react';
import '../styles/Dashboard.css';

function DashboardPage() {
  const navigate = useNavigate();
  const [activeView, setActiveView] = useState('today');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchMode, setSearchMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    loadItems();
  }, [activeView, searchMode]);

  const loadItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getItemsGrouped(activeView);
      
      let allItems = [];
      if (activeView === 'today' || activeView === 'tomorrow' || activeView === 'upcoming') {
        allItems = response.items;
      } else {
        allItems = response.items[activeView] || [];
      }
      
      // Filter out completed items - they should disappear
      const activeItems = allItems.filter(item => !item.completed);
      setItems(activeItems);
    } catch (error) {
      setError('Failed to load items');
      console.error('Load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncLoading(true);
    try {
      const result = await syncExternalData();
      alert(`✅ Synced ${result.synced.calendar} calendar events + ${result.synced.email} emails`);
      loadItems();
    } catch (error) {
      alert('❌ Sync failed. Make sure backend is running.');
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
    if (!window.confirm('Delete this item?')) return;
    
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
      // Remove from view immediately when completed
      if (completed) {
        setItems(items.filter(item => item.id !== id));
      } else {
        // Reload items if uncompleted
        loadItems();
      }
    } catch (error) {
      setError('Failed to update item');
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await searchItems(searchQuery);
      // Filter out completed items from search results - they should disappear
      const activeResults = response.items.filter(item => !item.completed);
      setItems(activeResults);
      setSearchMode(true);
      setShowSearch(false);
    } catch (error) {
      setError('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleClearSearch = () => {
    setSearchMode(false);
    setSearchQuery('');
    loadItems();
  };

  const handleLogout = () => {
    // Clear all local storage data
    localStorage.clear();
    // Navigate to home
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
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)}>✖</button>
          </div>
        )}

        <div className="dashboard-header">
          <div>
            <h1>
              {searchMode ? '🔍 Search Results' :
               activeView === 'today' ? '📅 Today' : 
               activeView === 'tomorrow' ? '🌅 Tomorrow' : 
               '📋 Upcoming'}
            </h1>
            <p className="view-subtitle">
              {searchMode ? `Showing results for "${searchQuery}"` : 
               `${items.length} active ${items.length === 1 ? 'item' : 'items'}`}
            </p>
          </div>
        </div>

        {/* Search in corner */}
        <div className="search-corner">
          {searchMode ? (
            <button className="search-corner-btn clear" onClick={handleClearSearch} title="Clear Search">
              <X size={18} />
            </button>
          ) : (
            <>
              {showSearch ? (
                <form onSubmit={handleSearch} className="search-corner-form">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search..."
                    className="search-corner-input"
                    autoFocus
                  />
                  <button type="submit" className="search-corner-submit" disabled={!searchQuery.trim()}>
                    <Search size={16} />
                  </button>
                  <button type="button" className="search-corner-close" onClick={() => setShowSearch(false)}>
                    <X size={16} />
                  </button>
                </form>
              ) : (
                <button className="search-corner-btn" onClick={() => setShowSearch(true)} title="Search">
                  <Search size={18} />
                </button>
              )}
            </>
          )}
        </div>

        <section className="input-section">
          <h2>✨ Add New Item</h2>
          <InputBox onSubmit={handleAddInput} />
        </section>

        <section className="items-section">
          <ItemList
            items={items}
            onDelete={handleDelete}
            onToggle={handleToggle}
            loading={loading}
          />
        </section>
      </main>
    </div>
  );
}

export default DashboardPage;