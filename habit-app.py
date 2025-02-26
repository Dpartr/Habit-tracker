from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "habit_tracker_secret_key"  # Required for flash messages

# Database functions
def get_db_connection():
    conn = sqlite3.connect('habit_tracker.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

# Check if column exists in table
def column_exists(conn, table_name, column_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(column['name'] == column_name for column in columns)

# Initialize the database
def init_db():
    # Check if the database file exists
    db_exists = os.path.exists('habit_tracker.db')
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY,
                    description TEXT,
                    amount REAL
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    habit_id INTEGER,
                    amount REAL,
                    quantity INTEGER DEFAULT 1,
                    date TEXT,
                    bounty_description TEXT DEFAULT NULL,
                    FOREIGN KEY (habit_id) REFERENCES habits (id)
                )''')
    
    # New table for bounties
    c.execute('''CREATE TABLE IF NOT EXISTS bounties (
                    id INTEGER PRIMARY KEY,
                    description TEXT,
                    amount REAL,
                    date_created TEXT,
                    completed INTEGER DEFAULT 0
                )''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    habits = conn.execute('SELECT id, description, amount FROM habits').fetchall()
    
    # Calculate total balance
    balance_row = conn.execute('SELECT SUM(amount * quantity) as total FROM transactions').fetchone()
    balance = balance_row['total'] if balance_row['total'] else 0
    
    # Get recent transactions with proper bounty descriptions
    transactions = conn.execute('''
        SELECT 
            t.id, 
            t.date, 
            t.amount, 
            t.quantity, 
            (t.amount * t.quantity) as total_amount, 
            CASE 
                WHEN t.habit_id = -1 THEN t.bounty_description
                ELSE h.description 
            END as description,
            t.habit_id
        FROM transactions t
        LEFT JOIN habits h ON t.habit_id = h.id
        ORDER BY t.id DESC LIMIT 10
    ''').fetchall()
    
    # Get active bounties
    bounties = conn.execute('''
        SELECT id, description, amount, date_created
        FROM bounties
        WHERE completed = 0
        ORDER BY id DESC
    ''').fetchall()
    
    conn.close()
    return render_template('index.html', habits=habits, balance=balance, 
                           transactions=transactions, bounties=bounties)

@app.route('/add_habit', methods=['POST'])
def add_habit():
    description = request.form.get('description')
    
    try:
        amount = float(request.form.get('amount'))
    except ValueError:
        flash('Please enter a valid amount', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    conn.execute('INSERT INTO habits (description, amount) VALUES (?, ?)', 
                (description, amount))
    conn.commit()
    conn.close()
    
    flash('Habit added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    habit_id = request.form.get('habit_id')
    
    try:
        amount = float(request.form.get('amount'))
        quantity = int(request.form.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except ValueError:
        flash('Please enter valid values', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    conn.execute('INSERT INTO transactions (habit_id, amount, quantity, date) VALUES (?, ?, ?, ?)', 
                (habit_id, amount, quantity, datetime.now().strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()
    
    flash(f'Transaction added successfully! ({quantity}x)', 'success')
    return redirect(url_for('index'))

@app.route('/add_bounty', methods=['POST'])
def add_bounty():
    description = request.form.get('description')
    
    try:
        amount = float(request.form.get('amount'))
    except ValueError:
        flash('Please enter a valid amount', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    conn.execute('INSERT INTO bounties (description, amount, date_created, completed) VALUES (?, ?, ?, 0)', 
                (description, amount, datetime.now().strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()
    
    flash('Bounty added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/complete_bounty/<int:bounty_id>', methods=['POST'])
def complete_bounty(bounty_id):
    conn = get_db_connection()
    
    # Get the bounty details
    bounty = conn.execute('SELECT id, description, amount FROM bounties WHERE id = ?', 
                         (bounty_id,)).fetchone()
    
    if not bounty:
        flash('Bounty not found', 'error')
        return redirect(url_for('index'))
    
    # Mark the bounty as completed
    conn.execute('UPDATE bounties SET completed = 1 WHERE id = ?', (bounty_id,))
    
    # Add the bounty amount to transactions with the bounty description
    conn.execute('''
        INSERT INTO transactions 
        (habit_id, amount, quantity, date, bounty_description) 
        VALUES (-1, ?, 1, ?, ?)
    ''', (bounty['amount'], datetime.now().strftime('%Y-%m-%d'), bounty['description']))
    
    conn.commit()
    conn.close()
    
    flash(f'Bounty completed: ${bounty["amount"]:.2f} added to balance!', 'success')
    return redirect(url_for('index'))

@app.route('/toggle_theme', methods=['POST'])
def toggle_theme():
    # This endpoint is called by AJAX to store the theme preference
    # It doesn't actually do anything server-side, just responds
    return jsonify({"status": "success"})

# Create templates directory and templates
@app.route('/create_templates')
def create_templates():
    import os
    
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Write the index.html template
    with open('templates/index.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Habit Tracker</title>
    <style>
        :root {
            --bg-color: #ffffff;
            --text-color: #333333;
            --card-bg: #f9f9f9;
            --border-color: #dddddd;
            --accent-color: #4CAF50;
            --accent-hover: #3e8e41;
            --success-bg: #dff0d8;
            --success-color: #3c763d;
            --error-bg: #f2dede;
            --error-color: #a94442;
            --button-text: white;
            --header-color: #4CAF50;
            --hint-color: #888888;
        }

        [data-theme="dark"] {
            --bg-color: #1a1a1a;
            --text-color: #f0f0f0;
            --card-bg: #2d2d2d;
            --border-color: #444444;
            --accent-color: #5cb85c;
            --accent-hover: #4cae4c;
            --success-bg: #2d4116;
            --success-color: #5cb85c;
            --error-bg: #4a1919;
            --error-color: #d9534f;
            --button-text: #f0f0f0;
            --header-color: #5cb85c;
            --hint-color: #aaaaaa;
        }

        body {
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: all 0.3s ease;
        }

        .theme-toggle {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            align-items: center;
        }

        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 30px;
            margin-left: 10px;
        }

        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 30px;
        }

        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 22px;
            width: 22px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }

        input:checked + .toggle-slider {
            background-color: var(--accent-color);
        }

        input:checked + .toggle-slider:before {
            transform: translateX(30px);
        }

        .container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }

        .section {
            flex: 1;
            min-width: 300px;
            border: 1px solid var(--border-color);
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            background-color: var(--card-bg);
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        h1, h2 {
            color: var(--header-color);
        }

        .balance {
            font-size: 1.5em;
            font-weight: bold;
            margin: 20px 0;
            color: var(--accent-color);
        }

        .hint-text {
            color: var(--hint-color);
            font-size: 0.9em;
            margin-top: 5px;
        }

        .habit-list, .transaction-list, .bounty-list {
            list-style-type: none;
            padding: 0;
        }

        .habit-item, .transaction-item, .bounty-item {
            padding: 10px;
            margin-bottom: 10px;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 3px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .habit-info {
            flex: 1;
        }

        .habit-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        form {
            margin-top: 10px;
        }

        label {
            display: block;
            margin: 5px 0;
        }

        input, select, button {
            padding: 8px;
            margin: 5px 0;
            width: 100%;
            box-sizing: border-box;
            border-radius: 3px;
            border: 1px solid var(--border-color);
            background-color: var(--card-bg);
            color: var(--text-color);
        }

        button {
            background-color: var(--accent-color);
            color: var(--button-text);
            border: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        button:hover {
            background-color: var(--accent-hover);
        }

        .quantity-input {
            width: 60px;
            margin: 0 5px;
        }

        .quick-log {
            width: auto;
            padding: 5px 10px;
            white-space: nowrap;
        }

        .messages {
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 3px;
        }

        .success {
            background-color: var(--success-bg);
            color: var(--success-color);
        }

        .error {
            background-color: var(--error-bg);
            color: var(--error-color);
        }

        .complete-button {
            background-color: #5bc0de;
        }

        .complete-button:hover {
            background-color: #46b8da;
        }

        @media (max-width: 768px) {
            .section {
                min-width: 100%;
            }
        }
    </style>
</head>
<body>
    <h1>Habit Tracker</h1>

    <div class="theme-toggle">
        <span id="theme-label">Light</span>
        <label class="toggle-switch">
            <input type="checkbox" id="theme-toggle">
            <span class="toggle-slider"></span>
        </label>
    </div>

    {% if get_flashed_messages() %}
        {% for category, message in get_flashed_messages(with_categories=true) %}
        <div class="messages {{ category }}">
            {{ message }}
        </div>
        {% endfor %}
    {% endif %}

    <div class="balance">
        Balance: ${{ "%.2f"|format(balance) }}
    </div>

    <div class="container">
        <div class="section">
            <h2>Add New Habit</h2>
            <form action="{{ url_for('add_habit') }}" method="post">
                <div>
                    <label for="description">Habit Description:</label>
                    <input type="text" id="description" name="description" required placeholder="e.g., Exercise 30 minutes">
                    <div class="hint-text">Describe the activity you want to track regularly</div>
                </div>
                <div>
                    <label for="amount">Dollar Amount:</label>
                    <input type="number" id="amount" name="amount" step="0.01" required placeholder="e.g., 5.00">
                    <div class="hint-text">Reward amount for each completion</div>
                </div>
                <button type="submit">Add Habit</button>
            </form>
        </div>

        <div class="section">
            <h2>Your Habits</h2>
            {% if habits %}
                <ul class="habit-list">
                {% for habit in habits %}
                    <li class="habit-item">
                        <div class="habit-info">
                            <strong>{{ habit['description'] }}</strong>
                            <div>${{ "%.2f"|format(habit['amount']) }} per completion</div>
                        </div>
                        <div class="habit-actions">
                            <form action="{{ url_for('add_transaction') }}" method="post" style="margin: 0; display: flex; align-items: center;">
                                <input type="hidden" name="habit_id" value="{{ habit['id'] }}">
                                <input type="hidden" name="amount" value="{{ habit['amount'] }}">
                                <input type="number" name="quantity" class="quantity-input" value="1" min="1" max="100">
                                <span>×</span>
                                <button type="submit" class="quick-log">Complete</button>
                            </form>
                        </div>
                    </li>
                {% endfor %}
                </ul>
            {% else %}
                <p>No habits added yet. Add your first habit!</p>
            {% endif %}
        </div>
    </div>

    <div class="container">
        <div class="section">
            <h2>Add Bounty</h2>
            <form action="{{ url_for('add_bounty') }}" method="post">
                <div>
                    <label for="bounty_description">Bounty Description:</label>
                    <input type="text" id="bounty_description" name="description" required placeholder="e.g., Deep clean my room">
                    <div class="hint-text">A one-time task you want to complete</div>
                </div>
                <div>
                    <label for="bounty_amount">Reward Amount:</label>
                    <input type="number" id="bounty_amount" name="amount" step="0.01" required placeholder="e.g., 10.00">
                    <div class="hint-text">How much you'll reward yourself when completed</div>
                </div>
                <button type="submit">Create Bounty</button>
            </form>
        </div>

        <div class="section">
            <h2>Bounty Board</h2>
            {% if bounties %}
                <ul class="bounty-list">
                {% for bounty in bounties %}
                    <li class="bounty-item">
                        <div class="habit-info">
                            <strong>{{ bounty['description'] }}</strong>
                            <div>Reward: ${{ "%.2f"|format(bounty['amount']) }}</div>
                            <div><small>Created: {{ bounty['date_created'] }}</small></div>
                        </div>
                        <form action="{{ url_for('complete_bounty', bounty_id=bounty['id']) }}" method="post">
                            <button type="submit" class="complete-button">Complete</button>
                        </form>
                    </li>
                {% endfor %}
                </ul>
            {% else %}
                <p>No active bounties. Add a bounty to motivate yourself!</p>
            {% endif %}
        </div>
    </div>

    <div class="section">
        <h2>Recent Transactions</h2>
        {% if transactions %}
            <ul class="transaction-list">
            {% for transaction in transactions %}
                <li class="transaction-item">
                    <strong>{{ transaction['description'] }}</strong>: 
                    {% if transaction['habit_id'] == -1 %}
                        <span>Bounty Completed: ${{ "%.2f"|format(transaction['amount']) }}</span>
                    {% else %}
                        <span>${{ "%.2f"|format(transaction['amount']) }} × {{ transaction['quantity'] }} = ${{ "%.2f"|format(transaction['total_amount']) }}</span>
                    {% endif %}
                    <div><small>{{ transaction['date'] }}</small></div>
                </li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No transactions yet. Complete habits or bounties!</p>
        {% endif %}
    </div>

    <script>
        // Dark mode toggle functionality
        document.addEventListener('DOMContentLoaded', function() {
            const toggleSwitch = document.getElementById('theme-toggle');
            const themeLabel = document.getElementById('theme-label');
            
            // Function to set the theme
            function setTheme(isDark) {
                if (isDark) {
                    document.documentElement.setAttribute('data-theme', 'dark');
                    themeLabel.textContent = 'Dark';
                    toggleSwitch.checked = true;
                } else {
                    document.documentElement.setAttribute('data-theme', 'light');
                    themeLabel.textContent = 'Light';
                    toggleSwitch.checked = false;
                }
                // Save preference to localStorage
                localStorage.setItem('dark-mode', isDark ? 'dark' : 'light');
            }
            
            // Check for saved preference or OS preference
            const savedTheme = localStorage.getItem('dark-mode');
            if (savedTheme) {
                setTheme(savedTheme === 'dark');
            } else {
                // Check OS preference
                const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
                setTheme(prefersDarkMode);
            }
            
            // Toggle event
            toggleSwitch.addEventListener('change', function(e) {
                setTheme(e.target.checked);
                
                // Optional: Send preference to server
                fetch('/toggle_theme', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ theme: e.target.checked ? 'dark' : 'light' }),
                });
            });
            
            // Listen for OS theme changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
                // Only change if user hasn't set a preference
                if (!localStorage.getItem('dark-mode')) {
                    setTheme(e.matches);
                }
            });
        });
    </script>
</body>
</html>''')
    
    return "Templates created. You can now run the app."

if __name__ == '__main__':
    import os
    
    # Check if templates directory exists, if not create it and templates
    if not os.path.exists('templates'):
        create_templates()
        print("Created templates directory and index.html")
    
    app.run(debug=True)