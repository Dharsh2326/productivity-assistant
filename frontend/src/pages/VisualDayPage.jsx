import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Calendar } from 'lucide-react';
import { visualizeDay, getItemsGrouped } from '../services/api';
import ItemCard from '../components/ItemCard';
import '../styles/VisualDay.css';

function VisualDayPage() {
  const navigate = useNavigate();
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
        // Fix: Use correct URL format
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
    // Implement delete if needed
    console.log('Delete', id);
  };

  const handleToggle = async (id, completed) => {
    // Implement toggle if needed
    console.log('Toggle', id, completed);
  };

  return (
    <div className="visual-day-page">
      <header className="visual-day-header">
        <h1>📅 Visual Day View</h1>
        <p>Your tasks visualized beautifully</p>
      </header>

      <div className="visual-day-container">
        <div className="controls-card">
          <div className="control-group">
            <label>
              <Calendar size={18} />
              Select Date
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="date-input"
            />
          </div>

          <button
            className="btn-primary generate-btn"
            onClick={handleGenerate}
            disabled={loading}
          >
            {loading ? '⏳ Generating...' : 'Generate Daily Timeline'}
          </button>
        </div>

        {imageUrl && !showFallback && (
          <div className="image-container">
            <div className="image-wrapper">
              <img 
                src={imageUrl} 
                alt="Day View Visualization"
                onError={() => setShowFallback(true)}
              />
            </div>
          </div>
        )}

        {showFallback && todayItems.length > 0 && (
          <div className="fallback-container">
            <div className="fallback-header">
              <h2>📋 Today's Tasks</h2>
              <p>{todayItems.length} tasks scheduled</p>
            </div>
            <div className="fallback-items">
              {todayItems.map(item => (
                <ItemCard
                  key={item.id}
                  item={item}
                  onDelete={handleDelete}
                  onToggle={handleToggle}
                />
              ))}
            </div>
          </div>
        )}

        {!imageUrl && !loading && !showFallback && (
          <div className="empty-state">
            <div className="empty-icon">🎨</div>
            <h3>Generate Your Day View</h3>
            <p>Click "Generate" to create a visual timeline of your day</p>
          </div>
        )}

        {showFallback && todayItems.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>No Tasks Today</h3>
            <p>Add some tasks to see them visualized here</p>
          </div>
        )}
      </div>
      <button className="back-btn" onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={20} />
          Back to Dashboard
        </button>
    </div>
    
  );
}

export default VisualDayPage;