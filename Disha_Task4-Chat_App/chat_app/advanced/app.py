"""
app.py — Advanced Tier Chat Application
=========================================
A web-based, multi-room chat app with login, message history, and
emoji shortcodes, built with Flask + Flask-SocketIO.

Why Flask-SocketIO instead of raw sockets here?
    The beginner tier already proves the raw-socket concept. For a
    GUI-ish, multi-room, many-user app, WebSockets (via Socket.IO)
    give us real-time push to a normal web page "for free" — no
    manual thread-per-client bookkeeping, and it naturally works in
    any browser without installing a GUI toolkit.

Run with:
    python app.py
Then open http://127.0.0.1:5000 in a browser (open it twice, or in
two different browsers / incognito windows, to chat with "yourself"
as two users on one machine).
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, join_room, leave_room, emit
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

import database as db
from emoji_support import render_emoji

app = Flask(__name__)
# In a real deployment this secret key should come from an environment
# variable, not be hard-coded. See README "Security notes".
app.config["SECRET_KEY"] = "dev-secret-key-change-me"

socketio = SocketIO(app)

db.init_db()


# ---------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------

def login_required(view):
    """Decorator: redirect to /login if the user has no active session."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------
# Routes: auth
# ---------------------------------------------------------------

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("rooms"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register"))

        # Passwords are hashed (salted) before ever touching the
        # database — see README for exactly what this does and
        # doesn't protect against.
        password_hash = generate_password_hash(password)
        success = db.create_user(username, password_hash)

        if not success:
            flash("That username is already taken.")
            return redirect(url_for("register"))

        flash("Account created! You can log in now.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = db.get_user(username)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.")
            return redirect(url_for("login"))

        session["username"] = username
        return redirect(url_for("rooms"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


# ---------------------------------------------------------------
# Routes: rooms
# ---------------------------------------------------------------

@app.route("/rooms", methods=["GET", "POST"])
@login_required
def rooms():
    if request.method == "POST":
        room_name = request.form.get("room_name", "").strip()
        if not room_name:
            flash("Room name can't be empty.")
        elif not db.create_room(room_name, session["username"]):
            flash("A room with that name already exists.")
        else:
            return redirect(url_for("chat", room_name=room_name))

    all_rooms = db.list_rooms()
    return render_template("rooms.html", rooms=all_rooms, username=session["username"])


@app.route("/chat/<room_name>")
@login_required
def chat(room_name):
    room = db.get_room(room_name)
    if room is None:
        flash("That room doesn't exist.")
        return redirect(url_for("rooms"))

    history = db.get_history(room["id"])
    return render_template(
        "chat.html",
        room_name=room_name,
        username=session["username"],
        history=history,
    )


# ---------------------------------------------------------------
# Socket.IO real-time events
# ---------------------------------------------------------------

@socketio.on("join")
def handle_join(data):
    """
    Client emits this right after loading a chat page. We put their
    socket connection into a Socket.IO "room" (a broadcast group)
    matching the chat room name, and announce their arrival.
    """
    username = session.get("username")
    room_name = data.get("room")
    if not username or not room_name:
        return

    room = db.get_room(room_name)
    if room is None:
        return

    join_room(room_name)
    emit(
        "system_message",
        {"text": f"{username} has joined the room."},
        room=room_name,
        include_self=False,
    )


@socketio.on("leave")
def handle_leave(data):
    username = session.get("username")
    room_name = data.get("room")
    if not username or not room_name:
        return

    leave_room(room_name)
    emit(
        "system_message",
        {"text": f"{username} has left the room."},
        room=room_name,
        include_self=False,
    )


@socketio.on("send_message")
def handle_send_message(data):
    """
    Core chat event: receive a message from one client, render any
    emoji shortcodes, persist it to SQLite (so it shows up in
    history for the next person who joins), then broadcast it to
    everyone currently in that room, including the sender (so their
    own message appears with the same timestamp everyone else sees).
    """
    username = session.get("username")
    room_name = data.get("room")
    text = (data.get("message") or "").strip()

    if not username or not room_name or not text:
        return

    room = db.get_room(room_name)
    if room is None:
        return

    text = render_emoji(text)
    timestamp = db.save_message(room["id"], username, text)

    emit(
        "new_message",
        {"username": username, "message": text, "timestamp": timestamp},
        room=room_name,
    )


if __name__ == "__main__":
    # allow_unsafe_werkzeug lets this run with `python app.py` directly
    # during development without a production WSGI server.
    socketio.run(app, host="127.0.0.1", port=5000, debug=True, allow_unsafe_werkzeug=True)
