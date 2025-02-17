import sqlite3
from flask import Blueprint, jsonify

bp = Blueprint('messages', __name__)
DATABASE = "messages.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enables column access by name
    return conn

# ✅ **Fix for /get-all-chats**
@bp.route('/get-all-chats')
def get_all_chats():
    conn = get_db_connection()
    chats = conn.execute("""
        SELECT phone_number, message_text
        FROM messages
        WHERE timestamp = (
            SELECT MAX(timestamp) FROM messages AS sub WHERE sub.phone_number = messages.phone_number
        )
        ORDER BY timestamp DESC
    """).fetchall()
    conn.close()
    
    result = [
        {"phone": chat["phone_number"], "last_message": chat["message_text"]} 
        for chat in chats
    ]
    return jsonify(result)

# ✅ **Fix for /get-messages/<phone>**
@bp.route('/get-messages/<phone>')
def get_messages(phone):
    conn = get_db_connection()
    messages = conn.execute("""
        SELECT message_text, direction, timestamp 
        FROM messages
        WHERE phone_number = ?
        ORDER BY timestamp ASC
    """, (phone,)).fetchall()
    conn.close()
    
    conversation_lines = []
    for msg in messages:
        prefix = "Me:" if msg["direction"] == "sent" else "Them:"
        formatted_message = msg["message_text"].replace("\n", "<br>")  # Prevents newline display issues
        conversation_lines.append(f"{prefix} {formatted_message}")
    
    conversation = "\n".join(conversation_lines)
    return jsonify({"conversation": conversation})
