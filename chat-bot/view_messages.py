import sqlite3

def view_messages():
    conn = sqlite3.connect("messages.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages")
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    messages = view_messages()
    for message in messages:
        print(message)
