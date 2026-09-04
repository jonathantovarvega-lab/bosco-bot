from flask import Flask, request
import os
import requests

app = Flask(__name__)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "bosco123")

# --- FUNCIONES DE MEMORIA (SUPABASE) ---
def guardar_mensaje(role, content):
    try:
        url = f"{os.getenv('SUPABASE_URL')}/rest/v1/historial_chat"
        headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json"
        }
        data = {"role": role, "content": content}
        requests.post(url, headers=headers, json=data, timeout=5)
    except Exception as e:
        print(f"Error guardando en Supabase: {e}", flush=True)

def obtener_historial():
    try:
        # Descargamos los últimos 6 mensajes para darle contexto a la IA
        url = f"{os.getenv('SUPABASE_URL')}/rest/v1/historial_chat?select=*&order=id.desc&limit=6"
        headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}"
        }
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            mensajes = r.json()
            mensajes.reverse() # Acomodamos del más viejo al más nuevo
            historial = ""
            for m in mensajes:
                quien = "John" if m['role'] == 'user' else "Bosco"
                historial += f"{quien}: {m['content']}\n"
            return historial
    except Exception as e:
        print(f"Error leyendo Supabase: {e}", flush=True)
    return ""

# --- CEREBRO (GEMINI) ---
def obtener_respuesta_ia(mensaje_usuario):
    # 1. Bosco recuerda de qué estaban hablando
    historial = obtener_historial()
    
    # 2. Construimos el pensamiento con tu contexto, el historial y tu nuevo mensaje
    prompt_completo = f"""Eres Bosco, el asistente personal inteligente y exclusivo de John.
Contexto sobre tu jefe:
- Tiene 27 años, vive en la colonia Roma Sur, CDMX.
- Trabaja en un despacho contable en la calle Iguala y maneja temas de IMSS y CONTPAQi.
- Negocios: Co-administra Jolly Prints con su socia Litzy (impresión, sublimación, plotter Cameo 5).
- Intereses: Cuida arañas saltarinas en terrarios bioactivos, juega Stardew Valley, Minecraft, y le gustan los teclados mecánicos.
Tu objetivo: Responder dudas rápidamente, ayudarle a organizar sus proyectos, y mantener un tono amigable, proactivo y conciso (ideal para leer en WhatsApp).

Historial de los últimos mensajes (para contexto):
{historial}

Mensaje actual de John: {mensaje_usuario}

Respuesta de Bosco:"""

    gemini_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={gemini_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt_completo}]}]
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=45)
        data = r.json()
        
        if r.status_code == 200:
            respuesta = data['candidates'][0]['content']['parts'][0]['text']
            
            # 3. Guardamos la plática actual en la memoria a largo plazo
            guardar_mensaje("user", mensaje_usuario)
            guardar_mensaje("assistant", respuesta)
            
            return respuesta
        else:
            print(f"Error REST Gemini: {data}", flush=True)
            return "Lo siento John, mi cerebro tuvo un cortocircuito interno."
    except Exception as e:
        print(f"Excepción de red Gemini: {e}", flush=True)
        return "Lo siento John, los servidores están lentos. Dame un minuto."

# --- RUTAS DE FLASK ---
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
            
            phone_id = os.getenv("PHONE_NUMBER_ID")
            wa_token = os.getenv("WHATSAPP_TOKEN")
            
            if phone_id and wa_token and text:
                respuesta_inteligente = obtener_respuesta_ia(text)

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
                requests.post(url_meta, headers_meta, json=payload_meta, timeout=10)

    except Exception as e:
        print(f"ERROR {e}", flush=True)

    return "OK", 200
