from flask import Flask, request
import os
import requests

app = Flask(__name__)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "bosco123")

@app.route("/", methods=["GET"])
def home():
    return "Bosco live", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK VERIFIED")
            return challenge, 200
        return "Forbidden", 403

    # POST handling
    data = request.get_json(silent=True)
    print(f"INCOMING: {data}", flush=True)

    if not data:
        return "OK", 200

    try:
        # Extraer value de forma segura (Soporta formato Real y formato Probar)
        value = {}
        if "entry" in data:
            changes = data["entry"][0].get("changes", [])
            if changes:
                value = changes[0].get("value", {})
        elif "value" in data:
            value = data["value"]

        # Si el webhook es un mensaje entrante (ignora estados de "leído/entregado")
        messages = value.get("messages", [])
        if messages:
            msg = messages[0]
            from_number = msg.get("from")
            text = msg.get("text", {}).get("body", "")
            print(f"MSG from {from_number}: {text}", flush=True)

            phone_id = os.getenv("PHONE_NUMBER_ID")
            wa_token = os.getenv("WHATSAPP_TOKEN")
            
            if phone_id and wa_token and text:
                url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
                headers = {
                    "Authorization": f"Bearer {wa_token}", 
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_number,
                    "text": {"body": f"Hola! Soy Bosco. Recibí: '{text}'"}
                }
                r = requests.post(url, headers=headers, json=payload, timeout=10)
                print(f"SEND {r.status_code} {r.text}", flush=True)

    except Exception as e:
        print(f"ERROR {e}", flush=True)

    # SIEMPRE retornar 200 OK para que Meta no desactive el webhook
    return "OK", 200
