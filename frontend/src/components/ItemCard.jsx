import { useState } from 'react';

function ItemCard({ item, onDelete, onToggle }) {
  const [showDetails, setShowDetails] = useState(false);

  const formatDate = (dateString) => {
    if (!dateString) return null;
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric',
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return dateString;
    }
  };

  const getTypeIcon = (type) => {
    switch(type) {
      case 'task': return '✅';
      case 'note': return '📝';
      case 'reminder': return '⏰';
      default: return '📌';
    }
  };

  const getPriorityColor = (priority) => {
    switch(priority) {
      case 'high': return '#ff4757';
      case 'medium': return '#ffa502';
      case 'low': return '#1e90ff';
      default: return '#95a5a6';
    }
  };

  return (
    <div className={`item-card ${item.type} ${item.completed ? 'completed' : ''}`}>
      <div className="item-header">
        <input
          type="checkbox"
          checked={item.completed || false}
          onChange={() => onToggle(item.id, !item.completed)}
          className="checkbox"
        />
        <span className="type-icon">{getTypeIcon(item.type)}</span>
        <h3 className="item-title">{item.title}</h3>
        <span 
          className="priority-badge" 
          style={{ backgroundColor: getPriorityColor(item.priority) }}
        >
          {item.priority || 'medium'}
        </span>
      </div>

      {item.description && (
        <p className="item-description">{item.description}</p>
      )}

      {item.datetime && (
        <div className="item-datetime">
          📅 {formatDate(item.datetime)}
        </div>
      )}

      {item.tags && item.tags.length > 0 && (
        <div className="item-tags">
          {item.tags.split(',').filter(t => t.trim()).map((tag, i) => (
            <span key={i} className="tag">#{tag.trim()}</span>
          ))}
        </div>
      )}

      <div className="item-footer">
        <div className="item-meta">
          <span className="type-label">{item.type}</span>
          {item.relevance_score && (
            <span className="relevance-score">
              Match: {(item.relevance_score * 100).toFixed(0)}%
            </span>
          )}
        </div>
        <button 
          onClick={() => onDelete(item.id)} 
          className="delete-btn"
        >
           Delete
        </button>
      </div>
    </div>
  );
}

export default ItemCard;