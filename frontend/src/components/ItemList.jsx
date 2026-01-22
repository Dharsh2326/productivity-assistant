import ItemCard from './ItemCard';

function ItemList({ items, onDelete, onToggle, loading }) {
  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Loading items...</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📭</div>
        <h3>No items yet</h3>
        <p>Start by adding a task, note, or reminder above!</p>
      </div>
    );
  }

  return (
    <div className="item-list">
      {items.map(item => (
        <ItemCard
          key={item.id}
          item={item}
          onDelete={onDelete}
          onToggle={onToggle}
        />
      ))}
    </div>
  );
}

export default ItemList;