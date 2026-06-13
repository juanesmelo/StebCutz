"""Webhook de WhatsApp Cloud API para StebCutz.

Una sola Lambda detrás de API Gateway que maneja:
  - GET  /webhook  -> verificacion del webhook que pide Meta (hub.challenge).
  - POST /webhook  -> recepcion de mensajes entrantes; responde "Hola".

Usa solo la libreria estandar + boto3 (incluido en el runtime de Lambda),
asi que la funcion no necesita dependencias empaquetadas.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

# Dependencias vendorizadas (google-auth, requests) instaladas en ./vendor.
# Hay que añadirlas al path ANTES de importar el cliente de Sheets.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

import boto3

VERIFY_TOKEN = os.environ["WHATSAPP_VERIFY_TOKEN"]
WHATSAPP_TOKEN = os.environ["WHATSAPP_TOKEN"]
PHONE_NUMBER_ID = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
TABLE_NAME = os.environ["TABLE_NAME"]
GRAPH_API_VERSION = os.environ.get("GRAPH_API_VERSION", "v21.0")

table = boto3.resource("dynamodb").Table(TABLE_NAME)


def handler(event, context):
    """Punto de entrada. API Gateway (REST, proxy) entrega httpMethod, etc."""
    method = (event.get("httpMethod") or "").upper()

    if method == "GET":
        return _verify_webhook(event)
    if method == "POST":
        return _handle_message(event)

    return {"statusCode": 405, "body": "Method Not Allowed"}


def _verify_webhook(event):
    """Meta llama GET con hub.* para validar la suscripcion del webhook."""
    params = event.get("queryStringParameters") or {}
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        # Meta espera el challenge en texto plano y status 200.
        return {"statusCode": 200, "body": challenge or ""}

    return {"statusCode": 403, "body": "Forbidden"}


def _handle_message(event):
    """Procesa la notificacion de mensaje entrante y responde 'Hola'."""
    body = json.loads(event.get("body") or "{}")

    try:
        value = body["entry"][0]["changes"][0]["value"]
    except (KeyError, IndexError, TypeError):
        return _ok()

    messages = value.get("messages")
    if not messages:
        # Puede ser un evento de estado (entregado/leido), lo ignoramos.
        return _ok()

    msg = messages[0]
    msg_id = msg.get("id", "")
    from_number = msg.get("from", "")

    # Idempotencia: Meta reintenta si no recibe 200; evitamos responder doble.
    if _already_processed(msg_id):
        return _ok()

    text = (msg.get("text") or {}).get("body", "")
    _save_message(msg_id, from_number, text)

    try:
        _send_reply(from_number, _build_reply(text))
    except urllib.error.HTTPError as err:
        # Logueamos el error pero igual devolvemos 200 para que Meta no reintente.
        print("Error enviando respuesta:", err.code, err.read().decode("utf-8", "ignore"))

    return _ok()


def _build_reply(text):
    """Decide la respuesta segun el texto entrante.

    Flujo actual:
      - "ping sheet"           -> prueba cruda de conexion con Google Sheets (debug).
      - consulta de horarios   -> disponibilidad real (ver availability.reply_for).
      - cualquier otra cosa    -> "Hola".

    Los imports son perezosos para que un fallo de ./vendor no afecte el flujo normal
    ni la verificacion (GET) del webhook.
    """
    cmd = (text or "").strip()

    if cmd.lower() == "ping sheet":
        try:
            import sheets

            rows = sheets.read_range("A1:B5")
        except Exception as err:  # noqa: BLE001 - queremos reportar cualquier fallo
            return f"Error leyendo el Sheet: {err}"
        if not rows:
            return "Conexion con Sheets OK, pero el rango A1:B5 esta vacio."
        return "Sheet OK:\n" + "\n".join(" | ".join(r) for r in rows)

    try:
        import availability

        reply = availability.reply_for(cmd)
        if reply is not None:
            return reply
    except Exception as err:  # noqa: BLE001 - reportamos cualquier fallo de lectura/parseo
        return f"Error consultando disponibilidad: {err}"

    return "Hola"


def _already_processed(msg_id):
    if not msg_id:
        return False
    resp = table.get_item(Key={"pk": f"MSG#{msg_id}"})
    return "Item" in resp


def _save_message(msg_id, from_number, text):
    table.put_item(
        Item={
            "pk": f"MSG#{msg_id}",
            "from_number": from_number,
            "text": text,
            "ts": int(time.time()),
        }
    )


def _send_reply(to_number, text):
    """Envia un mensaje de texto via WhatsApp Cloud API (Graph API)."""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": text},
        }
    ).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {WHATSAPP_TOKEN}")
    req.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read()


def _ok():
    return {"statusCode": 200, "body": "EVENT_RECEIVED"}
