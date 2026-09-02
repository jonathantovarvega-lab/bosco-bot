from flask import Flask, request
import requests
import os
app = Flask(__name__)
VERIFY_TOKEN = "bosco123"
ACCESS_TOKEN = "EAATFS4wgGwABSXKypCZCuJXvljRqp6EZA461HOTofIVKrZCQ81PTkcbJbNJWwZAm1kJHtjm11JD7iTj7wp6Mu6XzPCDkJ9VpQJLmCk4ySsPae0p4vxoUbwXiGCgqs8GDTdzV8ydEOW3du26f93fg8SMrm3MEF3AnRGbZC98cPksU9Avr8BS3ZCLOtdVZACUV2z7SAFc3jYZB0zLm6kKV0UkpHCQ4OAT3oftAv9h7VmfA2FRfYle6kMfjgm0oj76KAEfolHIHdjSREy3TU5PZCD3Ah"
PHONE_NUMBER_ID = "1351278931392986"
def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp","to": to,"type": "text","text": {"body": text}}
    requests.post(url, headers=headers, json=data)
@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "fail", 403
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                msgs = change.get("value", {}).get("messages", [])
                if msgs:
                    from_number = msgs[0].get("from")
                    body = msgs[0].get("text", {}).get("body", "")
                    reply = f"Hola! Soy Bosco. Recibi: '{body}'. Ya estoy conectado!"
                    send_whatsapp_message(from_number, reply)
    except Exception as e:
        print(e)
    return "OK", 200
@app.route('/')
def home():
    return "Bosco corriendo"
