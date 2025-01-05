from flask import Flask, request, jsonify
from hashlib import sha256
import requests
import uuid
import os

app = Flask(__name__)

SECRET_KEY = os.getenv("06ojdYWqpSyf07VwOsDDisk4N")
USER_ID = os.getenv("307488")
API_BASE_URL = "https://user-api.neverlose.cc/api/market/give-for-free"

def generate_signature(data, secret):
    sorted_data = "".join([f"{key}{data[key]}" for key in sorted(data)])
    return sha256((sorted_data + secret).encode()).hexdigest()

def validate_signature(data, secret):
    received_signature = data.pop("signature", None)
    expected_signature = generate_signature(data, secret)
    return received_signature == expected_signature

def deliver_item(username, item_code):
    transaction_id = str(uuid.uuid4())
    payload = {
        "user_id": USER_ID,
        "id": transaction_id,
        "username": username,
        "code": item_code,
    }
    payload["signature"] = generate_signature(payload, SECRET_KEY)
    response = requests.post(API_BASE_URL, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"HTTP {response.status_code}", "details": response.text}

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    username = data.get("username")
    item_code = data.get("item_code")
    signature = data.get("signature")
    if not username or not item_code or not signature:
        return jsonify({"error": "Missing required fields"}), 400
    if not validate_signature(data, SECRET_KEY):
        return jsonify({"error": "Invalid signature"}), 400
    result = deliver_item(username, item_code)
    if "error" in result:
        return jsonify({"status": "error", "details": result}), 500
    return jsonify({"status": "success", "result": result}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
