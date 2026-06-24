import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import './Auth.css';

export default function Signup() {
  const [form, setForm] = useState({ username: '', password: '', confirm: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirm) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      await api.post('/api/auth/signup', { username: form.username, password: form.password });
      setSuccess('Account created! Redirecting to login...');
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-glow" />
      <div className="auth-card">
        <div className="auth-logo">
          <span className="auth-logo-icon">📖</span>
          <h1 className="auth-logo-text">YourDiary</h1>
          <p className="auth-tagline">Start your AI-enhanced journaling journey</p>
        </div>

        <h2 className="auth-title">Create your account</h2>
        <p className="auth-subtitle">Join thousands of mindful writers</p>

        {error && <div className="alert alert-error">⚠️ {error}</div>}
        {success && <div className="alert alert-success">✅ {success}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              id="signup-username"
              type="text"
              placeholder="Choose a username (min 3 chars)"
              value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              id="signup-password"
              type="password"
              placeholder="Choose a password (min 4 chars)"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              required
            />
          </div>
          <div className="form-group">
            <label>Confirm Password</label>
            <input
              id="signup-confirm"
              type="password"
              placeholder="Repeat your password"
              value={form.confirm}
              onChange={e => setForm(f => ({ ...f, confirm: e.target.value }))}
              required
            />
          </div>

          <button id="signup-submit" type="submit" className="btn btn-primary btn-lg auth-submit" disabled={loading}>
            {loading ? <><span className="spinner" /> Creating account...</> : '🚀 Create Account'}
          </button>
        </form>

        <div className="divider">or</div>
        <p className="auth-switch">
          Already have an account?{' '}
          <Link to="/login" className="auth-link">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
