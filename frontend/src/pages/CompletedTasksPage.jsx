import { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import ItemList from '../components/ItemList';
import { getItems, deleteItem, updateItem } from '../services/api';
import '../styles/Dashboard.css';

function CompletedTasksPage() {
  const [items, setItems] = useState([]);
  const [activeFilter, setActiveFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCompletedItems();
  }, []);

  const loadCompletedItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getItems();
      const allItems = response.items || [];
      const completedItems = allItems.filter(item => item.completed);
      setItems(completedItems);
    } catch (err) {
      setError('Unable to load completed items');
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async (id) => {
    try {
      await updateItem(id, { completed: false });
      setItems(items.filter(item => item.id !== id));
    } catch {
      setError('Failed to restore item');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this item? Deletion is permanent.')) return;
    try {
      await deleteItem(id);
      setItems(items.filter(item => item.id !== id));
    } catch {
      setError('Failed to delete item');
    }
  };

  const handleUpdate = async (id, updates) => {
    try {
      await updateItem(id, updates);
      loadCompletedItems();
    } catch {
      setError('Failed to update item');
    }
  };

  const filteredItems = items.filter(item => {
    if (activeFilter === 'all') return true;
    return item.type === activeFilter;
  });

  const filters = [
    { id: 'all', label: 'All' },
    { id: 'task', label: 'Tasks' },
    { id: 'note', label: 'Notes' },
    { id: 'reminder', label: 'Reminders' }
  ];

  return (
    <div className="dashboard-layout">
      <Sidebar activeView="completed" />

      <main className="dashboard-main">
        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)}>✖</button>
          </div>
        )}

        <div className="dashboard-header">
          <div>
            <h1>Completed Items</h1>
            <p className="view-subtitle">
              {filteredItems.length} completed {filteredItems.length === 1 ? 'item' : 'items'} shown
            </p>
          </div>
        </div>

        <div className="filter-tabs" style={{ marginBottom: '2rem' }}>
          {filters.map(filter => (
            <button
              key={filter.id}
              className={`filter-tab ${activeFilter === filter.id ? 'active' : ''}`}
              onClick={() => setActiveFilter(filter.id)}
            >
              {filter.label}
            </button>
          ))}
        </div>

        <section className="items-section">
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading completed items...</p>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon" style={{ fontSize: '4rem', opacity: 0.5 }}>✓</div>
              <h3>No completed items yet.</h3>
              <p>Items you mark as complete will show up here.</p>
            </div>
          ) : (
            <ItemList
              items={filteredItems}
              onToggle={handleRestore}
              onDelete={handleDelete}
              onUpdate={handleUpdate}
              loading={loading}
            />
          )}
        </section>
      </main>
    </div>
  );
}

export default CompletedTasksPage;
