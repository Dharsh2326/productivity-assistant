import { useNavigate } from 'react-router-dom';
import { Calendar, Brain, Search, Sparkles, Zap, Mail, ArrowRight, CheckCircle, Clock } from 'lucide-react';
import FeatureCard from '../components/FeatureCard';
import '../styles/Landing.css';
import personalImg from '../assets/images/personalImg.png';
import professionalImg from '../assets/images/professionalImg.png';
import studentImg from '../assets/images/StudentsImg.png';
function LandingPage() {
  const navigate = useNavigate();

  const mainFeatures = [
    {
      icon: <Brain size={40} />,
      title: 'AI-Powered',
      description: 'Natural language processing understands what you mean, when you mean it',
    },
    {
      icon: <Zap size={40} />,
      title: 'Lightning Fast',
      description: 'Instant task creation with optimistic UI - no waiting for responses',
    },
    {
      icon: <Search size={40} />,
      title: 'Smart Search',
      description: 'Semantic vector search finds tasks by meaning, not just keywords',
    },
    {
      icon: <Calendar size={40} />,
      title: 'Auto-Sync',
      description: 'Automatically sync with calendar and extract tasks from emails',
    },
  ];

  const useCases = [
    {
      title: 'For Professionals',
      description: 'Track meetings, deadlines, and project tasks with natural language input. Stay on top of your work schedule effortlessly.',
      example: '"Team standup tomorrow at 9am" → Reminder created automatically',
      imageUrl: professionalImg,
      imageType: 'professional'
    },
    {
      title: 'For Students',
      description: 'Never miss an assignment or exam with AI-powered deadline tracking. Organize study sessions and project work seamlessly.',
      example: '"Math assignment due Friday" → High priority task with date',
      imageUrl: studentImg,
      imageType: 'student'
    },
    {
      title: 'For Personal Life',
      description: 'Organize errands, appointments, and personal goals effortlessly. Keep your life balanced and stress-free.',
      example: '"Buy groceries this weekend" → Shopping task for Saturday',
      imageUrl: personalImg,
      imageType: 'personal'
    },
  ];

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-new">
        <div className="floating-shape shape-1"></div>
        <div className="floating-shape shape-2"></div>
        <div className="floating-shape shape-3"></div>

        <div className="hero-container">
          {/* CENTERED APP NAME */}
          <div className="hero-title-section">
            <h1 className="hero-title-main">AuraPlan</h1>
            <p className="hero-subtitle-main">Your AI-powered productivity companion</p>
          </div>

          {/* Hero Content - Split Layout */}
          <div className="hero-split">
            <div className="hero-left">
              <p className="hero-description-large">
                Capture tasks, notes, and reminders using <strong>natural language</strong>.
              </p>
              <p className="hero-description-sub">
                Powered by AI to understand what you mean, when you mean it.
              </p>
              
              <div className="hero-buttons">
                <button className="btn-primary-new" onClick={() => navigate('/login')}>
                  Get Started <ArrowRight size={20} />
                </button>
                <button className="btn-secondary-new" onClick={() => navigate('/dashboard')}>
                  View Demo
                </button>
              </div>
            </div>

            <div className="hero-right">
              <div className="app-mockup">
                <div className="mockup-header">
                  <div className="mockup-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <div className="mockup-title">AuraPlan Dashboard</div>
                </div>
                <div className="mockup-content">
                  <div className="mockup-input">
                    <input type="text" placeholder="Remind me to call mom tomorrow at 5pm..." readOnly />
                    <button>Add</button>
                  </div>
                  <div className="mockup-tasks">
                    <div className="mockup-task high">
                      <span className="task-icon">✅</span>
                      <span className="task-text">Team meeting at 3pm</span>
                      <span className="task-priority">HIGH</span>
                    </div>
                    <div className="mockup-task medium">
                      <span className="task-icon">📅</span>
                      <span className="task-text">Review project proposal</span>
                      <span className="task-priority">MEDIUM</span>
                    </div>
                    <div className="mockup-task low">
                      <span className="task-icon">📝</span>
                      <span className="task-text">Buy groceries</span>
                      <span className="task-priority">LOW</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Features Grid */}
          <div className="features-grid-hero">
            {mainFeatures.map((feature, index) => (
              <div key={index} className="feature-card-hero">
                <div className="feature-icon-hero">{feature.icon}</div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works">
        <div className="section-container">
          <div className="section-header">
            <h2>How It Works</h2>
            <p>Three simple steps to boost your productivity</p>
          </div>

          <div className="steps-grid">
            <div className="step-card">
              <div className="step-number">1</div>
              <h3>Type Naturally</h3>
              <p>Just write in plain English: "Call dentist tomorrow at 2pm" or "Buy milk this evening"</p>
            </div>

            <div className="step-card">
              <div className="step-number">2</div>
              <h3>AI Understands</h3>
              <p>Our local LLM extracts the task, time, priority, and category automatically</p>
            </div>

            <div className="step-card">
              <div className="step-number">3</div>
              <h3>Get Organized</h3>
              <p>Tasks appear in Today/Tomorrow/Upcoming views, perfectly organized</p>
            </div>
          </div>
        </div>
      </section>

      {/* Perfect For Everyone - Zigzag Layout */}
      <section className="use-cases-zigzag">
        <div className="section-container">
          <div className="section-header">
            <h2>Perfect For Everyone</h2>
            <p>Whether you're a professional, student, or managing personal tasks</p>
          </div>

          {useCases.map((useCase, index) => (
            <div key={index} className={`zigzag-row ${index % 2 === 1 ? 'reverse' : ''}`}>
              <div className="zigzag-content">
                <h3>{useCase.title}</h3>
                <p className="zigzag-desc">{useCase.description}</p>
                <div className="zigzag-example">
                  <code>{useCase.example}</code>
                </div>
              </div>
              <div className="zigzag-image">
                {/* CONDITIONAL: Show real image if provided, else placeholder */}
                {useCase.imageUrl ? (
                  <img 
                    src={useCase.imageUrl} 
                    alt={useCase.title}
                    className="zigzag-real-image"
                  />
                ) : (
                  <div className={`placeholder-image ${useCase.imageType}`}>
                    <div className="placeholder-content">
                      <div className="placeholder-icon">
                        {useCase.imageType === 'professional' && '💼'}
                        {useCase.imageType === 'student' && '🎓'}
                        {useCase.imageType === 'personal' && '🏠'}
                      </div>
                      <div className="placeholder-text">
                        {useCase.imageType === 'professional' && 'Professional Dashboard'}
                        {useCase.imageType === 'student' && 'Student Planner'}
                        {useCase.imageType === 'personal' && 'Personal Life'}
                      </div>
                      <div className="placeholder-items">
                        {useCase.imageType === 'professional' && (
                          <>
                            <div className="placeholder-item">📊 Q1 Report</div>
                            <div className="placeholder-item">👥 Client Meeting</div>
                            <div className="placeholder-item">📧 Email Review</div>
                          </>
                        )}
                        {useCase.imageType === 'student' && (
                          <>
                            <div className="placeholder-item">📚 Study Math</div>
                            <div className="placeholder-item">✍️ Essay Draft</div>
                            <div className="placeholder-item">🔬 Lab Report</div>
                          </>
                        )}
                        {useCase.imageType === 'personal' && (
                          <>
                            <div className="placeholder-item">🛒 Groceries</div>
                            <div className="placeholder-item">🏃 Gym Session</div>
                            <div className="placeholder-item">👨‍👩‍👧 Family Time</div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Deep Dive - Updated */}
      <section className="features-deep">
        <div className="section-container">
          <div className="section-header">
            <h2>Powerful Features</h2>
            <p>Everything you need to stay organized and productive</p>
          </div>

          <div className="features-list">
            <div className="feature-row">
              <div className="feature-content">
                <h3><Sparkles size={24} /> Natural Language Processing</h3>
                <p>Type like you speak. Our AI understands context, extracts dates, priorities, and categories from your natural language input.</p>
                <ul className="feature-points">
                  <li><CheckCircle size={18} /> Understands relative dates ("tomorrow", "next week")</li>
                  <li><CheckCircle size={18} /> Extracts priorities ("urgent", "important")</li>
                  <li><CheckCircle size={18} /> Categorizes automatically (task, note, reminder)</li>
                </ul>
              </div>
              <div className="feature-visual">
                <div className="demo-card">
                  <div className="demo-input">"Team meeting tomorrow at 3pm - discuss Q1 goals"</div>
                  <div className="demo-arrow">→</div>
                  <div className="demo-output">
                    <div><strong>Type:</strong> Reminder</div>
                    <div><strong>Time:</strong> Tomorrow 3:00 PM</div>
                    <div><strong>Priority:</strong> Medium</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="feature-row reverse">
              <div className="feature-visual">
                <div className="demo-card">
                  <div className="demo-input">Search: "health tasks"</div>
                  <div className="demo-results">
                    <div className="result-item">🏃 Morning jog</div>
                    <div className="result-item">🏥 Doctor appointment</div>
                    <div className="result-item">💊 Buy vitamins</div>
                  </div>
                </div>
              </div>
              <div className="feature-content">
                <h3><Search size={24} /> Semantic Search</h3>
                <p>Find tasks by meaning, not just keywords. Vector database powered search understands relationships and context.</p>
                <ul className="feature-points">
                  <li><CheckCircle size={18} /> Search by concept, not exact words</li>
                  <li><CheckCircle size={18} /> Finds related tasks automatically</li>
                  <li><CheckCircle size={18} /> ChromaDB vector embeddings</li>
                </ul>
              </div>
            </div>

            <div className="feature-row">
              <div className="feature-content">
                <h3><Calendar size={24} /> Visual Day View</h3>
                <p>See your entire day as a beautiful timeline visualization. Perfect for planning and reviewing your schedule.</p>
                <ul className="feature-points">
                  <li><CheckCircle size={18} /> Color-coded by priority and type</li>
                  <li><CheckCircle size={18} /> Timeline view with time slots</li>
                  <li><CheckCircle size={18} /> Clear visual organization</li>
                </ul>
              </div>
              <div className="feature-visual">
                <div className="timeline-preview">
                  <div className="timeline-item priority-high">9:00 AM - Team Meeting</div>
                  <div className="timeline-item priority-medium">2:00 PM - Code Review</div>
                  <div className="timeline-item priority-low">5:00 PM - Gym</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Coming Soon Section */}
      <section className="coming-soon-full">
        <div className="section-container">
          <div className="coming-soon-section">
            <div className="coming-soon-badge">🚀 COMING SOON</div>
            <h2 className="coming-soon-title">Upcoming Features</h2>
            <p className="coming-soon-subtitle">We're constantly improving AuraPlan</p>
            
            <div className="coming-features-grid">
              <div className="coming-feature">
                <Mail size={32} />
                <h3>Gmail Integration</h3>
                <p>Automatically extract tasks from emails and newsletters</p>
              </div>
              <div className="coming-feature">
                <Calendar size={32} />
                <h3>Google Calendar Sync</h3>
                <p>Two-way sync with your Google Calendar events</p>
              </div>
              <div className="coming-feature">
                <Clock size={32} />
                <h3>Smart Reminders</h3>
                <p>Push notifications and desktop alerts</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="final-cta">
        <div className="cta-container">
          <h2>Ready to Transform Your Productivity?</h2>
          <p>Join the AI-powered productivity revolution. No credit card required.</p>
          <button className="btn-primary-large" onClick={() => navigate('/login')}>
            Start Free Now <ArrowRight size={24} />
          </button>
          <p className="cta-note">✨ Setup takes less than 2 minutes</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer-new">
        <div className="footer-content">
          <div className="footer-brand">
            <h3>✨ AuraPlan</h3>
            <p>AI-powered productivity for everyone</p>
          </div>
          <div className="footer-info">
            <p className="tech-stack">React • Flask • Ollama • ChromaDB • SQLite</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;