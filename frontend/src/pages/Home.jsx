import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import './Home.css';

const LENGTHS = [
  { id: 'short',    label: 'Short',    value: 20 },
  { id: 'medium',   label: 'Medium',   value: 30 },
  { id: 'sentence', label: 'Full Sentence', value: 'sentence' },
  { id: 'custom',   label: 'Custom',   value: 'custom' },
];

export default function Home() {
  const { user } = useAuth();
  const [text, setText] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [lengthMode, setLengthMode] = useState('short');
  const [customLen, setCustomLen] = useState(40);
  const [loadingSugg, setLoadingSugg] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [taskForm, setTaskForm] = useState({ title: '', description: '', priority: 'medium', due_date: '' });
  const [savingTask, setSavingTask] = useState(false);
  const debounceRef = useRef(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const getMaxLength = () => {
    if (lengthMode === 'sentence') return 'sentence';
    if (lengthMode === 'custom') return customLen;
    return LENGTHS.find(l => l.id === lengthMode)?.value || 20;
  };

  const fetchSuggestions = useCallback(async (currentText) => {
    if (currentText.length < 3) { setSuggestions([]); return; }
    setLoadingSugg(true);
    try {
      const { data } = await api.post('/api/diary/suggestions', {
        text: currentText,
        max_length: getMaxLength(),
        num_suggestions: 3,
      });
      setSuggestions(data.suggestions || []);
    } catch { setSuggestions([]); }
    finally { setLoadingSugg(false); }
  }, [lengthMode, customLen]); // eslint-disable-line

  const handleTextChange = (e) => {
    const val = e.target.value;
    setText(val);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(val), 600);
  };

  const applySuggestion = (s) => {
    setText(prev => prev + s);
    setSuggestions([]);
  };

  const handleSave = async () => {
    if (!text.trim()) return;
    setSaving(true);
    try {
      await api.post('/api/diary/entry', { message: text.trim() });
      showToast('✅ Entry saved to your diary!');
      setText('');
      setSuggestions([]);
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to save entry', 'error');
    } finally { setSaving(false); }
  };

  const handleAddTask = async () => {
    if (!taskForm.title.trim()) return;
    setSavingTask(true);
    try {
      await api.post('/api/tasks', taskForm);
      showToast('✅ Task created!');
      setShowTaskModal(false);
      setTaskForm({ title: '', description: '', priority: 'medium', due_date: '' });
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create task', 'error');
    } finally { setSavingTask(false); }
  };

  const openTaskModal = () => {
    setTaskForm(f => ({ ...f, title: text.trim().slice(0, 80) }));
    setShowTaskModal(true);
  };

  useEffect(() => () => clearTimeout(debounceRef.current), []);

  return (
    <div className="page home-page">
      {toast && (
        <div className={`toast toast-${toast.type}`}>{toast.msg}</div>
      )}

      {/* Header */}
      <div className="home-header">
        <div>
          <h1 className="page-title">✍️ Smart Writing</h1>
          <p className="page-subtitle">Welcome back, <strong>{user?.username}</strong> — your AI assistant is ready</p>
        </div>
        <div className="home-header-actions">
          <button id="refresh-suggestions-btn" className="btn btn-ghost btn-sm" onClick={() => fetchSuggestions(text)}>
            🔄 Refresh AI
          </button>
        </div>
      </div>

      {/* Main card */}
      <div className="card write-card">
        {/* Length selector */}
        <div className="length-selector">
          <span className="length-label">Suggestion length:</span>
          <div className="length-pills">
            {LENGTHS.map(l => (
              <button
                key={l.id}
                id={`length-${l.id}`}
                className={`pill ${lengthMode === l.id ? 'pill-active' : ''}`}
                onClick={() => setLengthMode(l.id)}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>

        {lengthMode === 'custom' && (
          <div className="custom-length">
            <label>Custom length: <strong>{customLen}</strong> chars</label>
            <input
              type="range" min={10} max={100} value={customLen}
              onChange={e => setCustomLen(Number(e.target.value))}
              className="range-input"
            />
          </div>
        )}

        {/* Suggestions */}
        {(suggestions.length > 0 || loadingSugg) && (
          <div className="suggestions-box">
            <div className="suggestions-header">
              <span>🧠 AI Suggestions</span>
              {loadingSugg && <span className="spinner" />}
            </div>
            {suggestions.map((s, i) => (
              <button key={i} className="suggestion-chip" onClick={() => applySuggestion(s)}>
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Textarea */}
        <div className="form-group">
          <label>Your thoughts</label>
          <textarea
            id="diary-textarea"
            className="diary-textarea"
            rows={8}
            placeholder="Dear diary... start writing and watch AI suggestions appear above ✨"
            value={text}
            onChange={handleTextChange}
            onKeyDown={e => { if (e.ctrlKey && e.key === 'Enter') handleSave(); }}
          />
          <small className="textarea-hint">
            💡 <kbd>Ctrl+Enter</kbd> to save quickly · Your LSTM AI learns your style with every entry
          </small>
        </div>

        {/* Actions */}
        <div className="write-actions">
          <button id="save-entry-btn" className="btn btn-primary" onClick={handleSave} disabled={saving || !text.trim()}>
            {saving ? <><span className="spinner" /> Saving...</> : '📔 Save Entry'}
          </button>
          <button id="add-task-btn" className="btn btn-success" onClick={openTaskModal} disabled={!text.trim()}>
            ✅ Add as Task
          </button>
          <button id="clear-btn" className="btn btn-ghost" onClick={() => { setText(''); setSuggestions([]); }}>
            🗑️ Clear
          </button>
        </div>
      </div>

      {/* Features */}
      <div className="features-grid">
        <div className="feature-card card">
          <div className="feature-icon">🧠</div>
          <h3>Personal LSTM AI</h3>
          <p>Your neural network learns your unique writing style. Improves automatically every 3 entries.</p>
        </div>
        <div className="feature-card card">
          <div className="feature-icon">✅</div>
          <h3>Task Integration</h3>
          <p>Turn your diary thoughts into actionable tasks with priorities, due dates, and progress tracking.</p>
        </div>
        <div className="feature-card card">
          <div className="feature-icon">🔒</div>
          <h3>Private & Secure</h3>
          <p>Your AI model is personal — never shared. All data is secured with JWT authentication.</p>
        </div>
      </div>

      {/* Add Task Modal */}
      {showTaskModal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowTaskModal(false)}>
          <div className="modal">
            <div className="modal-header">
              <span className="modal-title">✅ Create New Task</span>
              <button className="modal-close" onClick={() => setShowTaskModal(false)}>×</button>
            </div>
            <div className="form-group">
              <label>Title</label>
              <input id="task-title-input" value={taskForm.title} onChange={e => setTaskForm(f => ({ ...f, title: e.target.value }))} placeholder="Task title" />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea value={taskForm.description} onChange={e => setTaskForm(f => ({ ...f, description: e.target.value }))} placeholder="Optional description" rows={3} />
            </div>
            <div className="form-group">
              <label>Priority</label>
              <select value={taskForm.priority} onChange={e => setTaskForm(f => ({ ...f, priority: e.target.value }))}>
                <option value="low">🟢 Low</option>
                <option value="medium">🟡 Medium</option>
                <option value="high">🔴 High</option>
              </select>
            </div>
            <div className="form-group">
              <label>Due Date</label>
              <input type="date" value={taskForm.due_date} onChange={e => setTaskForm(f => ({ ...f, due_date: e.target.value }))} />
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => setShowTaskModal(false)}>Cancel</button>
              <button id="save-task-btn" className="btn btn-success" onClick={handleAddTask} disabled={savingTask || !taskForm.title.trim()}>
                {savingTask ? <><span className="spinner" /> Saving...</> : '✅ Create Task'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
