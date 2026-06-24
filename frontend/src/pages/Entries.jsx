import { useState, useEffect } from 'react';
import api from '../api';

function formatDate(ts) {
  if (!ts) return '';
  try {
    return new Date(ts).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return ts; }
}

export default function Entries() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/diary/entries')
      .then(({ data }) => setEntries(data.entries || []))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <h1 className="page-title">📋 All Entries</h1>
      <p className="page-subtitle">Every thought you've captured — fuel for your AI</p>

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        </div>
      )}

      {!loading && entries.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">🌱</div>
          <h3>No entries yet</h3>
          <p>Write your first diary entry to start training your personal AI!</p>
        </div>
      )}

      {!loading && entries.length > 0 && (
        <>
          <div className="card" style={{ marginBottom: '1.5rem', padding: '0.85rem 1.25rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            📊 <strong style={{ color: 'var(--purple-400)' }}>{entries.length}</strong> entries · AI trains every 3 entries · Your model improves continuously
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {entries.map((e, i) => (
              <div key={i} className="card" style={{ padding: '1rem 1.25rem', display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                <div style={{
                  minWidth: 36, height: 36, borderRadius: '50%',
                  background: 'linear-gradient(135deg, var(--purple-600), var(--indigo-500))',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.8rem', fontWeight: 700, color: 'white', flexShrink: 0
                }}>
                  {entries.length - i}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: '0.95rem', lineHeight: 1.6, color: 'var(--text-primary)', marginBottom: '0.35rem', wordBreak: 'break-word' }}>
                    {e.message}
                  </p>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    🕐 {formatDate(e.timestamp)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
