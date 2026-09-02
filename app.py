from flask import Flask, request
import os
import requests

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "bosco123")

@app.route("/", methods=["GET"])
def home():
    return "Bosco live", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print(f"WEBHOOK VERIFIED token={token}")
        return challenge, 200
    print(f"VERIFY FAIL mode={mode} token={token} expected={VERIFY_TOKEN}")
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def incoming():
    data = request.get_json()
    print(f"INCOMING: {data}")
    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        if messages:
            msg = messages[0]
            from_number = msg.get("from")
            text = msg.get("text", {}).get("body", "")

            # Responder con WhatsApp Cloud API
            phone_id = os.getenv("PHONE_NUMBER_ID")
            wa_token = os.getenv("WHATSAPP_TOKEN")
            url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
            headers = {"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"}
            payload = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "text": {"body": f"Hola! Soy Bosco. Recibí: '{text}'"}
            }
            r = requests.post(url, headers=headers, json=payload)
            print(f"SEND STATUS {r.status_code} {r.text}")
    except Exception as e:
        print(f"ERROR {e}")
    return "OK", 200
