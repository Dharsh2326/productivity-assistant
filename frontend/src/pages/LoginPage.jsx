import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, ArrowRight, Eye, EyeOff } from 'lucide-react';
import '../styles/Login.css';

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Simulate login process
    setTimeout(() => {
      // Clear any existing data
      localStorage.removeItem('taskmaster_session');
      // Create new session
      localStorage.setItem('taskmaster_session', JSON.stringify({
        email,
        loginTime: new Date().toISOString()
      }));
      // Navigate to dashboard
      navigate('/dashboard');
    }, 800);
  };

  return (
    <div className="login-page">
      {/* Animated Background Elements */}
      <div className="login-bg-shape shape-1"></div>
      <div className="login-bg-shape shape-2"></div>
      <div className="login-bg-shape shape-3"></div>

      <div className="login-container">
        {/* Login Card */}
        <div className="login-card">
          {/* Header */}
          <div className="login-header">
            <h1>AuraPlan</h1>
            <p>Sign in to access your workspace</p>
          </div>

          {/* Form */}
          <form onSubmit={handleLogin} className="login-form">
            {/* Email Field */}
            <div className="form-group">
              <label>
                <Mail size={18} />
                Email Address
              </label>
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            {/* Password Field */}
            <div className="form-group">
              <label>
                <Lock size={18} />
                Password
              </label>
              <div className="password-input-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLoading}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button 
              type="submit" 
              className="btn-primary login-btn"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className="spinner"></span>
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight size={20} />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Back Button */}
        <button className="back-btn" onClick={() => navigate('/')}>
          ← Back to Home
        </button>
      </div>
    </div>
  );
}

export default LoginPage;