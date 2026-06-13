"""Ensamblado del agente StebCutz con el OpenAI Agents SDK.

Carga el comportamiento desde behavior.md, registra las tools y expone run(), que
procesa un mensaje del usuario manteniendo memoria por numero en DynamoDB.
"""

import os
from pathlib import Path

from agents import Agent, Runner

from .memory import DynamoDBSession
from .tools.schedule import agendar_cita, consultar_disponibilidad

# Logging detallado del SDK a stdout (-> CloudWatch). Toggle con AGENT_DEBUG=0.
if os.environ.get("AGENT_DEBUG", "1") == "1":
    try:
        from agents import enable_verbose_stdout_logging

        enable_verbose_stdout_logging()
    except Exception as err:  # noqa: BLE001
        print("[agent] no se pudo activar verbose logging:", repr(err))

# Modelo por defecto (configurable con la env var OPENAI_MODEL). 'mini' = economico.
DEFAULT_MODEL = "gpt-5-mini"

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
    print(f"[agent] IN from={phone}: {text!r}")
    try:
        # `context=phone`: las tools lo leen via RunContextWrapper (no lo ve el modelo).
        result = Runner.run_sync(_agent, text, session=session, context=phone)
    except Exception as err:  # noqa: BLE001
        import traceback

        print("[agent] EXCEPTION:", repr(err))
        traceback.print_exc()
        raise
    print(f"[agent] OUT: {result.final_output!r}")
    return result.final_output
