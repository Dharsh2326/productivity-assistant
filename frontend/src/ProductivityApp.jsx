import { useState, useEffect } from 'react';
import InputBox from './components/InputBox';
import ItemList from './components/ItemList';
import SearchBar from './components/SearchBar';
import FilterTabs from './components/FilterTabs';
import { parseInput, getItems, deleteItem, updateItem, searchItems, healthCheck } from './services/api';
import './ProductivityApp.css';

function ProductivityApp() {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState('all');
  const [searchMode, setSearchMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Check backend health on mount
  useEffect(() => {
    checkBackend();
  }, []);

  // Load items when filter changes
  useEffect(() => {
    if (!searchMode) {
      loadItems();
    }
  }, [filter, searchMode]);

  const checkBackend = async () => {
    try {
      await healthCheck();
      setBackendStatus('connected');
      loadItems();
    } catch (error) {
      setBackendStatus('disconnected');
      setError(' Backend offline. Start Flask: python -m backend.app');
    }
  };

  const loadItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const filterType = filter === 'all' ? null : filter;
      const response = await getItems(filterType);
      setItems(response.items || []);
    } catch (error) {
      setError(error.error || 'Failed to load items');
    } finally {
      setLoading(false);
    }
  };

  const handleAddInput = async (input) => {
    setError(null);
    try {
      const response = await parseInput(input);
      if (response.success) {
        await loadItems();
        return response;
      }
    } catch (error) {
      setError(error.error || 'Failed to parse input. Make sure Ollama is running.');
      throw error;
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this item?')) return;
    
    setError(null);
    try {
      await deleteItem(id);
      await loadItems();
    } catch (error) {
      setError(error.error || 'Failed to delete item');
    }
  };

  const handleToggle = async (id, completed) => {
    setError(null);
    try {
      await updateItem(id, { completed });
      await loadItems();
    } catch (error) {
      setError(error.error || 'Failed to update item');
    }
  };

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

  return (
    <div className="productivity-app">
      {/* Header */}
      <header className="pa-header">
        <div className="pa-header-content">
          <h1 className="pa-title"> Productivity Assistant</h1>
          <p className="pa-tagline">AI-powered task management with natural language</p>
          <div className={`pa-status ${backendStatus}`}>
            <span className="pa-status-dot"></span>
            <span className="pa-status-text">
              {backendStatus === 'connected' ? '✓ Backend Connected (Ollama)' : 
               backendStatus === 'disconnected' ? '✗ Backend Offline' : 
               ' Checking...'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pa-container">
        {/* Error Banner */}
        {error && (
          <div className="pa-error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="pa-error-close">✖</button>
          </div>
        )}

        {/* Input Section */}
        <section className="pa-section">
          <h2 className="pa-section-title"> Add New Item</h2>
          <InputBox onSubmit={handleAddInput} />
        </section>

        {/* Search Section */}
        <section className="pa-section">
          <h2 className="pa-section-title"> Semantic Search</h2>
          <SearchBar 
            onSearch={handleSearch} 
            onClear={handleClearSearch}
            isSearchMode={searchMode}
            query={searchQuery}
          />
        </section>

        {/* Items Section */}
        <section className="pa-section">
          <div className="pa-section-header">
            <h2 className="pa-section-title"> Your Items</h2>
            <span className="pa-item-count">{items.length} {items.length === 1 ? 'item' : 'items'}</span>
          </div>
          
          {!searchMode && (
            <FilterTabs activeFilter={filter} onFilterChange={setFilter} />
          )}
          
          <ItemList 
            items={items} 
            onDelete={handleDelete} 
            onToggle={handleToggle}
            loading={loading}
          />
        </section>
      </main>

      {/* Footer */}
      <footer className="pa-footer">
      <p>© 2026 AuraPlan. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default ProductivityApp;