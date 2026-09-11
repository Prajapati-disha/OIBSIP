# Chat App — Beginner Tier (CLI, sockets + threading)

A two-user (expandable to more) command-line chat built with raw
TCP sockets and threading. No external libraries required —
everything here is Python's standard library.

## Feature checklist

- [x] Server script that listens for incoming client connections
- [x] Client script that connects to the server
- [x] Real-time, bidirectional message exchange between connected clients
- [x] Messages displayed with a timestamp prefix, e.g. `[14:35] Alice: Hello`
- [x] Graceful disconnection handling: the other client is notified when one leaves
- [x] Both scripts run on the same machine via `localhost` (127.0.0.1)

## Files

| File | Purpose |
|---|---|
| `server.py` | Listens on `127.0.0.1:5555`, accepts multiple clients, relays messages between them |
| `client.py` | Connects to the server, sends what you type, prints what others send |

## How to run

1. **Start the server** (leave this terminal open):
   ```bash
   python server.py
   ```
   You should see:
   ```
   [SERVER] Listening on 127.0.0.1:5555
   [SERVER] Waiting for clients to connect... (Ctrl+C to stop)
   ```

2. **Start the first client** in a new terminal:
   ```bash
   python client.py
   ```
   Enter a username, e.g. `Alice`.

3. **Start the second client** in another new terminal:
   ```bash
   python client.py
   ```
   Enter a different username, e.g. `Bob`.

4. Type messages in either client window and press Enter — they'll
   appear instantly (with a timestamp) in the other client's window.

5. Type `/quit` in a client, or press `Ctrl+C`, to disconnect. The
   remaining client will see:
   ```
   [14:42] *** Bob has left the chat ***
   ```

### Windows PowerShell note
If you're using a virtual environment, remember activation is:
```powershell
.venv\Scripts\Activate.ps1
```

## How it works (short version)

- The **server** opens a TCP socket, `bind()`s it to `127.0.0.1:5555`,
  and `listen()`s for connections. Every time a client connects via
  `accept()`, the server spins up a new **thread** dedicated to that
  client, so it can talk to many people at once without one client
  blocking another.
- Each **client** also runs two things at once: a background thread
  that just listens for incoming messages and prints them, and the
  main thread that reads what you type and sends it. That's why
  messages from the other person can "pop in" between your own
  keystrokes.
- The server keeps a dictionary of `{socket: username}` for everyone
  currently connected, and simply forwards ("broadcasts") every
  incoming message to everyone else in that dictionary.

## Known limitations (by design — this is the beginner tier)

- No authentication — anyone who can reach `127.0.0.1:5555` can join with any username.
- No message history — messages are not saved anywhere; closing the server loses everything.
- No encryption — messages travel as plain text (fine for localhost practice, not for the internet).
- Single "room" — everyone connected talks in the same conversation.

These limitations are intentionally addressed in the **Advanced Tier**.
