import { useState, useEffect } from 'react';
import api from '../api';
import './Tasks.css';

function formatDate(d) {
  if (!d) return null;
  try { return new Date(d + 'T00:00:00').toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }); }
  catch { return d; }
}

const PRIORITY_LABELS = { high: '🔴 High', medium: '🟡 Medium', low: '🟢 Low' };

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState({ total: 0, pending: 0, completed: 0, overdue: 0 });
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', priority: 'medium', due_date: '' });
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const loadTasks = async () => {
    try {
      const { data } = await api.get('/api/tasks');
      setTasks(data.tasks || []);
      setStats(data.stats || {});
    } catch { showToast('Failed to load tasks', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadTasks(); }, []);

  const handleCreate = async () => {
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      await api.post('/api/tasks', { ...form, due_date: form.due_date || null });
      showToast('✅ Task created!');
      setShowModal(false);
      setForm({ title: '', description: '', priority: 'medium', due_date: '' });
      loadTasks();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create task', 'error');
    } finally { setSaving(false); }
  };

  const toggleStatus = async (task) => {
    const newStatus = task.status === 'completed' ? 'pending' : 'completed';
    try {
      await api.patch(`/api/tasks/${task.id}/status`, { status: newStatus });
      setTasks(prev => prev.map(t => t.id === task.id ? { ...t, status: newStatus } : t));
      setStats(prev => ({
        ...prev,
        completed: newStatus === 'completed' ? prev.completed + 1 : prev.completed - 1,
        pending: newStatus === 'pending' ? prev.pending + 1 : prev.pending - 1,
      }));
    } catch { showToast('Failed to update task', 'error'); }
  };

  const deleteTask = async (id) => {
    try {
      await api.delete(`/api/tasks/${id}`);
      setTasks(prev => prev.filter(t => t.id !== id));
      showToast('🗑️ Task deleted');
      loadTasks();
    } catch { showToast('Failed to delete task', 'error'); }
  };

  const today = new Date().toISOString().split('T')[0];
  const isOverdue = (task) => task.status !== 'completed' && task.due_date && task.due_date < today;

  return (
    <div className="page-wide tasks-page">
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      {/* Header */}
      <div className="tasks-header">
        <div>
          <h1 className="page-title">✅ My Tasks</h1>
          <p className="page-subtitle">Organize your life with AI-enhanced task management</p>
        </div>
        <button id="add-task-btn" className="btn btn-primary" onClick={() => setShowModal(true)}>
          ➕ Add Task
        </button>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        {[
          { label: 'Total',     value: stats.total,     icon: '📋', cls: 'stat-total' },
          { label: 'Pending',   value: stats.pending,   icon: '⏳', cls: 'stat-pending' },
          { label: 'Completed', value: stats.completed, icon: '✅', cls: 'stat-done' },
          { label: 'Overdue',   value: stats.overdue,   icon: '🚨', cls: 'stat-overdue' },
        ].map(s => (
          <div key={s.label} className={`stat-card card ${s.cls}`}>
            <div className="stat-icon">{s.icon}</div>
            <div className="stat-value">{s.value ?? 0}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Task list */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        </div>
      ) : tasks.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>No tasks yet</h3>
          <p>Create your first task or convert a diary entry into one!</p>
          <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => setShowModal(true)}>
            ➕ Create Task
          </button>
        </div>
      ) : (
        <div className="task-list">
          {tasks.map(task => (
            <div key={task.id} className={`task-card card ${task.status === 'completed' ? 'task-done' : ''} ${isOverdue(task) ? 'task-overdue' : ''}`}>
              <div className="task-checkbox-wrap">
                <button
                  id={`task-toggle-${task.id}`}
                  className={`task-check ${task.status === 'completed' ? 'checked' : ''}`}
                  onClick={() => toggleStatus(task)}
                  title={task.status === 'completed' ? 'Mark pending' : 'Mark complete'}
                >
                  {task.status === 'completed' ? '✓' : ''}
                </button>
              </div>
              <div className="task-body">
                <div className="task-title-row">
                  <h3 className={`task-title ${task.status === 'completed' ? 'done' : ''}`}>{task.title}</h3>
                  <div className="task-badges">
                    <span className={`badge badge-${task.priority}`}>{PRIORITY_LABELS[task.priority]}</span>
                    <span className={`badge badge-${task.status}`}>{task.status === 'completed' ? '✅ Done' : '⏳ Pending'}</span>
                  </div>
                </div>
                {task.description && <p className="task-desc">{task.description}</p>}
                <div className="task-meta">
                  <span>📅 Created: {formatDate(task.created_at?.split('T')[0]) || task.created_at}</span>
                  {task.due_date && (
                    <span className={isOverdue(task) ? 'overdue-label' : ''}>
                      🔔 Due: {formatDate(task.due_date)}
                      {isOverdue(task) && ' (Overdue!)'}
                    </span>
                  )}
                </div>
              </div>
              <div className="task-actions">
                <button
                  id={`task-delete-${task.id}`}
                  className="btn btn-danger btn-sm"
                  onClick={() => deleteTask(task.id)}
                  title="Delete task"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowModal(false)}>
          <div className="modal">
            <div className="modal-header">
              <span className="modal-title">➕ New Task</span>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="form-group">
              <label>Title *</label>
              <input id="new-task-title" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="What needs to be done?" autoFocus />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Optional details..." rows={3} />
            </div>
            <div className="form-group">
              <label>Priority</label>
              <select value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}>
                <option value="low">🟢 Low</option>
                <option value="medium">🟡 Medium</option>
                <option value="high">🔴 High</option>
              </select>
            </div>
            <div className="form-group">
              <label>Due Date</label>
              <input type="date" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} />
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
              <button id="create-task-submit" className="btn btn-success" onClick={handleCreate} disabled={saving || !form.title.trim()}>
                {saving ? <><span className="spinner" /> Saving...</> : '✅ Create Task'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
