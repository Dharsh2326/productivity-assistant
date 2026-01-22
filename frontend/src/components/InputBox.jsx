import { useState } from 'react';

function InputBox({ onSubmit }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);
    try {
      await onSubmit(input);
      setInput('');
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="input-box">
      <form onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type naturally: 'Remind me to call mom tomorrow at 5pm' or 'Buy groceries next week' or 'Note: Meeting with team about Q1 goals'"
          rows="4"
          disabled={loading}
          className="input-textarea"
        />
        <button 
          type="submit" 
          disabled={loading || !input.trim()}
          className="submit-btn"
        >
          {loading ? '⏳ Processing...' : '✨ Add Item'}
        </button>
      </form>
    </div>
  );
}

export default InputBox;