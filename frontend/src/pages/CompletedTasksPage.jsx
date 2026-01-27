import { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar';
import ItemList from '../components/ItemList';
import { getItemsGrouped, updateItem } from '../services/api';
import '../styles/Dashboard.css';

function CompletedTasksPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCompletedItems();
  }, []);

  const loadCompletedItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getItemsGrouped('today');

      // Flatten + filter completed items
      const allItems = response.items || [];
      const completedItems = allItems.filter(item => item.completed);

      setItems(completedItems);
    } catch (err) {
      setError('Unable to load completed tasks');
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async (id) => {
    try {
      await updateItem(id, { completed: false });
      setItems(items.filter(item => item.id !== id));
    } catch {
      setError('Failed to restore task');
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main">
        <div className="dashboard-header">
          <h1> Completed Tasks</h1>
          <p className="view-subtitle">
            {items.length} completed {items.length === 1 ? 'task' : 'tasks'}
          </p>
        </div>

        {error && <p className="error-text">{error}</p>}

        <section className="items-section">
          <ItemList
            items={items}
            onToggle={(id) => handleRestore(id)}
            onDelete={null}
            loading={loading}
          />
        </section>
      </main>
    </div>
  );
}

export default CompletedTasksPage;
