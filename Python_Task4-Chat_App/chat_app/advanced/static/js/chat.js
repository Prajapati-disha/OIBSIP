/*
 * chat.js — real-time chat behaviour for one room page.
 *
 * Responsibilities:
 *   1. Connect to the Flask-SocketIO server and join this room.
 *   2. Send whatever the user types when they submit the form.
 *   3. Append incoming messages (from the server) to the page live.
 *   4. Fire a desktop Notification when a new message arrives while
 *      the browser tab/window is NOT focused.
 *
 * ROOM_NAME and USERNAME are defined as globals in chat.html just
 * before this script is loaded.
 */

const socket = io();

const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("message-form");
const inputEl = document.getElementById("message-input");

// Track whether the window currently has focus, so we know when a
// notification is actually useful (no point notifying someone who
// is already looking at the screen).
let windowFocused = true;
window.addEventListener("focus", () => { windowFocused = true; });
window.addEventListener("blur", () => { windowFocused = false; });

// Ask for notification permission once, up front. If the user
// declines, we simply never show notifications — the chat still
// works fine without them.
if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function appendChatMessage(username, message, timestamp, isMine) {
    const div = document.createElement("div");
    div.className = "message" + (isMine ? " mine" : "");
    div.innerHTML =
        `<span class="meta">[${timestamp}] ${escapeHtml(username)}:</span> ` +
        `<span class="text">${escapeHtml(message)}</span>`;
    messagesEl.appendChild(div);
    scrollToBottom();
}

function appendSystemMessage(text) {
    const div = document.createElement("div");
    div.className = "system-message";
    div.textContent = text;
    messagesEl.appendChild(div);
    scrollToBottom();
}

// Basic HTML-escaping so a message like "<script>" is displayed as
// text, not executed. This is important since we render user input
// with innerHTML above (needed to keep the emoji + styling simple).
function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function showDesktopNotification(username, message) {
    if (!("Notification" in window)) return;
    if (Notification.permission !== "granted") return;
    if (windowFocused) return; // only notify when the window is NOT focused

    const notification = new Notification(`${username} in #${ROOM_NAME}`, {
        body: message,
        tag: "chat-app-message", // collapses rapid-fire notifications into one
    });

    // Clicking the notification brings the chat window back into focus.
    notification.onclick = () => {
        window.focus();
        notification.close();
    };
}

// --- Socket.IO event wiring ---------------------------------------

socket.on("connect", () => {
    socket.emit("join", { room: ROOM_NAME });
});

socket.on("new_message", (data) => {
    const isMine = data.username === USERNAME;
    appendChatMessage(data.username, data.message, data.timestamp, isMine);
    if (!isMine) {
        showDesktopNotification(data.username, data.message);
    }
});

socket.on("system_message", (data) => {
    appendSystemMessage(data.text);
});

window.addEventListener("beforeunload", () => {
    socket.emit("leave", { room: ROOM_NAME });
});

// --- Form submission ------------------------------------------------

formEl.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = inputEl.value.trim();
    if (!text) return;

    socket.emit("send_message", { room: ROOM_NAME, message: text });
    inputEl.value = "";
});

// Scroll to the bottom once on initial page load so the most recent
// history is visible immediately.
scrollToBottom();
