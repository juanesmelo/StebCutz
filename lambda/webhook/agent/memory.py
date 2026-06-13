"""Memoria de conversacion por numero de WhatsApp en DynamoDB.

Implementa la interfaz Session del OpenAI Agents SDK (SessionABC). Guarda todos los
"items" de la conversacion (mensajes del usuario, llamadas a tools y respuestas del
agente) en UN item de DynamoDB por numero, como lista JSON. Se recorta a los ultimos
MAX_ITEMS para no crecer sin limite (DynamoDB limita cada item a 400 KB).

La tabla esta particionada por `phone` (PK), tal como se pidio en el diseno.
"""

import json
import os
import time

import boto3
from agents.memory.session import SessionABC

# ~10-15 turnos de contexto; suficiente para una conversacion de agendamiento.
MAX_ITEMS = 40

_table = None


def _get_table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["CONVERSATIONS_TABLE"])
    return _table


class DynamoDBSession(SessionABC):
    """Sesion de conversacion respaldada por DynamoDB (PK = numero de WhatsApp)."""

    def __init__(self, phone, max_items=MAX_ITEMS):
        self.phone = str(phone)
        self.max_items = max_items

    def _load(self):
        resp = _get_table().get_item(Key={"phone": self.phone}, ConsistentRead=True)
        raw = (resp.get("Item") or {}).get("items")
        return json.loads(raw) if raw else []

    def _save(self, items):
        _get_table().put_item(
            Item={
                "phone": self.phone,
                "items": json.dumps(items, ensure_ascii=False),
                "updated_at": int(time.time()),
            }
        )

    # --- Interfaz SessionABC (los metodos son async; usan boto3 sincrono adentro,
    #     lo cual es aceptable para una unica peticion por invocacion de Lambda). ---

    async def get_items(self, limit=None):
        items = self._load()
        if limit is not None and limit > 0:
            return items[-limit:]
        return items

    async def add_items(self, items):
        if not items:
            return
        current = self._load()
        current.extend(items)
        self._save(current[-self.max_items:])

    async def pop_item(self):
        current = self._load()
        if not current:
            return None
        last = current.pop()
        self._save(current)
        return last

    async def clear_session(self):
        _get_table().delete_item(Key={"phone": self.phone})
