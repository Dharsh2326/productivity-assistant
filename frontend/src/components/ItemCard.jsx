import { useState, useEffect } from 'react';

function ItemCard({ item, onDelete, onToggle, onUpdate }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(item.title);
  const [editDescription, setEditDescription] = useState(item.description || '');
  const [editDatetime, setEditDatetime] = useState('');
  const [editPriority, setEditPriority] = useState(item.priority || 'medium');
  const [editTags, setEditTags] = useState(item.tags || '');

  const formatToInputDateTime = (isoString) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      const pad = (n) => n.toString().padStart(2, '0');
      const yyyy = date.getFullYear();
      const mm = pad(date.getMonth() + 1);
      const dd = pad(date.getDate());
      const hh = pad(date.getHours());
      const min = pad(date.getMinutes());
      return `${yyyy}-${mm}-${dd}T${hh}:${min}`;
    } catch {
      return '';
    }
  };

  useEffect(() => {
    setEditTitle(item.title);
    setEditDescription(item.description || '');
    setEditDatetime(formatToInputDateTime(item.datetime));
    setEditPriority(item.priority || 'medium');
    setEditTags(item.tags || '');
  }, [item]);

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

  const formatCreatedDate = (dateString) => {
    if (!dateString) return null;
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const getPriorityColor = (priority) => {
    switch(priority) {
      case 'high': return '#fb5967';
      case 'medium': return '#e6a428';
      case 'low': return '#448fda';
      default: return '#95a5a6';
    }
  };

  const handleSave = () => {
    if (!editTitle.trim()) return;

    let isoDatetime = null;
    if (editDatetime) {
      try {
        const dt = new Date(editDatetime);
        if (!isNaN(dt.getTime())) {
          isoDatetime = dt.toISOString();
        }
      } catch {
        isoDatetime = editDatetime;
      }
    }

    if (onUpdate) {
      onUpdate(item.id, {
        title: editTitle,
        description: editDescription,
        datetime: isoDatetime,
        priority: editPriority,
        tags: editTags.split(',').map(t => t.trim()).filter(t => t).join(',')
      });
    }
    setIsEditing(false);
  };

  const handleDelete = () => {
    if (onDelete) {
      onDelete(item.id);
    }
  };

  const todayStr = new Date().toISOString().split('T')[0];
  const itemDateStr = item.datetime ? item.datetime.split('T')[0] : '';
  const isOverdueItem = !item.completed && itemDateStr && itemDateStr < todayStr && item.type !== 'note';

  const cardClasses = [
    'item-card',
    item.type,
    item.completed ? 'completed' : '',
    isOverdueItem ? 'overdue-item' : '',
    isEditing ? 'editing' : ''
  ].filter(c => c).join(' ');

  if (isEditing) {
    return (
      <div className={cardClasses}>
        <div className="edit-form-group">
          <label>Title</label>
          <input
            type="text"
            className="edit-input"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            required
          />
        </div>

        <div className="edit-form-group">
          <label>Description</label>
          <textarea
            className="edit-textarea"
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            rows={2}
          />
        </div>

        <div className="edit-form-row">
          <div className="edit-form-group">
            <label>Due Date & Time</label>
            <input
              type="datetime-local"
              className="edit-input"
              value={editDatetime}
              onChange={(e) => setEditDatetime(e.target.value)}
            />
          </div>

          <div className="edit-form-group">
            <label>Priority</label>
            <select
              className="edit-select"
              value={editPriority}
              onChange={(e) => setEditPriority(e.target.value)}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>

        <div className="edit-form-group">
          <label>Tags (comma separated)</label>
          <input
            type="text"
            className="edit-input"
            value={editTags}
            onChange={(e) => setEditTags(e.target.value)}
            placeholder="tag1, tag2"
          />
        </div>

        <div className="edit-form-actions">
          <button onClick={handleSave} className="save-btn">Save</button>
          <button onClick={() => setIsEditing(false)} className="cancel-btn">Cancel</button>
        </div>
      </div>
    );
  }

  return (
    <div className={cardClasses}>
      <div className="item-header">
        {item.type !== 'note' && onToggle && (
          <input
            type="checkbox"
            checked={item.completed || false}
            onChange={() => onToggle(item.id, !item.completed)}
            className="checkbox"
          />
        )}
        <span className={`type-badge ${item.type}`}>
          {item.type}
        </span>
        <h3 className="item-title">{item.title}</h3>
        {item.type !== 'note' && (
          <span 
            className="priority-badge" 
            style={{ backgroundColor: getPriorityColor(item.priority) }}
          >
            {item.priority || 'medium'}
          </span>
        )}
      </div>

      {item.description && (
        <p className="item-description">{item.description}</p>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {item.datetime && (
          <div className="item-datetime">
            📅 {formatDate(item.datetime)}
          </div>
        )}

        {item.type === 'note' && item.created_at && (
          <div className="item-datetime" style={{ color: '#64748b', fontSize: '0.85rem' }}>
            📝 Created: {formatCreatedDate(item.created_at)}
          </div>
        )}
      </div>

      {item.tags && item.tags.length > 0 && (
        <div className="item-tags" style={{ marginTop: '0.75rem' }}>
          {item.tags.split(',').filter(t => t.trim()).map((tag, i) => (
            <span key={i} className="tag">#{tag.trim()}</span>
          ))}
        </div>
      )}

      <div className="item-footer">
        <div className="item-meta">
          {item.relevance_score && (
            <span className="relevance-score">
              Match: {(item.relevance_score * 100).toFixed(0)}%
            </span>
          )}
        </div>
        <div className="card-actions">
          {onUpdate && (
            <button 
              onClick={() => setIsEditing(true)} 
              className="edit-btn"
            >
              Edit
            </button>
          )}
          {onDelete && (
            <button 
              onClick={handleDelete} 
              className="delete-btn"
            >
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ItemCard;