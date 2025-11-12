from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import psutil
import time
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fullname TEXT NOT NULL,
                        email TEXT NOT NULL,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        action TEXT,
                        timestamp TEXT
                      )''')
    conn.commit()
    conn.close()

init_db()

# Routes
@app.route('/')
def home():
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = username
            log_activity(username, "logged in")
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/create-account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (fullname, email, username, password) VALUES (?, ?, ?, ?)",
                           (fullname, email, username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login_page'))
        except sqlite3.IntegrityError:
            return render_template('create-account.html', error="Username already exists.")
    return render_template('create-account.html')

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    username = session.get('username')
    if username:
        log_activity(username, "logged out")
    session.pop('username', None)
    return redirect(url_for('login_page'))

# System Data
@app.route('/system_data')
def system_data():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    net = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    return jsonify({
        'cpu': cpu,
        'ram': ram,
        'disk': disk,
        'net': net,
        'time': time.strftime("%H:%M:%S")
    })

# Activity Log
def log_activity(username, action):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (username, action, timestamp) VALUES (?, ?, ?)",
                   (username, action, time.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

@app.route('/activity_log')
def activity_log():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, action, timestamp FROM logs ORDER BY id DESC LIMIT 10")
    logs = cursor.fetchall()
    conn.close()
    return jsonify(logs)

if __name__ == '__main__':
    app.run(debug=True)
