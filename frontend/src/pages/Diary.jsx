import { useState, useEffect } from 'react';
import api from '../api';
import './Diary.css';

function formatDate(ts) {
  if (!ts) return '';
  try {
    return new Date(ts).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return ts; }
}

export default function Diary() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.get('/api/diary/entries')
      .then(({ data }) => setEntries(data.entries || []))
      .catch(() => setError('Failed to load diary entries'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = entries.filter(e =>
    e.message.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page">
      <h1 className="page-title">📔 My Diary</h1>
      <p className="page-subtitle">Your chronological writing timeline</p>

      {entries.length > 3 && (
        <div className="diary-search form-group">
          <input
            id="diary-search"
            placeholder="🔍 Search your entries..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      )}

      {loading && (
        <div className="diary-loading">
          <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
          <p>Loading your diary...</p>
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      {!loading && filtered.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📝</div>
          <h3>{search ? 'No entries match your search' : 'Your diary is empty'}</h3>
          <p>{search ? 'Try a different search term' : 'Start writing on the Home page and your entries will appear here'}</p>
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="diary-stats card">
          <span>📊 <strong>{entries.length}</strong> total entries</span>
          {search && <span>🔍 Showing <strong>{filtered.length}</strong> results</span>}
        </div>
      )}

      <div className="timeline">
        {filtered.map((entry, i) => (
          <div key={i} className="timeline-item">
            <div className="timeline-dot" />
            <div className="timeline-line" />
            <div className="timeline-card card">
              <div className="timeline-meta">
                <span className="timeline-date">🕐 {formatDate(entry.timestamp)}</span>
                <span className="entry-num">Entry #{entries.length - i}</span>
              </div>
              <p className="timeline-text">{entry.message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
