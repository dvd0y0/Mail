
from flask import Flask, render_template, request, redirect, session
from cryptography.fernet import Fernet
from functools import wraps
from datetime import datetime
import hashlib
import json
import uuid
import os

app = Flask(__name__)
app.secret_key = "secret_key"

DATA_FILE = "data.txt"
PASS_FILE = "pass.txt"

SECRET_KEY = b"6OLg-wRZtaxYEzffKY0ahPz_6q3_WQjAkk_J8HWQhnQ="
fernet = Fernet(SECRET_KEY)

def get_password():
    with open(PASS_FILE, "r") as f:
        return f.read().strip()

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin")
        return f(*args, **kwargs)
    return wrapper

def load_messages():

    messages = []

    if not os.path.exists(DATA_FILE):
        return messages

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:

        try:
            data = json.loads(line.strip())

            try:
                decrypted = fernet.decrypt(
                    data["message"].encode()
                ).decode()
            except:
                decrypted = data["message"]

            messages.append({
                "id": data["id"],
                "name": data["name"],
                "message": decrypted,
                "photo": data["photo"],
                "date": data["date"],
                "ip": data["ip"]
            })

        except Exception as e:
            print(e)

    return messages[::-1]

def save_message(name, message, photo, ip):

    encrypted = fernet.encrypt(
        message.encode()
    ).decode()

    data = {
        "id": str(uuid.uuid4()),
        "name": name,
        "message": encrypted,
        "photo": photo,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "ip": ip
    }

    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

@app.route("/", methods=["GET", "POST"])
def index():

    success = False

    if request.method == "POST":

        save_message(
            request.form.get("name"),
            request.form.get("message"),
            request.form.get("photo"),
            request.remote_addr
        )

        success = True

    return render_template(
        "index.html",
        success=success
    )

@app.route("/admin", methods=["GET", "POST"])
def admin():

    error = None

    if request.method == "POST":

        password = request.form.get("password")

        hashed = hashlib.sha256(
            password.encode()
        ).hexdigest()

        if hashed == get_password():

            session["admin"] = True

        else:
            error = "Неверный пароль"

    messages = []

    if session.get("admin"):
        messages = load_messages()

    return render_template(
        "index2.html",
        messages=messages,
        error=error
    )

@app.route("/delete/<message_id>", methods=["POST"])
@admin_required
def delete_message(message_id):

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []

    for line in lines:

        try:
            data = json.loads(line.strip())

            if data["id"] != message_id:
                new_lines.append(line)

        except:
            continue

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
