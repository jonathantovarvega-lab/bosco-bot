from flask import Flask, request
import os
import requests
import google.generativeai as genai

app = Flask(__name__)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "bosco123")

# Inicializamos el cliente de Gemini usando la variable de entorno
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Definimos la personalidad y memoria de Bosco
instrucciones_bosco = """Eres Bosco, el asistente personal inteligente y exclusivo de John.
Contexto sobre tu jefe:
- Tiene 27 años, vive en la colonia Roma Sur, CDMX.
- Trabaja en un despacho contable en la calle Iguala y maneja temas de IMSS y CONTPAQi.
- Negocios: Co-administra Jolly Prints con su socia Litzy (impresión, sublimación, Cameo 5).
- Intereses: Cuida arañas saltarinas en terrarios bioactivos, juega Stardew Valley, Minecraft, y le gustan los teclados mecánicos (usa un Epomaker Galaxy 100).
Tu objetivo: Responder dudas rápidamente, ayudarle a organizar sus proyectos, y mantener un tono amigable, proactivo y conciso (ideal para leer en WhatsApp)."""

# Configuramos el modelo de IA
modelo_ia = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=instrucciones_bosco
)

def obtener_respuesta_ia(mensaje_usuario):
    try:
        respuesta = modelo_ia.generate_content(mensaje_usuario)
        return respuesta.text
    except Exception as e:
        print(f"Error de Gemini: {e}", flush=True)
        return "Lo siento John, mi cerebro de IA está teniendo problemas de conexión ahora mismo."

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
                # Bosco procesa tu mensaje con Gemini
                respuesta_inteligente = obtener_respuesta_ia(text)

                url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
                headers = {
                    "Authorization": f"Bearer {wa_token}", 
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_number,
                    "text": {"body": respuesta_inteligente}
                }
                requests.post(url, headers=headers, json=payload, timeout=10)

    except Exception as e:
        print(f"ERROR {e}", flush=True)

    return "OK", 200
