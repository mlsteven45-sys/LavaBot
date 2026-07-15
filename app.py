"""
Webhook de Flask para el bot de WhatsApp de LavaExpress La 43.
"""
import os
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv

import claude_assistant
import services_data
from whatsapp_api import send_text_message

load_dotenv()

app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")


@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    modo = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if modo == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Token inválido", 403


@app.route("/webhook", methods=["POST"])
def recibir_mensaje():
    data = request.get_json()
    
    try:
        entry = data["entry"][0]
        cambio = entry["changes"][0]["value"]
        if "messages" not in cambio:
            return jsonify({"status": "ok"}), 200
        mensaje = cambio["messages"][0]
        numero_remitente = mensaje["from"]
        tipo_mensaje = mensaje["type"]

        if tipo_mensaje == "audio":
            send_text_message(numero_remitente,
                "¡Hola! Por el momento solo puedo leer mensajes de texto 😊 ¿Me escribes tu mensaje?")
            return jsonify({"status": "ok"}), 200

        if tipo_mensaje != "text":
            send_text_message(numero_remitente,
                "Por ahora solo puedo leer mensajes de texto 🙏 ¿Me cuentas en palabras qué necesitas?")
            return jsonify({"status": "ok"}), 200

        texto = mensaje["text"]["body"]
        print(f"📨 [{numero_remitente}]: {texto[:200]}", flush=True)

        hilo = threading.Thread(
            target=claude_assistant.handle_message,
            args=(numero_remitente, texto),
            daemon=True,
        )
        hilo.start()

    except (KeyError, IndexError) as e:
        print("⚠️ Error procesando mensaje:", e)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
