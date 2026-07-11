"""
Asistente conversacional de LavaExpress La 43.
Atiende motos, carros, camionetas y vans.
"""
import os
import threading
from datetime import datetime, timedelta
import time
import json

import anthropic
import services_data
import booking
import google_calendar
import cliente_db
from whatsapp_api import send_text_message, send_image_message

MODELO = "claude-haiku-4-5"
MAX_MENSAJES_HISTORIAL = 20

historial_conversaciones = {}
ultima_actividad = {}
retoma_enviada = {}
MINUTOS_INACTIVIDAD_RETOMA = 15

_cliente_anthropic = None
_candados_por_numero = {}
_candado_global = threading.Lock()


def _obtener_candado(numero: str) -> threading.Lock:
    with _candado_global:
        if numero not in _candados_por_numero:
            _candados_por_numero[numero] = threading.Lock()
        return _candados_por_numero[numero]


def _get_cliente():
    global _cliente_anthropic
    if _cliente_anthropic is None:
        _cliente_anthropic = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _cliente_anthropic


def _fecha_actual_bogota() -> str:
    ahora = datetime.utcnow() - timedelta(hours=5)
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    return f"{ahora.strftime('%Y-%m-%d')} ({dias[ahora.weekday()]})"


def _construir_catalogo() -> str:
    """Construye el catálogo completo de servicios para todos los tipos de vehículo."""
    secciones = []
    for tipo in services_data.TIPOS_VEHICULO:
        servicios = services_data.SERVICIOS.get(tipo, {})
        if not servicios:
            continue
        lineas = [f"\n*{tipo.upper()}:*"]
        for nombre, precio in servicios.items():
            precio_fmt = f"${precio:,}".replace(",", ".") + " COP" if precio else "Según cotización"
            desc = services_data.DESCRIPCIONES_SERVICIOS.get(nombre, "")
            lineas.append(f"• {nombre} — {precio_fmt}" + (f"\n  {desc}" if desc else ""))
        secciones.append("\n".join(lineas))
    return "\n".join(secciones)


def _construir_system_prompt(numero: str = "") -> str:
    catalogo_texto = _construir_catalogo()

    nombre_cliente = cliente_db.obtener_nombre(numero) if numero else None
    if nombre_cliente:
        contexto_cliente = (
            f"\nCLIENTE ACTUAL: Ya conoces a este cliente, su nombre es *{nombre_cliente}*. "
            f"Salúdalo por su nombre de forma natural al inicio de la conversación."
        )
    else:
        contexto_cliente = (
            "\nCLIENTE ACTUAL: No tenemos el nombre de este cliente aún. "
            "No lo pidas de entrada — espera a que la conversación llegue a un punto natural."
        )

    return f"""Eres el asistente virtual de {services_data.NOMBRE_NEGOCIO}, un lavadero de motos y carros en Medellín, Colombia. Hablas por WhatsApp directamente con los clientes.

INFORMACIÓN DEL NEGOCIO:
- Horario de atención: {services_data.HORARIO_ATENCION}
- Ubicación: {services_data.UBICACION}
- Métodos de pago: {services_data.METODOS_PAGO}

SERVICIOS Y PRECIOS (organizados por tipo de vehículo):
{catalogo_texto}

CAPACIDAD:
- Máximo {services_data.MAX_CITAS_POR_HORA} vehículos por franja horaria de 1 hora.
- Antes de confirmar una cita, SIEMPRE usa verificar_disponibilidad para consultar si hay cupo.
- Si no hay cupo, infórmale al cliente y sugiérele otra hora.

FECHA DE HOY: {_fecha_actual_bogota()}

CÓMO DEBES COMPORTARTE:
- Habla como una persona real, cálida y cercana, en español colombiano natural. No suenes robótico.
- Usa emojis con naturalidad. Respuestas cortas y directas como en WhatsApp.
- Cuando el cliente pregunte por servicios, primero pregúntale el tipo de vehículo (moto, carro, camioneta o van) para mostrarle los precios correctos.
- Para agendar necesitas: nombre completo, placa del vehículo, tipo de vehículo, servicio deseado, fecha y hora. Pregúntalos de forma natural.
- Las fechas/horas para las herramientas van en formato fecha="YYYY-MM-DD" y hora="HH:MM" en 24 horas.
- CRÍTICO: Para reagendar o cancelar, SIEMPRE llama primero a buscar_mis_citas para obtener el event_id real. NUNCA inventes el event_id.
- NUNCA ofrezcas proactivamente cancelar. Solo procésalo si el cliente lo pide explícitamente.
- Si el cliente confirma asistencia al recordatorio, usa notificar_confirmacion.
- Si el cliente tiene una PQR, usa enviar_pqr.
- Si el cliente pide EXPLÍCITAMENTE hablar con un asesor o una persona humana (usando palabras como "asesor", "persona", "humano", "hablar con alguien"), usa solicitar_asesor. NO uses solicitar_asesor cuando el cliente simplemente está confirmando una fecha, hora o datos de la cita — eso es parte normal del agendamiento.
- Si el cliente responde al seguimiento post-servicio, usa enviar_pqr para informarle al asesor.
- Si el cliente dice que queda lejos, menciona que estamos ubicados en Manrique Central, muy cerca del metro y con fácil acceso.
- REGLA IMPORTANTE: nunca digas que algo se hizo sin haber llamado realmente a la herramienta correspondiente.
- Nunca inventes información. Si no sabes algo, dilo con honestidad.{contexto_cliente}"""


