import { useState, useEffect } from 'react';

function SearchBar({ onSearch, onClear, isSearchMode, query }) {
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    setSearchQuery(query || '');
  }, [query]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    await onSearch(searchQuery);
  };

  const handleClear = () => {
    setSearchQuery('');
    onClear();
  };

  return (
    <div className="search-bar">
      <form onSubmit={handleSearch}>
        <div className="search-input-group">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="🔍 Semantic search: 'work tasks' or 'health reminders' or 'shopping'"
            className="search-input"
          />
          <button 
            type="submit" 
            disabled={!searchQuery.trim()}
            className="search-btn"
          >
            🔍 Search
          </button>
          {isSearchMode && (
            <button 
              type="button"
              onClick={handleClear}
              className="clear-btn"
            >
              ✖️ Clear
            </button>
          )}
        </div>
      </form>
      {isSearchMode && searchQuery && (
        <p className="search-mode-indicator">
          🎯 Showing search results for: "<strong>{searchQuery}</strong>"
        </p>
      )}
    </div>
  );
}

export default SearchBar;