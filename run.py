import logging
from flask import Flask
from flask_cors import CORS
from app import create_app  # Assuming you have a factory
from routes import bp as messages_bp  # Import the blueprint

app = create_app()
CORS(app)
app.register_blueprint(messages_bp)  # Register your routes blueprint

if __name__ == "__main__":
    logging.info("Flask app started")
    app.run(host="0.0.0.0", port=8000)
