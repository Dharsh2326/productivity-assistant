import { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import ItemList from '../components/ItemList';
import InputBox from '../components/InputBox';
import SearchBar from '../components/SearchBar';
import { getItems, deleteItem, updateItem, parseInput, searchItems } from '../services/api';
import '../styles/Dashboard.css';

function NotesPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchMode, setSearchMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (!searchMode) {
      loadNotes();
    }
  }, [searchMode]);

  const loadNotes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getItems('note');
      const notes = response.items || [];
      // Sort notes by newest first (created_at DESC)
      notes.sort((a, b) => {
        const dateA = a.created_at ? new Date(a.created_at) : new Date(0);
        const dateB = b.created_at ? new Date(b.created_at) : new Date(0);
        return dateB - dateA;
      });
      setItems(notes);
    } catch (err) {
      setError('Unable to load notes');
    } finally {
      setLoading(false);
    }
  };

  const handleAddInput = async (input) => {
    setError(null);
    try {
      const result = await parseInput(input);
      if (result.success) {
        loadNotes();
      } else {
        setError(result.error || 'Failed to add note.');
      }
    } catch (err) {
      setError(err.error || 'Failed to add note');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this item? Deletion is permanent.')) return;
    try {
      await deleteItem(id);
      loadNotes();
    } catch {
      setError('Failed to delete note');
    }
  };

  const handleUpdate = async (id, updates) => {
    try {
      await updateItem(id, updates);
      loadNotes();
    } catch {
      setError('Failed to update note');
    }
  };

  const handleSearch = async (query) => {
    setLoading(true);
    setError(null);
    setSearchQuery(query);
    try {
      const response = await searchItems(query);
      // Filter search results to only keep notes and sort them
      const notes = (response.items || []).filter(item => item.type === 'note');
      notes.sort((a, b) => {
        const dateA = a.created_at ? new Date(a.created_at) : new Date(0);
        const dateB = b.created_at ? new Date(b.created_at) : new Date(0);
        return dateB - dateA;
      });
      setItems(notes);
      setSearchMode(true);
    } catch (err) {
      setError(err.error || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleClearSearch = () => {
    setSearchMode(false);
    setSearchQuery('');
    loadNotes();
  };

  return (
    <div className="dashboard-layout">
      <Sidebar activeView="notes" />

      <main className="dashboard-main">
        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)}>✖</button>
          </div>
        )}

        <div className="dashboard-header">
          <div>
            <h1>Notes</h1>
            <p className="view-subtitle">
              {items.length} {items.length === 1 ? 'note' : 'notes'}
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

        <section className="input-section">
          <h2>Add New Note</h2>
          <InputBox onSubmit={handleAddInput} />
        </section>

        <section className="items-section">
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading notes...</p>
            </div>
          ) : items.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon" style={{ fontSize: '4rem', opacity: 0.5 }}>📝</div>
              <h3>No notes yet</h3>
              <p style={{ fontStyle: 'italic', color: '#64748b' }}>Example Note: "DBMS normalization has 3NF and BCNF"</p>
            </div>
          ) : (
            <ItemList
              items={items}
              onDelete={handleDelete}
              onToggle={null} /* Notes don't use toggle checkbox */
              onUpdate={handleUpdate}
              loading={loading}
            />
          )}
        </section>
      </main>
    </div>
  );
}

export default NotesPage;