HERRAMIENTAS = [
    {
        "name": "verificar_disponibilidad",
        "description": "Verifica si hay cupo disponible en una fecha y hora. Úsala SIEMPRE antes de agendar_cita.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fecha": {"type": "string", "description": "Fecha YYYY-MM-DD"},
                "hora": {"type": "string", "description": "Hora HH:MM en 24h"},
            },
            "required": ["fecha", "hora"],
        },
    },
    {
        "name": "notificar_confirmacion",
        "description": "Notifica al asesor que un cliente confirmó su cita.",
        "input_schema": {
            "type": "object",
            "properties": {"nombre_cliente": {"type": "string"}},
            "required": ["nombre_cliente"],
        },
    },
    {
        "name": "agendar_cita",
        "description": "Crea una cita en el calendario. Solo úsala después de confirmar todos los datos y verificar disponibilidad.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string"},
                "placa": {"type": "string"},
                "tipo_vehiculo": {"type": "string", "description": "moto, carro, camioneta o van"},
                "servicio": {"type": "string"},
                "fecha": {"type": "string", "description": "YYYY-MM-DD"},
                "hora": {"type": "string", "description": "HH:MM en 24h"},
            },
            "required": ["nombre", "placa", "tipo_vehiculo", "servicio", "fecha", "hora"],
        },
    },
    {
        "name": "buscar_mis_citas",
        "description": "Busca las próximas citas del cliente. Úsala antes de reagendar o cancelar.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "cancelar_cita",
        "description": "Cancela una cita usando su event_id (obtenido de buscar_mis_citas). Solo si el cliente lo pide explícitamente.",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": ["event_id"],
        },
    },
    {
        "name": "reagendar_cita",
        "description": "Cambia la fecha/hora de una cita usando su event_id (obtenido de buscar_mis_citas).",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "fecha": {"type": "string", "description": "Nueva fecha YYYY-MM-DD"},
                "hora": {"type": "string", "description": "Nueva hora HH:MM"},
            },
            "required": ["event_id", "fecha", "hora"],
        },
    },
    {
        "name": "enviar_pqr",
        "description": "Envía una PQR o respuesta de seguimiento al asesor.",
        "input_schema": {
            "type": "object",
            "properties": {"mensaje": {"type": "string"}},
            "required": ["mensaje"],
        },
    },
    {
        "name": "solicitar_asesor",
        "description": "Avisa al asesor que el cliente quiere hablar con una persona.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _ejecutar_herramienta(nombre_herramienta: str, args: dict, numero: str) -> str:
    try:
        if nombre_herramienta == "verificar_disponibilidad":
            cantidad = google_calendar.contar_citas_en_franja(args["fecha"], args["hora"])
            disponibles = services_data.MAX_CITAS_POR_HORA - cantidad
            if disponibles > 0:
                return f"Hay cupo disponible ({disponibles} espacios libres). Puedes proceder a agendar."
            return f"No hay cupo para esa hora ({cantidad} vehículos ya agendados). Sugiere otra hora."

        elif nombre_herramienta == "notificar_confirmacion":
            if services_data.NUMERO_DUENO:
                send_text_message(services_data.NUMERO_DUENO,
                    f"✅ *Confirmación de cita*\n{args.get('nombre_cliente', 'Un cliente')} confirmó su asistencia 🚗")
            return "Confirmación enviada al asesor."

        elif nombre_herramienta == "agendar_cita":
            if "PPF" in args.get("servicio", ""):
                if services_data.NUMERO_DUENO:
                    send_text_message(services_data.NUMERO_DUENO,
                        f"🛡️ *Solicitud PPF*\nCliente: {numero}\nNombre: {args.get('nombre')}\nPlaca: {args.get('placa')}")
                return "PPF requiere cotización. Avisa al cliente que un asesor lo contactará."

            datos = {
                "nombre": args["nombre"],
                "placa": args["placa"].upper(),
                "tipo_vehiculo": args["tipo_vehiculo"],
                "servicio": args["servicio"],
            }
            event_id = booking.guardar_cita_estructurada(numero, datos, args["fecha"], args["hora"])

            if args.get("nombre"):
                cliente_db.guardar_nombre(numero, args["nombre"])

            if event_id and services_data.NUMERO_DUENO:
                try:
                    fecha_legible = datetime.strptime(args["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
                    hora_legible = datetime.strptime(args["hora"], "%H:%M").strftime("%I:%M %p").lstrip("0")
                except Exception:
                    fecha_legible = args["fecha"]
                    hora_legible = args["hora"]
                precio = services_data.SERVICIOS.get(args["tipo_vehiculo"], {}).get(args["servicio"])
                precio_texto = (f"${precio:,}".replace(",", ".") + " COP" if precio else "Según cotización")
                send_text_message(services_data.NUMERO_DUENO,
                    f"📅 *Nueva cita agendada*\n\n"
                    f"👤 *Nombre:* {args['nombre']}\n"
                    f"🚗 *Placa:* {args['placa'].upper()}\n"
                    f"🚘 *Vehículo:* {args['tipo_vehiculo'].capitalize()}\n"
                    f"🔧 *Servicio:* {args['servicio']}\n"
                    f"💰 *Precio:* {precio_texto}\n"
                    f"📆 *Fecha:* {fecha_legible}\n"
                    f"🕒 *Hora:* {hora_legible}\n"
                    f"📱 *WhatsApp:* {numero}"
                )

            if event_id:
                return f"Cita agendada correctamente para el {args['fecha']} a las {args['hora']}."
            return "No se pudo agendar automáticamente. Dile al cliente con honestidad y ofrece escalar con un asesor."

        elif nombre_herramienta == "buscar_mis_citas":
            citas = google_calendar.buscar_eventos_por_cliente(numero)
            if not citas:
                return "El cliente no tiene citas próximas agendadas."
            lineas = [
                f"event_id={c['id']} | {c['resumen']} | {c['inicio'].strftime('%Y-%m-%d %H:%M')}"
                for c in citas
            ]
            return "Citas (usa EXACTAMENTE el event_id, no lo modifiques):\n" + "\n".join(lineas)

        elif nombre_herramienta == "cancelar_cita":
            exito = google_calendar.eliminar_evento(args["event_id"])
            if exito:
                if services_data.NUMERO_DUENO:
                    send_text_message(services_data.NUMERO_DUENO,
                        f"❌ *Cita cancelada*\n📱 Cliente: {numero}")
                return "Cita cancelada correctamente."
            return "No se pudo cancelar. Avísale al cliente que un asesor lo ayudará."

        elif nombre_herramienta == "reagendar_cita":
            exito = google_calendar.actualizar_evento_estructurado(args["event_id"], args["fecha"], args["hora"])
            if exito:
                if services_data.NUMERO_DUENO:
                    try:
                        fecha_legible = datetime.strptime(args["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y")
                        hora_legible = datetime.strptime(args["hora"], "%H:%M").strftime("%I:%M %p").lstrip("0")
                    except Exception:
                        fecha_legible = args["fecha"]
                        hora_legible = args["hora"]
                    send_text_message(services_data.NUMERO_DUENO,
                        f"📅 *Cita reagendada*\n"
                        f"📱 *Cliente:* {numero}\n"
                        f"📆 *Nueva fecha:* {fecha_legible}\n"
                        f"🕒 *Nueva hora:* {hora_legible}"
                    )
                return "Cita reagendada correctamente."
            return "No se pudo reagendar. Avísale al cliente que un asesor lo ayudará."

        elif nombre_herramienta == "enviar_pqr":
            if services_data.NUMERO_DUENO:
                send_text_message(services_data.NUMERO_DUENO,
                    f"📩 *Nueva PQR*\nCliente: {numero}\nMensaje: {args['mensaje']}")
            return "PQR enviada al asesor."

        elif nombre_herramienta == "solicitar_asesor":
            if services_data.NUMERO_DUENO:
                send_text_message(services_data.NUMERO_DUENO,
                    f"🙋 *Solicitud de asesor*\nEl cliente {numero} quiere hablar con una persona.")
            return "Aviso enviado al asesor."

        return "Herramienta no reconocida."

    except Exception as error:
        print(f"⚠️ Error ejecutando {nombre_herramienta}:", error)
        return "Error técnico. Informa al cliente con honestidad y ofrece escalar con un asesor."


def verificar_retomas():
    ahora = time.time()
    limite = MINUTOS_INACTIVIDAD_RETOMA * 60
    try:
        ultima_actividad.update(json.load(open("actividad.json")) if os.path.exists("actividad.json") else {})
    except:
        pass
    for numero, ts in list(ultima_actividad.items()):
        if retoma_enviada.get(numero):
            continue
        if ahora - ts < limite:
            continue
        sesion = historial_conversaciones.get(numero, [])
        if not sesion:
            continue
        ultimo_assistant = next((m for m in reversed(sesion) if m.get("role") == "assistant"), None)
        if not ultimo_assistant:
            continue
        try:
            send_text_message(numero,
                "¡Hola! 👋 Veo que quedamos a medias con tu agendamiento. "
                "¿Seguimos? Aquí estamos para ayudarte 🚗")
            retoma_enviada[numero] = True
        except Exception as e:
            print(f"⚠️ Error enviando retoma a {numero}: {e}")


def handle_message(numero: str, texto: str):
    candado = _obtener_candado(numero)
    with candado:
        _procesar_mensaje(numero, texto)


def _procesar_mensaje(numero: str, texto: str):
    try:
        _act = json.load(open("actividad.json")) if os.path.exists("actividad.json") else {}
    except:
        _act = {}
    _act[numero] = time.time()
    json.dump(_act, open("actividad.json", "w"))
    retoma_enviada.pop(numero, None)

    verificar_retomas()

    if numero not in historial_conversaciones:
        historial_conversaciones[numero] = []
    historial = historial_conversaciones[numero]
    historial.append({"role": "user", "content": texto})

    cliente = _get_cliente()
    system_prompt = _construir_system_prompt(numero)

    try:
        respuesta = None
        while True:
            respuesta = cliente.messages.create(
                model=MODELO,
                max_tokens=1024,
                system=system_prompt,
                tools=HERRAMIENTAS,
                messages=historial,
            )
            historial.append({"role": "assistant", "content": respuesta.content})
            if respuesta.stop_reason != "tool_use":
                break
            resultados_herramientas = []
            for bloque in respuesta.content:
                if bloque.type == "tool_use":
                    resultado = _ejecutar_herramienta(bloque.name, bloque.input, numero)
                    resultados_herramientas.append({
                        "type": "tool_result",
                        "tool_use_id": bloque.id,
                        "content": resultado,
                    })
            historial.append({"role": "user", "content": resultados_herramientas})

        texto_respuesta = "".join(
            bloque.text for bloque in respuesta.content if bloque.type == "text"
        ).strip()
        if texto_respuesta:
            print(f"🤖 [{numero}]: {texto_respuesta[:100]}", flush=True)
            send_text_message(numero, texto_respuesta)

    except Exception as error:
        print("⚠️ Error al hablar con Claude:", error)
        send_text_message(numero, "Disculpa, tuve un problema técnico. ¿Puedes repetir tu mensaje? 🙏")

    finally:
        historial_conversaciones[numero] = historial[-MAX_MENSAJES_HISTORIAL:]
