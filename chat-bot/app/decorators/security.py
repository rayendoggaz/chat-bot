from functools import wraps
from flask import current_app, jsonify, request
import logging
import hashlib
import hmac


def validate_signature(payload, signature):
    """
    Validate the incoming payload's signature against our expected signature
    """
    # Use the App Secret to hash the payload
    expected_signature = hmac.new(
        bytes(current_app.config["APP_SECRET"], "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Check if the signature matches
    return hmac.compare_digest(expected_signature, signature)


def signature_required(func):
    def wrapper(*args, **kwargs):
        secret = current_app.config.get("APP_SECRET")
        received_signature = request.headers.get("X-Hub-Signature-256", "")

        # Debug: Log incoming signature and payload
        logging.info(f"Received Signature: {received_signature}")
        logging.info(f"Payload: {request.get_data()}")

        if not secret or not received_signature:
            logging.error("Missing APP_SECRET or X-Hub-Signature-256 header.")
            return jsonify({"status": "error", "message": "Signature missing or invalid"}), 403

        # Compute HMAC using the secret and payload
        computed_signature = "sha256=" + hmac.new(
            secret.encode("utf-8"), request.get_data(), hashlib.sha256
        ).hexdigest()

        # Debug: Log computed signature
        logging.info(f"Computed Signature: {computed_signature}")

        if not hmac.compare_digest(received_signature, computed_signature):
            logging.error("Signature verification failed!")
            return jsonify({"status": "error", "message": "Signature verification failed"}), 403

        return func(*args, **kwargs)

    return wrapper