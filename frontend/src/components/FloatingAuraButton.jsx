import { Sparkles } from 'lucide-react';

function FloatingAuraButton({ isOpen, onClick }) {
  return (
    <button
      className={`floating-aura-btn ${isOpen ? 'open' : ''}`}
      onClick={onClick}
      aria-label="Ask Aura"
      title="Ask Aura AI Assistant"
    >
      <div className="aura-glow-effect"></div>
      <Sparkles size={24} className="aura-icon" />
    </button>
  );
}

export default FloatingAuraButton;
