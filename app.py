from flask import Flask, request
import os
import requests

app = Flask(__name__)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "bosco123")

def obtener_respuesta_ia(mensaje_usuario):
    # Inyectamos tu memoria directamente en el texto
    prompt_completo = f"""Eres Bosco, el asistente personal inteligente y exclusivo de John.
Contexto sobre tu jefe:
- Tiene 27 años, vive en la colonia Roma Sur, CDMX.
- Trabaja en un despacho contable en la calle Iguala y maneja temas de IMSS y CONTPAQi.
- Negocios: Co-administra Jolly Prints con su socia Litzy (impresión, sublimación, plotter Cameo 5).
- Intereses: Cuida arañas saltarinas en terrarios bioactivos, juega Stardew Valley, Minecraft, y le gustan los teclados mecánicos.
Tu objetivo: Responder dudas rápidamente, ayudarle a organizar sus proyectos, y mantener un tono amigable, proactivo y conciso (ideal para leer en WhatsApp).

Mensaje de John: {mensaje_usuario}

Respuesta de Bosco:"""

    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return "Error: No se encontró la API Key de Gemini en Render."

    # Enlace directo al modelo más rápido sin usar librerías externas
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt_completo}]}]
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        data = r.json()
        
        if r.status_code == 200:
            respuesta = data['candidates'][0]['content']['parts'][0]['text']
            return respuesta
        else:
            print(f"Error REST Gemini: {data}", flush=True)
            return "Lo siento John, mi cerebro tuvo un cortocircuito interno."
    except Exception as e:
        print(f"Excepción de red Gemini: {e}", flush=True)
        return "Lo siento John, no me pude conectar al servidor de IA."

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
            return challenge, 200
        return "Forbidden", 403

    data = request.get_json(silent=True)
    if not data:
        return "OK", 200

    try:
        value = {}
        if "entry" in data:
            changes = data["entry"][0].get("changes", [])
            if changes:
                value = changes[0].get("value", {})
        elif "value" in data:
            value = data["value"]

        messages = value.get("messages", [])
        if messages:
            msg = messages[0]
            from_number = msg.get("from")
            text = msg.get("text", {}).get("body", "")
            print(f"MSG from {from_number}: {text}", flush=True)

            phone_id = os.getenv("PHONE_NUMBER_ID")
            wa_token = os.getenv("WHATSAPP_TOKEN")
            
            if phone_id and wa_token and text:
                # 1. Bosco piensa
                respuesta_inteligente = obtener_respuesta_ia(text)

                # 2. Bosco responde
                url_meta = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
                headers_meta = {
                    "Authorization": f"Bearer {wa_token}", 
                    "Content-Type": "application/json"
                }
                payload_meta = {
                    "messaging_product": "whatsapp",
                    "to": from_number,
                    "text": {"body": respuesta_inteligente}
                }
                requests.post(url_meta, headers=headers_meta, json=payload_meta, timeout=10)

    except Exception as e:
        print(f"ERROR {e}", flush=True)

    return "OK", 200
