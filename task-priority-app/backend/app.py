from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # for session management


def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )''')

    # Tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task TEXT,
        urgency INTEGER,
        due_in INTEGER,
        completion INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()

# -------------------- ROUTES -------------------- #

@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            flash("Signup successful! Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already exists!", "danger")
        conn.close()

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password_input):
            session['user_id'] = user[0]
            session['name'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "danger")

    return render_template('login.html')


@app.route('/create-task', methods=['GET', 'POST'])
def create_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        task = request.form['task']
        urgency = int(request.form['urgency'])
        due_in = int(request.form['due_in'])
        completion = int(request.form['completion'])

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO tasks (user_id, task, urgency, due_in, completion) VALUES (?, ?, ?, ?, ?)",
                  (session['user_id'], task, urgency, due_in, completion))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    return render_template('create_task.html', name=session['name'])


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT task, urgency, due_in, completion FROM tasks WHERE user_id = ?", (session['user_id'],))
    rows = c.fetchall()
    conn.close()

    def get_priority_class(urgency, due_in, completion):
        score = urgency * 2 + max(0, 10 - due_in) - completion / 10
        if score > 12:
            return 'high'
        elif score > 6:
            return 'medium'
        else:
            return 'low'

    tasks = []
    for row in rows:
        priority = get_priority_class(row[1], row[2], row[3])
        tasks.append({
            'task': row[0],
            'urgency': row[1],
            'due_in': row[2],
            'completion': row[3],
            'priority': priority
        })

    return render_template('dashboard.html', name=session['name'], tasks=tasks)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# -------------------- RUN -------------------- #
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
