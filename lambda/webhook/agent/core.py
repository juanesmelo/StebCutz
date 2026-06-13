"""Ensamblado del agente StebCutz con el OpenAI Agents SDK.

Carga el comportamiento desde behavior.md, registra las tools y expone run(), que
procesa un mensaje del usuario manteniendo memoria por numero en DynamoDB.
"""

import os
from pathlib import Path

from agents import Agent, Runner

from .memory import DynamoDBSession
from .tools.schedule import agendar_cita, consultar_disponibilidad

# Modelo por defecto (configurable con la env var OPENAI_MODEL). 'mini' = economico.
DEFAULT_MODEL = "gpt-4o-mini"

# El comportamiento/persona del agente vive en un .md aparte (facil de editar).
_BEHAVIOR = (Path(__file__).resolve().parent / "behavior.md").read_text(encoding="utf-8")

_agent = Agent(
    name="StebCutz",
    instructions=_BEHAVIOR,
    model=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
    tools=[consultar_disponibilidad, agendar_cita],
)


def run(phone, text):
    """Procesa un mensaje del usuario y devuelve la respuesta del agente (texto).

    La memoria de la conversacion se carga y guarda automaticamente en DynamoDB,
    particionada por `phone` (el numero de WhatsApp).
    """
    session = DynamoDBSession(phone)
    result = Runner.run_sync(_agent, text, session=session)
    return result.final_output
