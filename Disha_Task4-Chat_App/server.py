"""
server.py — Beginner Tier Chat Server
======================================
This script is the "hub" of the chat. It listens for incoming
connections, keeps track of every connected client, and relays
any message it receives from one client to everybody else.

Concepts used (good to know for the video tutorials mentioned in
the checklist):
    - socket.socket()  -> creates a network endpoint
    - bind()           -> attaches the socket to an address/port
    - listen()         -> puts the socket in "waiting for clients" mode
    - accept()         -> blocks until a client connects, then returns
                          a NEW socket dedicated to that client
    - threading.Thread -> lets us handle multiple clients at once,
                          because accept() and recv() are both
                          "blocking" calls that would otherwise
                          freeze the whole program.

Run this FIRST, then start client.py in two separate terminals.
"""

import socket
import threading
from datetime import datetime

# ---------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------
HOST = "127.0.0.1"   # localhost -> only reachable from this machine
PORT = 5555           # arbitrary "unused" port above 1024

# ---------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------
# We store every connected client as: { socket_object: username }
# A lock is used because multiple threads (one per client) will
# read/write this dictionary at the same time, and dictionaries
# are not guaranteed thread-safe for compound operations.
clients = {}
clients_lock = threading.Lock()


def timestamp() -> str:
    """Return the current time formatted like [14:35]."""
    return datetime.now().strftime("[%H:%M]")


def broadcast(message: str, exclude_socket=None):
    """
    Send `message` to every connected client except `exclude_socket`
    (used so a user doesn't receive an echo of their own message,
    since the client already prints what it sends locally).
    """
    with clients_lock:
        # list(...) makes a copy so we can safely remove dead sockets
        # while iterating.
        for client_socket in list(clients.keys()):
            if client_socket is exclude_socket:
                continue
            try:
                client_socket.sendall(message.encode("utf-8"))
            except OSError:
                # The socket is broken/closed -> clean it up.
                remove_client(client_socket)


def remove_client(client_socket, notify=True):
    """Remove a client from the registry and optionally tell others."""
    with clients_lock:
        username = clients.pop(client_socket, None)
    if username is not None:
        try:
            client_socket.close()
        except OSError:
            pass
        if notify:
            leave_msg = f"{timestamp()} *** {username} has left the chat ***"
            print(leave_msg)
            broadcast(leave_msg)


def handle_client(client_socket, address):
    """
    Runs in its own thread for the entire lifetime of one client's
    connection. Responsible for:
      1. Receiving the username (the very first message sent).
      2. Looping: receive a message -> stamp it -> broadcast it.
      3. Cleaning up gracefully when the client disconnects.
    """
    try:
        # --- Step 1: the first message a client sends is its username ---
        username = client_socket.recv(1024).decode("utf-8").strip()
        if not username:
            username = f"Guest-{address[1]}"

        with clients_lock:
            clients[client_socket] = username

        join_msg = f"{timestamp()} *** {username} has joined the chat ***"
        print(join_msg)
        broadcast(join_msg, exclude_socket=client_socket)

        # Let the newly connected client know they're in.
        client_socket.sendall(
            f"{timestamp()} Connected as '{username}'. Say hi!\n".encode("utf-8")
        )

        # --- Step 2: main receive loop ---
        while True:
            data = client_socket.recv(1024)
            if not data:
                # An empty bytes object means the client closed the
                # connection (a "graceful" TCP shutdown).
                break

            text = data.decode("utf-8").strip()
            if not text:
                continue

            full_message = f"{timestamp()} {username}: {text}"
            print(full_message)
            broadcast(full_message, exclude_socket=client_socket)

    except (ConnectionResetError, ConnectionAbortedError, OSError):
        # The client crashed / lost network / force-closed -> treat the
        # same as a graceful disconnect from the server's perspective.
        pass
    finally:
        # --- Step 3: cleanup runs no matter how we exit the loop ---
        remove_client(client_socket)


def main():
    # AF_INET  -> use IPv4
    # SOCK_STREAM -> use TCP (reliable, ordered, connection-based)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allows the server to restart quickly and reuse the port instead
    # of waiting for the OS to release it ("Address already in use"
    # errors are the #1 annoyance without this line).
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))
    server_socket.listen()  # backlog defaults to a reasonable value

    print(f"[SERVER] Listening on {HOST}:{PORT}")
    print("[SERVER] Waiting for clients to connect... (Ctrl+C to stop)")

    try:
        while True:
            # accept() blocks here until a client connects.
            client_socket, address = server_socket.accept()
            print(f"[SERVER] New connection from {address}")

            # One thread per client so multiple people can chat at once.
            # daemon=True means these threads won't block program exit.
            thread = threading.Thread(
                target=handle_client, args=(client_socket, address), daemon=True
            )
            thread.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    finally:
        with clients_lock:
            for sock in list(clients.keys()):
                sock.close()
        server_socket.close()


if __name__ == "__main__":
    main()
