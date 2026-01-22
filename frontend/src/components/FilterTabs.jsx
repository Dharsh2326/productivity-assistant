function FilterTabs({ activeFilter, onFilterChange }) {
  const filters = [
    { id: 'all', label: 'All', icon: '📋' },
    { id: 'task', label: 'Tasks', icon: '✅' },
    { id: 'note', label: 'Notes', icon: '📝' },
    { id: 'reminder', label: 'Reminders', icon: '⏰' }
  ];

  return (
    <div className="filter-tabs">
      {filters.map(filter => (
        <button
          key={filter.id}
          className={`filter-tab ${activeFilter === filter.id ? 'active' : ''}`}
          onClick={() => onFilterChange(filter.id)}
        >
          <span className="filter-icon">{filter.icon}</span>
          <span className="filter-label">{filter.label}</span>
        </button>
      ))}
    </div>
  );
}

export default FilterTabs;