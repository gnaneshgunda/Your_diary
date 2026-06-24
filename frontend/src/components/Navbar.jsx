import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="navbar-brand">
          <span className="brand-icon">📖</span>
          <span className="brand-name">YourDiary</span>
        </NavLink>

        {user ? (
          <div className="navbar-links">
            <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
              ✍️ Write
            </NavLink>
            <NavLink to="/diary" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              📔 Diary
            </NavLink>
            <NavLink to="/tasks" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              ✅ Tasks
            </NavLink>
            <NavLink to="/entries" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              📋 Entries
            </NavLink>
            <div className="nav-divider" />
            <span className="nav-user">👤 {user.username}</span>
            <button className="nav-logout" onClick={handleLogout}>Logout</button>
          </div>
        ) : (
          <div className="navbar-links">
            <NavLink to="/login" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Login</NavLink>
            <NavLink to="/signup" className="nav-btn">Sign Up</NavLink>
          </div>
        )}
      </div>
    </nav>
  );
}
