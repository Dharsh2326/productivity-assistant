import { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import { visualizeDay, getItemsGrouped, deleteItem, updateItem } from '../services/api';
import ItemCard from '../components/ItemCard';
import '../styles/VisualDay.css';
import '../styles/Dashboard.css';

function VisualDayPage() {
  const today = new Date().toISOString().split('T')[0];
  const [date, setDate] = useState(today);
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [todayItems, setTodayItems] = useState([]);
  const [showFallback, setShowFallback] = useState(false);

  useEffect(() => {
    loadTodayItems();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadTodayItems = async () => {
    try {
      const response = await getItemsGrouped('today');
      setTodayItems(response.items || []);
    } catch (error) {
      console.error('Error loading items:', error);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    setImageUrl(null);
    setShowFallback(false);
    
    try {
      const result = await visualizeDay(date);
      if (result.success && result.image_url) {
        const fullImageUrl = result.image_url.startsWith('http') 
          ? result.image_url 
          : `http://localhost:5000${result.image_url}`;
        setImageUrl(fullImageUrl);
      } else {
        setShowFallback(true);
      }
    } catch (error) {
      console.error('Visualization error:', error);
      setShowFallback(true);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this item? Deletion is permanent.')) return;
    try {
      await deleteItem(id);
      loadTodayItems();
    } catch (error) {
      console.error('Error deleting:', error);
    }
  };

  const handleToggle = async (id, completed) => {
    try {
      await updateItem(id, { completed });
      loadTodayItems();
    } catch (error) {
      console.error('Error updating:', error);
    }
  };

  const handleUpdate = async (id, updates) => {
    try {
      await updateItem(id, updates);
      loadTodayItems();
    } catch (error) {
      console.error('Error updating:', error);
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar activeView="day-view" />

      <main className="dashboard-main">
        <header className="visual-day-header" style={{ marginBottom: '2rem' }}>
          <h1>Visual Day View</h1>
          <p className="view-subtitle">Your tasks visualized beautifully</p>
        </header>

        <div className="visual-day-container">
          <div className="controls-card" style={{ background: 'white', border: '1px solid #e5e7eb', padding: '1.5rem', borderRadius: '16px', marginBottom: '2rem' }}>
            <div className="control-group" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
              <label style={{ fontWeight: '600', color: '#374151', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Calendar size={18} />
                Select Date
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="date-input"
                style={{ padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '1rem' }}
              />
            </div>

            <button
              className="btn-primary generate-btn"
              onClick={handleGenerate}
              disabled={loading}
              style={{ width: '100%' }}
            >
              {loading ? 'Generating...' : 'Generate Daily Timeline'}
            </button>
          </div>

          {imageUrl && !showFallback && (
            <div className="image-container" style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '16px', padding: '1.5rem', display: 'flex', justifyContent: 'center' }}>
              <div className="image-wrapper" style={{ maxWidth: '100%', overflow: 'hidden' }}>
                <img 
                  src={imageUrl} 
                  alt="Day View Visualization"
                  style={{ maxWidth: '100%', height: 'auto', borderRadius: '8px' }}
                  onError={() => setShowFallback(true)}
                />
              </div>
            </div>
          )}

          {showFallback && todayItems.length > 0 && (
            <div className="fallback-container" style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '16px', padding: '1.5rem' }}>
              <div className="fallback-header" style={{ marginBottom: '1.5rem' }}>
                <h2>Today's Tasks</h2>
                <p className="view-subtitle">{todayItems.length} tasks scheduled</p>
              </div>
              <div className="fallback-items" style={{ display: 'grid', gap: '1rem' }}>
                {todayItems.map(item => (
                  <ItemCard
                    key={item.id}
                    item={item}
                    onDelete={handleDelete}
                    onToggle={handleToggle}
                    onUpdate={handleUpdate}
                  />
                ))}
              </div>
            </div>
          )}

          {!imageUrl && !loading && !showFallback && (
            <div className="empty-state" style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '16px', padding: '3rem 2rem', textAlign: 'center' }}>
              <h3 style={{ fontSize: '1.25rem', color: '#374151', marginBottom: '0.5rem' }}>Generate Your Day View</h3>
              <p style={{ color: '#6b7280' }}>Click "Generate" to create a visual timeline of your day</p>
            </div>
          )}

          {showFallback && todayItems.length === 0 && (
            <div className="empty-state" style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '16px', padding: '3rem 2rem', textAlign: 'center' }}>
              <h3 style={{ fontSize: '1.25rem', color: '#374151', marginBottom: '0.5rem' }}>No Tasks Today</h3>
              <p style={{ color: '#6b7280' }}>Add some tasks to see them visualized here</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default VisualDayPage;