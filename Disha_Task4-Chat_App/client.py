"""
client.py — Beginner Tier Chat Client
=======================================
Connects to server.py and lets one person chat. Run this script in
TWO separate terminal windows (each with a different username) to
simulate a real two-user conversation, all on localhost.

Why two threads?
    - One thread continuously LISTENS for incoming messages from the
      server and prints them the moment they arrive (this is what
      makes the chat feel "real-time").
    - The MAIN thread continuously waits for YOU to type something
      and sends it when you hit Enter.
    Without threading, the program could only do one of these two
    things at a time, so you'd never see incoming messages while
    waiting to type your own.
"""

import socket
import threading
import sys
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5555


def timestamp() -> str:
    return datetime.now().strftime("[%H:%M]")


def receive_messages(sock: socket.socket):
    """
    Runs forever in a background thread, printing whatever the
    server sends us. Exits cleanly (and lets the user know) if the
    connection is lost for any reason.
    """
    while True:
        try:
            data = sock.recv(1024)
        except OSError:
            break

        if not data:
            # Server closed the connection.
            print(f"\n{timestamp()} *** Disconnected from server ***")
            break

        message = data.decode("utf-8")
        # \r clears the current input line before printing, so the
        # incoming message doesn't visually collide with what the
        # user is currently typing.
        print(f"\r{message}\nYou: ", end="", flush=True)

    # Tell the whole process to exit once the connection drops,
    # since the input() call in the main thread can't be interrupted
    # from another thread otherwise.
    print("Press Enter to close the client.")
    import os
    os._exit(0)


def main():
    username = input("Choose a username: ").strip() or "Anonymous"

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((HOST, PORT))
    except ConnectionRefusedError:
        print(f"[CLIENT] Could not connect to {HOST}:{PORT}. "
              f"Is server.py running?")
        sys.exit(1)

    # First message we send is always the username (server.py expects this).
    client_socket.sendall(username.encode("utf-8"))

    # Background thread: keeps listening for messages from the server.
    listener = threading.Thread(target=receive_messages, args=(client_socket,), daemon=True)
    listener.start()

    print(f"{timestamp()} Connected to server as '{username}'. "
          f"Type a message and press Enter. Type /quit to exit.\n")

    try:
        while True:
            text = input("You: ")
            if text.strip().lower() == "/quit":
                break
            if text.strip() == "":
                continue
            try:
                client_socket.sendall(text.encode("utf-8"))
            except OSError:
                print(f"{timestamp()} *** Connection lost. Could not send message. ***")
                break
    except KeyboardInterrupt:
        pass
    finally:
        print(f"{timestamp()} Disconnecting...")
        client_socket.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
