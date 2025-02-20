import logging
from flask import current_app, jsonify
import json
import requests
import re
import sqlite3
from transformers import pipeline
from rapidfuzz import process, fuzz

# Initialize the text-generation model (using GPT-Neo)
chat_model = pipeline("text-generation", model="EleutherAI/gpt-neo-125M")

def extract_keywords(text):
    """
    Extracts individual words from the input text.
    """
    return re.findall(r'\b\w+\b', text.lower())

def query_odata(user_input):
    """
    Filters the mock OData JSON to return relevant data based on user input.
    """
    file_path = "C:/Users/Betech/Desktop/python-whatsapp-bot-main/chat-bot/app/utils/mock_odata.json"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"Error loading mock OData: {e}")
        return []
    
    keywords = extract_keywords(user_input)
    relevant_data = []
    
    for item in data.get("value", []):
        for key in ["product_name", "customer", "employee_name"]:
            if key in item:
                match_score = process.extractOne(user_input, [item[key]], scorer=fuzz.partial_ratio)
                if match_score and match_score[1] > 70:
                    relevant_data.append(item)
                    break
    
    return relevant_data

def log_message(phone_number, name, message_text, direction):
    """
    Logs a message (sent or received) to the SQLite database messages.db.
    """
    try:
        conn = sqlite3.connect("messages.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT,
                name TEXT,
                message_text TEXT,
                direction TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "INSERT INTO messages (phone_number, name, message_text, direction) VALUES (?, ?, ?, ?)",
            (phone_number, name, message_text, direction)
        )
        conn.commit()
    except Exception as e:
        logging.error(f"Error logging message to database: {e}")
    finally:
        conn.close()

def generate_response(user_input):
    """
    Generates a response by combining structured ERP data with GPT-Neo.
    """
    relevant_data = query_odata(user_input)
    
    if relevant_data:
        data_summary = "\n".join(
            [f"{key.capitalize()}: {value}" for item in relevant_data for key, value in item.items()]
        )
        prompt = f"""
You are an AI assistant helping users query an ERP system.
Based on the summarized ERP data below, answer the following question concisely.
If the data does not contain the answer, reply exactly: "I don't have that information."

Summarized Data:
{data_summary}

Question: {user_input}

Answer:
"""
    else:
        return "I don't have that information."
    
    generated = chat_model(prompt, max_length=150, do_sample=True, temperature=0.1)[0]['generated_text']
    response = generated.split("Answer:")[-1].strip() if "Answer:" in generated else generated.strip()
    
    return response if len(response) > 10 else "I don't have that information."

def process_text_for_whatsapp(text):
    """
    Applies custom formatting to text (e.g., removes unwanted characters or adjusts asterisks).
    """
    text = re.sub(r"\【.*?\】", "", text).strip()
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)
    return text

def get_text_message_input(recipient, text):
    """
    Formats a text message for WhatsApp.
    """
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    })

def send_message(data):
    """
    Sends a message via WhatsApp API.
    """
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}"
    }
    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        logging.info(f"WhatsApp message sent: {response.status_code}")
        return response

def process_whatsapp_message(body):
    """
    Process incoming WhatsApp messages and fetch the user's profile picture.
    """
    try:
        entry = body["entry"][0]["changes"][0]["value"]
        contacts = entry.get("contacts", [])
        messages = entry.get("messages", [])

        if not messages or not contacts:
            logging.warning("No valid messages or contacts in request body")
            return

        wa_id = contacts[0]["wa_id"]
        contact_name = contacts[0]["profile"]["name"] if "profile" in contacts[0] else "Unknown"

        # Fetch profile photo
        profile_photo_url = get_whatsapp_profile_photo(wa_id)
        
        message_body = messages[0]["text"]["body"]
        log_message(wa_id, contact_name, message_body, "received")

        response_text = generate_response(message_body)
        response_text = f"Hello {contact_name}, " + response_text
        response_text = process_text_for_whatsapp(response_text)
        log_message(wa_id, contact_name, response_text, "sent")

        # Log profile picture if available
        if profile_photo_url:
            logging.info(f"User {contact_name} profile photo: {profile_photo_url}")

        data = get_text_message_input(wa_id, response_text)
        send_message(data)
    
    except Exception as e:
        logging.error(f"Error processing WhatsApp message: {e}")


import requests
import logging

def get_whatsapp_profile_photo(wa_id):
    """
    Retrieves the user's WhatsApp profile picture URL.
    """
    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{wa_id}/profile"
    
    headers = {
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "profile_pic_url" in data:
            return data["profile_pic_url"]
        else:
            return None  # No profile picture available
        
    except requests.RequestException as e:
        logging.error(f"Error retrieving WhatsApp profile photo: {e}")
        return None


def is_valid_whatsapp_message(body):
    """
    Validates if the incoming request body contains a valid WhatsApp message.
    """
    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        if "messages" in value and isinstance(value["messages"], list):
            return True
        return False
    except Exception as e:
        logging.error(f"Error validating WhatsApp message: {e}")
        return False
