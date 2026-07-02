import { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import ItemList from '../components/ItemList';
import InputBox from '../components/InputBox';
import SearchBar from '../components/SearchBar';
import { getItems, deleteItem, updateItem, parseInput, searchItems } from '../services/api';
import '../styles/Dashboard.css';

function RemindersPage() {
  const [items, setItems] = useState([]);
  const [dueTodayReminders, setDueTodayReminders] = useState([]);
  const [upcomingReminders, setUpcomingReminders] = useState([]);
  const [completedReminders, setCompletedReminders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchMode, setSearchMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (!searchMode) {
      loadReminders();
    }
  }, [searchMode]);

  const loadReminders = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getItems('reminder');
      const reminders = response.items || [];
      
      const todayStr = new Date().toISOString().split('T')[0];
      
      const dueToday = [];
      const upcoming = [];
      const completed = [];

      reminders.forEach(item => {
        if (item.completed) {
          completed.push(item);
        } else if (!item.datetime) {
          upcoming.push(item);
        } else {
          try {
            const itemDateStr = item.datetime.split('T')[0];
            if (itemDateStr <= todayStr) {
              dueToday.push(item);
            } else {
              upcoming.push(item);
            }
          } catch {
            upcoming.push(item);
          }
        }
      });

      setDueTodayReminders(dueToday);
      setUpcomingReminders(upcoming);
      setCompletedReminders(completed);
      setItems(reminders);
    } catch (err) {
      setError('Unable to load reminders');
    } finally {
      setLoading(false);
    }
  };

  const handleAddInput = async (input) => {
    setError(null);
    try {
      const result = await parseInput(input);
      if (result.success) {
        loadReminders();
      } else {
        setError(result.error || 'Failed to add reminder.');
      }
    } catch (err) {
      setError(err.error || 'Failed to add reminder');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this item? Deletion is permanent.')) return;
    try {
      await deleteItem(id);
      loadReminders();
    } catch {
      setError('Failed to delete reminder');
    }
  };

  const handleToggle = async (id, completed) => {
    try {
      await updateItem(id, { completed });
      loadReminders();
    } catch {
      setError('Failed to update reminder');
    }
  };

  const handleUpdate = async (id, updates) => {
    try {
      await updateItem(id, updates);
      loadReminders();
    } catch {
      setError('Failed to update reminder');
    }
  };

  const handleSearch = async (query) => {
    setLoading(true);
    setError(null);
    setSearchQuery(query);
    try {
      const response = await searchItems(query);
      const reminders = (response.items || []).filter(item => item.type === 'reminder');
      setItems(reminders);
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
    loadReminders();
  };

  const totalActiveCount = dueTodayReminders.length + upcomingReminders.length;

  return (
    <div className="dashboard-layout">
      <Sidebar activeView="reminders" />

      <main className="dashboard-main">
        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)}>✖</button>
          </div>
        )}

        <div className="dashboard-header">
          <div>
            <h1>Reminders</h1>
            <p className="view-subtitle">
              {totalActiveCount} active {totalActiveCount === 1 ? 'reminder' : 'reminders'}
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
          <h2>Add New Reminder</h2>
          <InputBox onSubmit={handleAddInput} />
        </section>

        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading reminders...</p>
          </div>
        ) : searchMode ? (
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
        ) : items.length === 0 ? (
          <section className="items-section">
            <div className="empty-state">
              <div className="empty-icon" style={{ fontSize: '4rem', opacity: 0.5 }}>⏰</div>
              <h3>No reminders yet</h3>
              <p style={{ fontStyle: 'italic', color: '#64748b' }}>Example Reminder: "Remind me to call mom tomorrow at 5 PM"</p>
            </div>
          </section>
        ) : (
          <>
            {dueTodayReminders.length > 0 && (
              <section className="items-section">
                <h2 className="section-subtitle">⏰ Due Today</h2>
                <ItemList
                  items={dueTodayReminders}
                  onDelete={handleDelete}
                  onToggle={handleToggle}
                  onUpdate={handleUpdate}
                  loading={loading}
                />
              </section>
            )}

            {upcomingReminders.length > 0 && (
              <section className="items-section">
                <h2 className="section-subtitle">📅 Upcoming</h2>
                <ItemList
                  items={upcomingReminders}
                  onDelete={handleDelete}
                  onToggle={handleToggle}
                  onUpdate={handleUpdate}
                  loading={loading}
                />
              </section>
            )}

            {completedReminders.length > 0 && (
              <section className="items-section">
                <h2 className="section-subtitle">✓ Completed</h2>
                <ItemList
                  items={completedReminders}
                  onDelete={handleDelete}
                  onToggle={handleToggle}
                  onUpdate={handleUpdate}
                  loading={loading}
                />
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default RemindersPage;
