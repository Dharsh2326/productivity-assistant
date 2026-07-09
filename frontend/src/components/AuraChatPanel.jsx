import { useState, useRef, useEffect } from 'react';
import { Send, X, Bot, User, Sparkles, Loader, CheckCircle, AlertTriangle, Info, Trash2, Edit, CheckSquare, PlusCircle } from 'lucide-react';
import { askAura } from '../services/api';

function AuraChatPanel({ isOpen, onClose }) {
  // Generate or retrieve persistent Session ID
  const [sessionId] = useState(() => {
    let id = sessionStorage.getItem('aura_session_id');
    if (!id) {
      id = 'session_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
      sessionStorage.setItem('aura_session_id', id);
    }
    return id;
  });

  const [messages, setMessages] = useState(() => {
    const saved = sessionStorage.getItem('aura_messages');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse saved aura messages', e);
      }
    }
    return [
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Hello! I am Aura, your AI productivity workspace assistant. I can now create, update, complete, and delete your tasks, reminders, and notes. Try asking me something!',
        sources: [],
        actionPerformed: false
      }
    ];
  });

  useEffect(() => {
    sessionStorage.setItem('aura_messages', JSON.stringify(messages));
  }, [messages]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  
  const messagesEndRef = useRef(null);

  const suggestedPrompts = [
    'What should I do today?',
    'Remind me to revise DBMS tomorrow 7pm',
    'Mark groceries as complete',
    'Delete old gym reminder',
    'Move DBMS assignment to Friday'
  ];

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (textToSend, confirmAction = null, pendingConfData = null) => {
    if (!textToSend.trim() && !confirmAction) return;
    if (loading) return;

    const userMsgText = confirmAction ? (confirmAction === 'confirm' ? 'Confirm' : 'Cancel') : textToSend;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: userMsgText
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
      const data = await askAura(textToSend, historyPayload, confirmAction, sessionId);
      
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || "No response received.",
        sources: data.sources || [],
        actionPerformed: data.action_performed || false,
        actionType: data.action_type || null,
        affectedItems: data.affected_items || [],
        pendingConfirmation: data.pending_confirmation || null,
        ambiguousMatches: data.ambiguous_matches || null
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Emit refresh event if an action was executed
      if (data.action_performed) {
        window.dispatchEvent(new CustomEvent('aura-refresh-data'));
      }
    } catch (err) {
      console.error('Ask Aura error:', err);
      const friendlyErr = err.error || "I'm having trouble connecting to my backend. Please make sure the backend server and Ollama are running.";
      setErrorMsg(friendlyErr);
      
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

  // Helper to render action icon
  const getActionIcon = (actionType) => {
    if (!actionType) return <CheckCircle className="action-icon" size={16} />;
    if (actionType.startsWith('create')) return <PlusCircle className="action-icon create-color" size={16} />;
    if (actionType.startsWith('complete')) return <CheckSquare className="action-icon complete-color" size={16} />;
    if (actionType.startsWith('delete')) return <Trash2 className="action-icon delete-color" size={16} />;
    return <Edit className="action-icon update-color" size={16} />;
  };

  // Helper to format date
  const formatItemDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return dateStr;
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
                
                {/* Standard Message Bubble */}
                <div className="message-bubble">
                  {msg.content}
                </div>

                {/* Ambiguous matches / Disambiguation choices */}
                {isAssistant && msg.ambiguousMatches && msg.ambiguousMatches.length > 0 && (
                  <div className="disambiguation-container">
                    <div className="disambiguation-label">Matching items found:</div>
                    <div className="disambiguation-list">
                      {msg.ambiguousMatches.map((item) => (
                        <button
                          key={item.id}
                          className="disambiguation-choice-btn"
                          onClick={() => handleSendMessage(String(item.id))}
                        >
                          <span className={`item-type-tag ${item.type}`}>{item.type.toUpperCase()}</span>
                          <span className="item-title">{item.title}</span>
                          <span className="item-id-hint">ID: {item.id}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Pending Confirmation Card */}
                {isAssistant && msg.pendingConfirmation && (
                  <div className="aura-confirmation-card">
                    <div className="confirmation-header">
                      <AlertTriangle size={18} className="warn-icon" />
                      <span>Confirm {msg.pendingConfirmation.action_type.replace('_', ' ')}</span>
                    </div>
                    <div className="confirmation-body">
                      {msg.pendingConfirmation.affected_items && msg.pendingConfirmation.affected_items.map((item, idx) => (
                        <div key={idx} className="affected-item-row">
                          <span className={`item-type-badge ${item.type}`}>{item.type.toUpperCase()}</span>
                          <div className="item-detail">
                            <div className="item-title">{item.title}</div>
                            {item.datetime && <div className="item-date">{formatItemDate(item.datetime)}</div>}
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="confirmation-actions">
                      <button 
                        className="btn-confirm" 
                        onClick={() => handleSendMessage('', 'confirm', msg.pendingConfirmation)}
                        disabled={loading}
                      >
                        Confirm
                      </button>
                      <button 
                        className="btn-cancel" 
                        onClick={() => handleSendMessage('', 'cancel', msg.pendingConfirmation)}
                        disabled={loading}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* Actions Performed Section (Separated from Sources) */}
                {isAssistant && msg.actionPerformed && msg.affectedItems && msg.affectedItems.length > 0 && (
                  <div className="aura-actions-performed-container">
                    <div className="actions-performed-label">Actions Performed:</div>
                    <div className="actions-list">
                      {msg.affectedItems.map((item, idx) => (
                        <div key={idx} className="action-item-card">
                          <div className="action-item-header">
                            {getActionIcon(msg.actionType)}
                            <span className="action-type-text">
                              {msg.actionType ? msg.actionType.replace('_', ' ').toUpperCase() : 'UPDATED'}
                            </span>
                          </div>
                          <div className="action-item-body">
                            <div className="action-item-title">{item.title}</div>
                            {item.description && <div className="action-item-desc">{item.description}</div>}
                            <div className="action-item-meta">
                              <span className={`meta-type-tag ${item.type}`}>{item.type.toUpperCase()}</span>
                              {item.priority && <span className={`meta-priority ${item.priority}`}>{item.priority}</span>}
                              {item.datetime && <span className="meta-date">{formatItemDate(item.datetime)}</span>}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Sources Used Section (Separated from Actions) */}
                {isAssistant && msg.sources && msg.sources.length > 0 && (
                  <div className="aura-message-sources">
                    <div className="sources-label">Sources Used:</div>
                    <div className="sources-list">
                      {msg.sources.map((src, index) => (
                        <div 
                          key={index} 
                          className="source-item-chip" 
                          title={`ID: ${src.id} | Relevance: ${Math.round(src.relevance_score * 100)}%`}
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
        <p className="suggestions-header">Try commands:</p>
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
            placeholder="Ask Aura or manage AuraPlan..."
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
