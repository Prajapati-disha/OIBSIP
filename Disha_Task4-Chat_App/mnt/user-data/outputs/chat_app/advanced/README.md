# Chat App — Advanced Tier (Flask-SocketIO web app)

A multi-room, multi-user web chat with login, persistent history,
desktop notifications, and emoji shortcode support. Includes all
Beginner Tier features plus everything below.

## Feature checklist

- [x] GUI chat window — served as a web app using Flask (+ Socket.IO for real-time push)
- [x] User registration and login (username + password, stored in SQLite, passwords hashed)
- [x] Multiple chat rooms: users can create or join named rooms
- [x] Message history: past messages in a room load automatically when a user joins
- [x] Desktop notification for new messages when the window is not focused
- [x] Emoji support: `:smile:`, `:fire:`, `:thumbsup:`, etc. render as real Unicode emoji
- [x] Security transparency section (below) documenting storage and encryption status
- [x] (Beginner) Real-time bidirectional messaging, timestamps, graceful disconnect notices, localhost-friendly

## Project structure

```
advanced/
├── app.py                 # Flask app + Socket.IO event handlers (the "server")
├── database.py             # All SQLite reads/writes live here
├── emoji_support.py        # :shortcode: -> 🙂 conversion
├── requirements.txt
├── chat.db                 # created automatically on first run
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── rooms.html
│   └── chat.html
└── static/
    ├── css/style.css
    └── js/chat.js           # Socket.IO client, sending/receiving, notifications
```

## Setup & run

1. Create and activate a virtual environment (recommended):
   ```bash
   py -m venv .venv
   .venv\Scripts\Activate.ps1        # Windows PowerShell
   # source .venv/bin/activate       # macOS/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Open **http://127.0.0.1:5000** in your browser. To test chat with
   "two people," open a second browser (or an incognito/private
   window) and register/log in as a different user there.

5. Register an account, log in, create or join a room, and start
   chatting. Try typing `:wave:` or `:fire:` in a message.

6. To see the desktop notification feature, open a room in two
   windows logged in as two different users, click away from one
   window (so it loses focus), and send a message from the other —
   a system notification should pop up.

## How the pieces fit together

- **Flask** serves normal web pages: register, login, room list, and
  the chat room itself (server-rendered with Jinja2 templates).
- **Flask-SocketIO** layers a WebSocket connection on top of that,
  so messages appear instantly without the page needing to reload
  or poll the server.
- **SQLite** (via `database.py`) is the single source of truth for
  users, rooms, and message history — nothing important lives only
  in memory, so restarting the server doesn't lose data.
- **`emoji_support.py`** rewrites shortcodes to Unicode *before* a
  message is saved to the database, so the emoji is stored and
  redisplayed correctly for everyone, including users who join later
  and load it from history.
- **`chat.js`** in the browser listens for `new_message` /
  `system_message` events from the server and appends them to the
  page. It also uses the browser's `Notification` API to alert users
  of new messages when their window isn't focused.

## Security & privacy notes (required transparency section)

This project is a learning exercise, not a production-secure
messenger. Please read this before using it for anything beyond
local practice:

**What IS protected:**
- Passwords are never stored in plain text. They are hashed with
  Werkzeug's `generate_password_hash` (PBKDF2 with a per-user salt)
  before being written to `chat.db`. Even if the database file were
  leaked, an attacker would not directly recover passwords.
- Basic HTML-escaping is applied to messages in the browser before
  they are inserted into the page, to prevent a message like
  `<script>...</script>` from executing in another user's browser.

**What is NOT protected (by design, for this learning project):**
- **Messages are stored in plain text in `chat.db`.** Anyone with
  file access to the server (or the `.db` file itself) can read
  every message ever sent, in every room. There is no message
  encryption at rest.
- **There is no end-to-end encryption.** Messages are sent as plain
  WebSocket payloads. On `localhost` this doesn't matter, but if you
  deployed this app over a real network without HTTPS/WSS, messages
  could be intercepted in transit.
- **`SECRET_KEY` is hard-coded** in `app.py` for convenience. In any
  real deployment, this should be a long random value loaded from an
  environment variable, since it's used to sign session cookies.
- **No rate limiting or spam protection** — a user can send unlimited
  messages as fast as they want.
- **No admin/moderation tools** — anyone can create rooms, and any
  room member can post; there's no way to delete messages, ban
  users, or make a room private.
- **Session cookies are not marked `Secure`** (which requires HTTPS),
  so this should only be run over plain HTTP on `localhost` or a
  trusted local network, never exposed directly to the internet as-is.

**In short:** treat every message sent through this app as something
that lives permanently, in readable form, in `chat.db` on whichever
machine runs the server — the same way you'd treat a plain text file.

## Known limitations

- Single server process, in-memory Socket.IO room tracking (fine for
  a class project / localhost use; a production version would use a
  message queue like Redis to support multiple server instances).
- No password reset flow.
- No "typing..." indicator or read receipts.
