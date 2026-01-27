import { useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import '../styles/Landing.css';
import personalImg from '../assets/images/personalImg.png';
import professionalImg from '../assets/images/professionalImg.png';
import studentImg from '../assets/images/StudentsImg.png';

function LandingPage() {
  const navigate = useNavigate();

  const mainFeatures = [
    {
      title: 'AI-Powered',
      description: 'Natural language processing understands what you mean, when you mean it',
    },
    {
      title: 'Lightning Fast',
      description: 'Instant task creation with optimistic UI - no waiting for responses',
    },
    {
      title: 'Auto-Sync',
      description: 'Automatically sync with calendar and extract tasks from emails',
    },
  ];

  const useCases = [
    {
      title: 'For Professionals',
      description: 'Track meetings, deadlines, and project tasks with natural language input. Manage work tasks efficiently.',
      example: '"Team standup tomorrow at 9am" → Reminder created automatically',
      imageUrl: professionalImg,
      imageType: 'professional'
    },
    {
      title: 'For Students',
      description: 'Track assignments and exams effectively with AI-powered deadline tracking. Organize study sessions and project work seamlessly.',
      example: '"Math assignment due Friday" → High priority task with date',
      imageUrl: studentImg,
      imageType: 'student'
    },
    {
      title: 'For Personal Life',
      description: 'Manage personal tasks and goals efficiently. Keep your life balanced and stress-free.',
      example: '"Buy groceries this weekend" → Shopping task for Saturday',
      imageUrl: personalImg,
      imageType: 'personal'
    },
  ];

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-new">
        <div className="hero-container">
          {/* CENTERED APP NAME */}
          <div className="hero-title-section">
            <h1 className="hero-title-main">AuraPlan</h1>
            <p className="hero-subtitle-main">AI-powered assistant for managing tasks and reminders</p>
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
                      <span className="task-text">Team meeting at 3pm</span>
                      <span className="task-priority">HIGH</span>
                    </div>
                    <div className="mockup-task medium">
                      <span className="task-text">Review project proposal</span>
                      <span className="task-priority">MEDIUM</span>
                    </div>
                    <div className="mockup-task low">
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
              <h3>Enter Tasks Naturally</h3>
              <p>Enter tasks in natural language: 'Schedule dentist appointment tomorrow at 2 PM'</p>
            </div>

            <div className="step-card">
              <h3>AI Parses Your Input</h3>
              <p>Our local LLM extracts the task, time, priority, and category automatically</p>
            </div>

            <div className="step-card">
              <h3>Tasks Organized Automatically</h3>
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
                <img 
                  src={useCase.imageUrl} 
                  alt={useCase.title}
                  className="zigzag-real-image"
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Deep Dive */}
      <section className="features-deep">
        <div className="section-container">
          <div className="section-header">
            <h2>Powerful Features</h2>
            <p>Everything you need to stay organized and productive</p>
          </div>

          <div className="features-list">
            <div className="feature-row">
              <div className="feature-content">
                <h3>Natural Language Processing</h3>
                <p>Input tasks in natural language. Our AI understands context, extracts dates, priorities, and categories from your natural language input.</p>
                <ul className="feature-points">
                  <li>Understands relative dates ("tomorrow", "next week")</li>
                  <li>Extracts priorities ("urgent", "important")</li>
                  <li>Categorizes automatically (task, note, reminder)</li>
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

            <div className="feature-row">
              <div className="feature-content">
                <h3>Visual Day View</h3>
                <p>View a comprehensive timeline of your daily tasks. Perfect for planning and reviewing your schedule.</p>
                <ul className="feature-points">
                  <li>Color-coded by priority and type</li>
                  <li>Timeline view with time slots</li>
                  <li>Clear visual organization</li>
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
            <div className="coming-soon-badge">COMING SOON</div>
            <h2 className="coming-soon-title">Upcoming Features</h2>
            <p className="coming-soon-subtitle">We're constantly improving AuraPlan</p>
            
            <div className="coming-features-grid">
              <div className="coming-feature">
                <h3>Gmail Integration</h3>
                <p>Automatically extract tasks from emails and newsletters</p>
              </div>
              <div className="coming-feature">
                <h3>Google Calendar Sync</h3>
                <p>Two-way sync with your Google Calendar events</p>
              </div>
              <div className="coming-feature">
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
          <button className="btn-primary-large" onClick={() => navigate('/login')}>
            Login <ArrowRight size={24} />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer-new">
        <div className="footer-content">
          <div className="footer-brand">
            <h3>AuraPlan</h3>
            <p>AI-powered productivity assistant</p>
          </div>

          <div className="footer-info">
            <p>© 2026 AuraPlan. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;