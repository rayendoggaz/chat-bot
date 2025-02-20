import sqlite3
from flask import Blueprint, jsonify, request

bp = Blueprint('messages', __name__)
DATABASE = "messages.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enables column access by name
    return conn

@bp.route('/get-all-chats')
def get_all_chats():
    """
    Returns one record per unique phone number with the latest message.
    """
    conn = get_db_connection()
    chats = conn.execute("""
        SELECT TRIM(phone_number) AS phone_number,
               name,
               message_text
        FROM messages
        WHERE timestamp = (
            SELECT MAX(timestamp)
            FROM messages AS sub
            WHERE TRIM(sub.phone_number) = TRIM(messages.phone_number)
        )
        ORDER BY timestamp DESC
    """).fetchall()
    conn.close()
    
    result = [
        {
            "phone": chat["phone_number"],
            "name": chat["name"],   # Include the contact's name
            "last_message": chat["message_text"]
        } 
        for chat in chats
    ]
    return jsonify(result)


@bp.route('/get-messages/<phone>')
def get_messages(phone):
    """
    Returns all messages for a given phone number, along with the contact name.
    """
    phone = phone.strip()

    conn = get_db_connection()
    messages = conn.execute("""
        SELECT name, message_text, direction, timestamp 
        FROM messages
        WHERE TRIM(phone_number) = TRIM(?)
        ORDER BY timestamp ASC
    """, (phone,)).fetchall()
    conn.close()
    
    if messages:
        contact_name = messages[0]["name"]  # Get the name from the first message
    else:
        contact_name = "Unknown"

    conversation = [
        {
            "text": msg["message_text"],
            "direction": msg["direction"],
            "timestamp": msg["timestamp"]
        }
        for msg in messages
    ]
    
    return jsonify({"name": contact_name, "conversation": conversation})
