from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key"

DB_NAME = "messages.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT,
        date TEXT,
        name TEXT,
        message TEXT,
        photo TEXT
    )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_hash():
    with open("pass.txt","r") as f:
        return f.read().strip()

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        ip = request.remote_addr
        today = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM messages WHERE ip=? AND date LIKE ?", (ip, f"{today}%"))
        count = c.fetchone()[0]

        if count >= 3:
            conn.close()
            return render_template("index.html", error="Лимит 3 сообщения в сутки!")

        name = request.form["name"]
        message = request.form["message"]
        photo = request.form["photo"]

        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute(
            "INSERT INTO messages (ip,date,name,message,photo) VALUES (?,?,?,?,?)",
            (ip,date,name,message,photo)
        )

        conn.commit()
        conn.close()

        return render_template("index.html", success=True)

    return render_template("index.html")

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        password = request.form["password"]
        hashed = hashlib.sha256(password.encode()).hexdigest()

        if hashed == get_hash():
            session["admin"] = True
            return redirect("/dashboard")

    return '''
    <form method="POST">
    <input type="password" name="password" placeholder="Password">
    <button type="submit">Login</button>
    </form>
    '''

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM messages ORDER BY id DESC")
    messages = c.fetchall()
    conn.close()

    return render_template("index2.html", messages=messages)

if __name__ == "__main__":
    app.run(debug=True)
