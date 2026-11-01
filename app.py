
from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
import os
import re
import subprocess
import webbrowser

app = Flask(__name__)

OMNIROUTE_URL = "http://127.0.0.1:20128/v1/chat/completions"
MODEL = "kiro/claude-sonnet-4.5"

DB_PATH = os.path.join(os.path.dirname(__file__), "jarvis_memory.db")

SYSTEM_PROMPT = """
You are JARVIS, the user's personal AI assistant.

Rules:
- Your name is JARVIS, never Kiro.
- Speak clearly and directly.
- Keep answers short unless asked for detail.
- Help with coding, study, research, and computer tasks.
- Give Windows commands with the exact CMD window to use.
- Explain tasks one step at a time.
- Never claim you performed an action unless you did.
- Ask permission before suggesting risky computer actions.
- Use saved memories and past conversations when relevant.
"""


def get_db():
    return sqlite3.connect(DB_PATH)


def initialise_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT NOT NULL UNIQUE
            )
        """)


def save_message(role, content):
    with get_db() as db:
        db.execute(
            "INSERT INTO messages (role, content) VALUES (?, ?)",
            (role, content)
        )


def detect_memories(message):
    patterns = [
        r"\bmy name is [^.!?]+",
        r"\bmy favourite [^.!?]+",
        r"\bmy favorite [^.!?]+",
        r"\bi prefer [^.!?]+",
        r"\bi like [^.!?]+",
        r"\bi dislike [^.!?]+",
        r"\bmy hobby is [^.!?]+",
        r"\bmy hobbies are [^.!?]+",
        r"\bi study [^.!?]+",
        r"\bi am in class [^.!?]+",
    ]

    found = []

    for pattern in patterns:
        found.extend(re.findall(pattern, message, re.IGNORECASE))

    return [fact.strip() for fact in found]


def save_memory(fact):
    with get_db() as db:
        db.execute(
            "INSERT OR IGNORE INTO memories (fact) VALUES (?)",
            (fact,)
        )


# SAFE COMPUTER CONTROL

APP_COMMANDS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "file explorer": ["explorer.exe"],
    "explorer": ["explorer.exe"],
    "task manager": ["taskmgr.exe"],
}

FOLDER_COMMANDS = {
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    "documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
}

WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chatgpt.com",
}


def control_computer(message):
    command = message.lower().strip()

    # Open approved applications
    for name, executable in APP_COMMANDS.items():
        if command in (
            f"open {name}",
            f"launch {name}",
            f"start {name}"
        ):
            subprocess.Popen(executable)
            return f"Opening {name}."

    # Open approved folders
    for name, path in FOLDER_COMMANDS.items():
        if command in (
            f"open {name}",
            f"open {name} folder"
        ):
            if os.path.isdir(path):
                os.startfile(path)
                return f"Opening {name}."
            return f"{name} folder was not found."

    # Open approved websites
    for name, url in WEBSITES.items():
        if command in (
            f"open {name}",
            f"open {name} website",
            f"launch {name}"
        ):
            webbrowser.open(url)
            return f"Opening {name}."

    return None


initialise_database()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    message = (request.json or {}).get("message", "").strip()

    if not message:
        return jsonify({"reply": "Please enter a message."}), 400

    try:
        # Computer control
        computer_reply = control_computer(message)

        if computer_reply:
            save_message("user", message)
            save_message("assistant", computer_reply)
            return jsonify({"reply": computer_reply})

        # Manual memory command
        if message.lower().startswith("remember that "):
            fact = message[len("remember that "):].strip()

            if fact:
                save_memory(fact)

            reply = "I have saved that in my memory."
            save_message("user", message)
            save_message("assistant", reply)

            return jsonify({"reply": reply})

        # Automatic memory detection
        for fact in detect_memories(message):
            save_memory(fact)

        # Load memories and conversation history
        with get_db() as db:
            memories = db.execute(
                "SELECT fact FROM memories ORDER BY id"
            ).fetchall()

            history = db.execute(
                "SELECT role, content FROM messages ORDER BY id"
            ).fetchall()

        memory_text = "\n".join(
            f"- {row[0]}" for row in memories
        )

        messages = [{
            "role": "system",
            "content": SYSTEM_PROMPT
            + "\n\nSaved memories:\n"
            + (memory_text if memory_text else "No saved memories yet.")
        }]

        messages.extend([
            {"role": role, "content": content}
            for role, content in history
        ])

        messages.append({
            "role": "user",
            "content": message
        })

        response = requests.post(
            OMNIROUTE_URL,
            json={
                "model": MODEL,
                "messages": messages
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()
        reply = data["choices"][0]["message"]["content"]

        save_message("user", message)
        save_message("assistant", reply)

        return jsonify({"reply": reply})

    except requests.exceptions.RequestException as e:
        return jsonify({
            "reply": f"OmniRoute connection error: {e}"
        }), 500

    except (KeyError, IndexError, TypeError):
        return jsonify({
            "reply": "JARVIS received an unexpected response."
        }), 500

    except Exception as e:
        return jsonify({
            "reply": f"Computer control error: {e}"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765)
