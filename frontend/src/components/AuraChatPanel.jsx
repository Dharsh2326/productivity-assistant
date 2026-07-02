import { useState, useRef, useEffect } from 'react';
import { Send, X, Bot, User, Sparkles, Loader } from 'lucide-react';
import { askAura } from '../services/api';

function AuraChatPanel({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am Aura, your AI productivity workspace assistant. How can I help you organize or prioritize your day?',
      sources: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  
  const messagesEndRef = useRef(null);

  const suggestedPrompts = [
    'What should I do today?',
    'Show overdue tasks.',
    'Show my reminders.',
    'Show my notes.',
    'Summarize my workload.'
  ];

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (textToSend) => {
    if (!textToSend.trim() || loading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: textToSend
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setErrorMsg(null);

    // Build history for backend (role: 'user' / 'assistant', content)
    const historyPayload = messages.map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    try {
      const data = await askAura(textToSend, historyPayload);
      
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || "I didn't get a proper response.",
        sources: data.sources || []
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Ask Aura error:', err);
      const friendlyErr = err.error || "I'm having trouble connecting to my backend. Please make sure the backend server and Ollama are running.";
      setErrorMsg(friendlyErr);
      
      // Also add an assistant message indicating failure
      setMessages(prev => [
        ...prev, 
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `⚠️ Failed to get response: ${friendlyErr}`,
          sources: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(input);
    }
  };

  return (
    <div className={`aura-chat-panel ${isOpen ? 'open' : ''}`}>
      {/* Panel Header */}
      <div className="aura-panel-header">
        <div className="header-title">
          <Bot className="aura-header-bot-icon" size={20} />
          <span>Ask Aura AI</span>
        </div>
        <button className="close-panel-btn" onClick={onClose} aria-label="Close panel">
          <X size={20} />
        </button>
      </div>

      {/* Messages Window */}
      <div className="aura-messages-container">
        {messages.map((msg) => {
          const isAssistant = msg.role === 'assistant';
          return (
            <div key={msg.id} className={`chat-message-row ${isAssistant ? 'assistant-row' : 'user-row'}`}>
              <div className="message-avatar">
                {isAssistant ? <Sparkles size={16} /> : <User size={16} />}
              </div>
              <div className="message-content-wrapper">
                <div className="message-bubble">
                  {msg.content}
                </div>
                
                {/* Sources Attribution */}
                {isAssistant && msg.sources && msg.sources.length > 0 && (
                  <div className="aura-message-sources">
                    <div className="sources-label">Sources Consulted:</div>
                    <div className="sources-list">
                      {msg.sources.map((src, index) => (
                        <div 
                          key={index} 
                          className="source-item-chip" 
                          title={`ID: ${src.id} | Match: ${Math.round(src.relevance_score * 100)}%`}
                        >
                          <span className={`source-type-badge ${src.type}`}>
                            {src.type.toUpperCase()}
                          </span>
                          <span className="source-title-text">{src.title}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading / Typing Indicator */}
        {loading && (
          <div className="chat-message-row assistant-row loading-row">
            <div className="message-avatar">
              <Sparkles size={16} />
            </div>
            <div className="message-bubble loading-bubble">
              <Loader className="spinner-icon" size={16} />
              <span>Aura is thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts Section */}
      <div className="aura-suggestions-container">
        <p className="suggestions-header">Quick Questions:</p>
        <div className="suggestions-list">
          {suggestedPrompts.map((prompt, idx) => (
            <button 
              key={idx} 
              className="suggestion-chip-btn"
              onClick={() => handleSendMessage(prompt)}
              disabled={loading}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Footer / Input Box */}
      <div className="aura-panel-footer">
        {errorMsg && (
          <div className="aura-footer-error">
            <span>{errorMsg}</span>
            <button className="clear-error-btn" onClick={() => setErrorMsg(null)}>✖</button>
          </div>
        )}
        <div className="aura-input-wrapper">
          <textarea
            className="aura-chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask Aura about your tasks, notes..."
            rows={1}
            disabled={loading}
          />
          <button 
            className="aura-send-btn" 
            onClick={() => handleSendMessage(input)} 
            disabled={loading || !input.trim()}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default AuraChatPanel;
