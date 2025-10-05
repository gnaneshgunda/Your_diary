class YourDiaryManager {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.suggestionsBox = document.getElementById('suggestions');
        this.sendBtn = document.getElementById('sendBtn');
        this.addTaskBtn = document.getElementById('addTaskBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.refreshSuggestionsBtn = document.getElementById('refreshSuggestionsBtn');
        this.suggestionTimeout = null;
        this.currentSuggestionLength = 20;
        this.initEventListeners();
        this.showWelcomeMessage();
    }

    showWelcomeMessage() {
        // Show a brief welcome animation
        if (this.messageInput) {
            setTimeout(() => {
                this.messageInput.placeholder = "Dear diary... Start writing and let AI help you express your thoughts!";
            }, 1000);
        }
    }

    initEventListeners() {
        if (this.messageInput) {
            this.messageInput.addEventListener('input', (e) => this.handleInput(e));
            this.messageInput.addEventListener('focus', () => {
                this.messageInput.style.transform = 'scale(1.01)';
            });
            this.messageInput.addEventListener('blur', () => {
                this.messageInput.style.transform = 'scale(1)';
            });
        }

        // Button event listeners
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.saveDiaryEntry());
        }

        if (this.addTaskBtn) {
            this.addTaskBtn.addEventListener('click', () => this.showTaskModal());
        }

        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.clearInput());
        }

        if (this.refreshSuggestionsBtn) {
            this.refreshSuggestionsBtn.addEventListener('click', () => this.refreshSuggestions());
        }

        // Suggestion length controls
        const lengthRadios = document.querySelectorAll('input[name="suggestionLength"]');
        lengthRadios.forEach(radio => {
            radio.addEventListener('change', (e) => this.handleLengthChange(e));
        });

        const customLengthSlider = document.getElementById('customLength');
        if (customLengthSlider) {
            customLengthSlider.addEventListener('input', (e) => {
                document.getElementById('customLengthValue').textContent = e.target.value;
                if (document.getElementById('lengthCustom').checked) {
                    this.currentSuggestionLength = parseInt(e.target.value);
                    this.refreshSuggestions();
                }
            });
        }

        // Task management events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('task-checkbox')) {
                this.toggleTaskStatus(e.target.dataset.taskId, e.target.checked);
            }

            if (e.target.classList.contains('delete-task')) {
                e.preventDefault();
                this.deleteTask(e.target.dataset.taskId);
            }

            if (e.target.classList.contains('convert-to-task')) {
                this.convertMessageToTask(e.target.dataset.message);
            }
        });

        // Modal handlers
        const saveTaskBtn = document.getElementById('saveTaskBtn');
        if (saveTaskBtn) {
            saveTaskBtn.addEventListener('click', () => this.saveTask());
        }

        const saveNewTaskBtn = document.getElementById('saveNewTaskBtn');
        if (saveNewTaskBtn) {
            saveNewTaskBtn.addEventListener('click', () => this.saveNewTask());
        }

        const saveConvertTaskBtn = document.getElementById('saveConvertTaskBtn');
        if (saveConvertTaskBtn) {
            saveConvertTaskBtn.addEventListener('click', () => this.saveConvertTask());
        }

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (this.messageInput && this.suggestionsBox &&
                !this.messageInput.contains(e.target) && 
                !this.suggestionsBox.contains(e.target)) {
                this.hideSuggestions();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter' && this.messageInput && document.activeElement === this.messageInput) {
                e.preventDefault();
                this.saveDiaryEntry();
            }
            if (e.key === 'Escape') {
                this.hideSuggestions();
            }
        });
    }

    handleLengthChange(e) {
        const value = e.target.value;
        const customContainer = document.getElementById('customLengthContainer');

        if (value === 'custom') {
            customContainer.style.display = 'block';
            this.currentSuggestionLength = parseInt(document.getElementById('customLength').value);
        } else {
            customContainer.style.display = 'none';
            if (value === '20') {
                this.currentSuggestionLength = 20;
            } else if (value === '30') {
                this.currentSuggestionLength = 30;
            } else if (value === 'sentence') {
                this.currentSuggestionLength = 'sentence';
            }
        }

        this.refreshSuggestions();
    }

    refreshSuggestions() {
        if (this.messageInput && this.messageInput.value.length >= 2) {
            this.getSuggestions(this.messageInput.value, true);
        }
    }

    handleInput(event) {
        clearTimeout(this.suggestionTimeout);
        const text = event.target.value;

        if (text.length < 2) {
            this.hideSuggestions();
            return;
        }

        this.showLoading();
        this.suggestionTimeout = setTimeout(() => this.getSuggestions(text), 400);
    }

    showLoading() {
        if (this.suggestionsBox) {
            this.suggestionsBox.innerHTML = '<div class="suggestion-item"><i class="bi bi-brain me-2"></i>YourDiary AI is thinking...</div>';
            this.showSuggestionsBox();
        }
    }

    async getSuggestions(text, isRefresh = false) {
        try {
            const requestData = {
                text: text,
                max_length: this.currentSuggestionLength,
                num_suggestions: isRefresh ? 5 : 3
            };

            const response = await fetch('/get_suggestions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(requestData)
            });

            const data = await response.json();

            if (data.suggestions && data.suggestions.length > 0) {
                this.displaySuggestions(data.suggestions);
            } else {
                this.showNoSuggestions();
            }
        } catch (error) {
            console.error('Error getting suggestions:', error);
            this.showNoSuggestions();
        }
    }

    displaySuggestions(suggestions) {
        if (!this.suggestionsBox) return;

        this.suggestionsBox.innerHTML = '';

        // Add header
        const headerDiv = document.createElement('div');
        headerDiv.className = 'suggestion-header';
        headerDiv.innerHTML = `<i class="bi bi-lightbulb me-2"></i>${suggestions.length} AI suggestions (${this.currentSuggestionLength === 'sentence' ? 'complete sentences' : this.currentSuggestionLength + ' chars'})`;
        this.suggestionsBox.appendChild(headerDiv);

        suggestions.forEach((suggestion, index) => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.innerHTML = `
                <div class="suggestion-text">${suggestion}</div>
                <small class="text-muted">${suggestion.length} chars</small>
            `;
            div.addEventListener('click', () => this.selectSuggestion(suggestion));
            this.suggestionsBox.appendChild(div);
        });

        this.showSuggestionsBox();
    }

    showNoSuggestions() {
        if (this.suggestionsBox) {
            this.suggestionsBox.innerHTML = '<div class="suggestion-item text-muted"><i class="bi bi-hourglass-split me-2"></i>Training AI for better suggestions...</div>';
            this.showSuggestionsBox();
            setTimeout(() => this.hideSuggestions(), 2500);
        }
    }

    showSuggestionsBox() {
        if (!this.messageInput || !this.suggestionsBox) return;

        const rect = this.messageInput.getBoundingClientRect();
        this.suggestionsBox.style.left = rect.left + 'px';
        this.suggestionsBox.style.top = (rect.top - Math.min(250, this.suggestionsBox.offsetHeight + 20)) + 'px';
        this.suggestionsBox.style.width = rect.width + 'px';
        this.suggestionsBox.style.display = 'block';
    }

    hideSuggestions() {
        if (this.suggestionsBox) {
            this.suggestionsBox.style.display = 'none';
        }
    }

    selectSuggestion(suggestion) {
        if (this.messageInput) {
            const cursorPos = this.messageInput.selectionStart;
            const textBefore = this.messageInput.value.substring(0, cursorPos);
            const textAfter = this.messageInput.value.substring(cursorPos);

            this.messageInput.value = textBefore + suggestion + textAfter;

            const newCursorPos = cursorPos + suggestion.length;
            this.messageInput.setSelectionRange(newCursorPos, newCursorPos);

            this.hideSuggestions();
            this.messageInput.focus();

            // Visual feedback
            this.messageInput.style.background = '#f0f9ff';
            setTimeout(() => {
                this.messageInput.style.background = '';
            }, 300);
        }
    }

    async saveDiaryEntry() {
        if (!this.messageInput) return;

        const message = this.messageInput.value.trim();
        if (!message) {
            this.showAlert('Please write something in your diary first! 📝', 'warning');
            return;
        }

        this.sendBtn.disabled = true;
        this.sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving & Training AI...';

        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            if (data.success) {
                this.clearInput();
                const trainingMsg = data.total_messages % 3 === 0 ? 
                    'Entry saved! 🧠 AI is learning from your writing style...' : 
                    `Entry saved! ${3 - (data.total_messages % 3)} more entries until next AI training.`;
                this.showAlert(trainingMsg, 'success');

                // Celebration animation
                this.celebrateEntry();
            }
        } catch (error) {
            this.showAlert('Failed to save entry. Please try again.', 'danger');
        } finally {
            this.sendBtn.disabled = false;
            this.sendBtn.innerHTML = '<i class="bi bi-journal-plus"></i> Save Entry';
        }
    }

    celebrateEntry() {
        // Brief success animation
        if (this.messageInput) {
            this.messageInput.style.background = '#dcfce7';
            setTimeout(() => {
                this.messageInput.style.background = '';
            }, 1000);
        }
    }

    showTaskModal() {
        if (!this.messageInput) return;

        const text = this.messageInput.value.trim();
        if (text) {
            document.getElementById('taskTitle').value = text.substring(0, 100);
            document.getElementById('taskDescription').value = text;
        }

        const modal = new bootstrap.Modal(document.getElementById('taskModal'));
        modal.show();
    }

    async saveTask() {
        const title = document.getElementById('taskTitle').value.trim();
        if (!title) {
            this.showAlert('Please enter a task title', 'warning');
            return;
        }

        const taskData = {
            title: title,
            description: document.getElementById('taskDescription').value.trim(),
            priority: document.getElementById('taskPriority').value,
            due_date: document.getElementById('taskDueDate').value
        };

        try {
            const response = await fetch('/add_task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(taskData)
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Task created successfully! ✅', 'success');
                this.clearInput();
                bootstrap.Modal.getInstance(document.getElementById('taskModal')).hide();
                setTimeout(() => window.location.reload(), 1000);
            }
        } catch (error) {
            this.showAlert('Error creating task', 'danger');
        }
    }

    async saveNewTask() {
        const title = document.getElementById('newTaskTitle').value.trim();
        if (!title) {
            this.showAlert('Please enter a task title', 'warning');
            return;
        }

        const taskData = {
            title: title,
            description: document.getElementById('newTaskDescription').value.trim(),
            priority: document.getElementById('newTaskPriority').value,
            due_date: document.getElementById('newTaskDueDate').value
        };

        try {
            const response = await fetch('/add_task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(taskData)
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Task created successfully! 📋', 'success');
                bootstrap.Modal.getInstance(document.getElementById('newTaskModal')).hide();
                setTimeout(() => window.location.reload(), 1000);
            }
        } catch (error) {
            this.showAlert('Error creating task', 'danger');
        }
    }

    async saveConvertTask() {
        const title = document.getElementById('convertTaskTitle').value.trim();
        if (!title) {
            this.showAlert('Please enter a task title', 'warning');
            return;
        }

        const taskData = {
            title: title,
            description: document.getElementById('convertTaskDescription').value.trim(),
            priority: document.getElementById('convertTaskPriority').value,
            due_date: document.getElementById('convertTaskDueDate').value
        };

        try {
            const response = await fetch('/add_task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(taskData)
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Diary entry converted to task! 🔄', 'success');
                bootstrap.Modal.getInstance(document.getElementById('convertTaskModal')).hide();
                setTimeout(() => window.location.reload(), 1000);
            }
        } catch (error) {
            this.showAlert('Error converting to task', 'danger');
        }
    }

    async toggleTaskStatus(taskId, completed) {
        try {
            const response = await fetch('/update_task_status', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ 
                    task_id: taskId, 
                    status: completed ? 'completed' : 'pending' 
                })
            });

            const data = await response.json();

            if (data.success) {
                const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
                if (taskCard) {
                    const title = taskCard.querySelector('.task-title');
                    const badge = taskCard.querySelector('.task-status');

                    if (completed) {
                        title.classList.add('text-decoration-line-through', 'text-muted');
                        badge.className = 'badge task-status bg-success';
                        badge.innerHTML = '<i class="bi bi-check-circle"></i> Complete';
                        taskCard.style.opacity = '0.7';
                    } else {
                        title.classList.remove('text-decoration-line-through', 'text-muted');
                        badge.className = 'badge task-status bg-warning text-dark';
                        badge.innerHTML = '<i class="bi bi-clock"></i> Pending';
                        taskCard.style.opacity = '1';
                    }
                }

                this.showAlert(completed ? 'Task completed! Great job! 🎉' : 'Task marked as pending 📝', 'success');
            }
        } catch (error) {
            this.showAlert('Error updating task', 'danger');
        }
    }

    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task? This action cannot be undone.')) return;

        try {
            const response = await fetch('/delete_task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ task_id: taskId })
            });

            const data = await response.json();

            if (data.success) {
                const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
                if (taskCard) {
                    taskCard.style.opacity = '0';
                    taskCard.style.transform = 'translateX(-100px)';
                    setTimeout(() => taskCard.remove(), 300);
                }
                this.showAlert('Task deleted successfully 🗑️', 'info');
            }
        } catch (error) {
            this.showAlert('Error deleting task', 'danger');
        }
    }

    convertMessageToTask(message) {
        document.getElementById('convertTaskTitle').value = message.substring(0, 100);
        document.getElementById('convertTaskDescription').value = message;
        const modal = new bootstrap.Modal(document.getElementById('convertTaskModal'));
        modal.show();
    }

    clearInput() {
        if (this.messageInput) {
            this.messageInput.value = '';
            this.hideSuggestions();
            this.messageInput.focus();

            // Reset placeholder
            this.messageInput.placeholder = "Dear diary... What's on your mind today?";
        }
    }

    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.style.borderRadius = '12px';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }
        }, 5000);
    }
}

// Initialize YourDiary when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new YourDiaryManager();

    // Add some nice loading animations
    const cards = document.querySelectorAll('.card, .diary-entry, .task-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});