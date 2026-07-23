import auraAvatar from '../assets/images/aura-avatar.png';

function FloatingAuraButton({ isOpen, onClick }) {
  return (
    <button
      className={`floating-aura-btn ${isOpen ? 'open' : ''}`}
      onClick={onClick}
      aria-label="Ask Aura"
      title="Ask Aura AI Assistant"
    >
      <div className="aura-glow-effect"></div>
      <img src={auraAvatar} alt="Aura" className="aura-icon" width={48} height={48} />
    </button>
  );
}

export default FloatingAuraButton;