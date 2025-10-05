from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import datetime
from models.database import (init_db, get_user_messages, save_message, get_user_by_username, 
                           create_user, add_task, get_user_tasks, update_task_status, 
                           delete_task, get_task_stats)
from models.lstm_model import LSTMModelManager

app = Flask(__name__)
app.secret_key = 'yourdiary-secret-key-change-in-production'
model_manager = LSTMModelManager()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/diary')
def diary():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_messages = get_user_messages(session['user_id'])
    return render_template('diary.html', messages=user_messages)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = username
            flash(f'Welcome back to YourDiary, {username}! Your AI assistant is ready to help you write.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'warning')
        elif len(password) < 4:
            flash('Password must be at least 4 characters long', 'warning')
        elif create_user(username, password):
            flash(f'Welcome to YourDiary, {username}! Your personal AI writing assistant is being initialized.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists. Please choose a different one.', 'danger')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye {username}! Your diary entries are safely saved.', 'info')
    return redirect(url_for('login'))

@app.route('/tasks')
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_tasks = get_user_tasks(session['user_id'])
    stats = get_task_stats(session['user_id'])
    return render_template('tasks.html', tasks=user_tasks, stats=stats)

@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_messages = get_user_messages(session['user_id'])
    return render_template('messages.html', messages=user_messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    message = request.json.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Empty message'}), 400

    save_message(session['user_id'], message)
    recent_messages = get_user_messages(session['user_id'], limit=10)
    message_texts = [msg[0] for msg in recent_messages]

    total_messages = len(get_user_messages(session['user_id']))
    if total_messages % 3 == 0 and total_messages > 0:
        print(f"🎯 YourDiary: Training AI for user {session['user_id']} after {total_messages} entries")
        thread = threading.Thread(
            target=model_manager.train_user_model_background, 
            args=(session['user_id'], message_texts)
        )
        thread.daemon = True
        thread.start()

    return jsonify({'success': True, 'total_messages': total_messages})

@app.route('/add_task', methods=['POST'])
def add_task_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    priority = data.get('priority', 'medium')
    due_date = data.get('due_date', '')

    if not title:
        return jsonify({'error': 'Title required'}), 400

    if add_task(session['user_id'], title, description, priority, due_date):
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to add task'}), 500

@app.route('/update_task_status', methods=['POST'])
def update_task_status_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    task_id = request.json.get('task_id')
    status = request.json.get('status')

    if update_task_status(task_id, status, session['user_id']):
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to update task'}), 500

@app.route('/delete_task', methods=['POST'])
def delete_task_route():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    task_id = request.json.get('task_id')

    if delete_task(task_id, session['user_id']):
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to delete task'}), 500

@app.route('/get_suggestions', methods=['POST'])
def get_suggestions():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json
    text = data.get('text', '')
    max_length = data.get('max_length', 20)
    num_suggestions = data.get('num_suggestions', 3)

    if len(text) < 2:
        return jsonify({'suggestions': []})

    try:
        print(f"🧠 YourDiary AI: Generating suggestions for user {session['user_id']}")
        user_model = model_manager.get_user_model(session['user_id'])

        # Handle different length options
        if max_length == 'sentence':
            suggestions = user_model.get_completions_till_period(text, num_suggestions=num_suggestions)
        else:
            max_len = int(max_length) if isinstance(max_length, (str, int)) else 20
            suggestions = user_model.get_completions(text, num_suggestions=num_suggestions, max_length=max_len)

        print(f"✅ YourDiary AI: Generated {len(suggestions)} suggestions")
        return jsonify({'suggestions': suggestions})
    except Exception as e:
        print(f"❌ YourDiary AI Error: {e}")
        # Return thoughtful fallback suggestions
        fallback_suggestions = [
            ' feels meaningful to me',
            ' brings me joy',
            ' is something I want to remember'
        ]
        return jsonify({'suggestions': fallback_suggestions[:num_suggestions]})

if __name__ == '__main__':
    print("🌟 Starting YourDiary - Your Personal AI Writing Assistant")
    print("📖 Features: AI-powered diary + smart suggestions + task management")
    print("🧠 LSTM neural network learns your unique writing style")
    print("✨ Customizable suggestion lengths for perfect writing flow")
    init_db()
    model_manager.load_base_model()
    print("📝 YourDiary is ready at: http://localhost:5000")
    print("💫 Write your first entry and watch the AI learn your style!")
    app.run(debug=True, port=5000, host='0.0.0.0')
