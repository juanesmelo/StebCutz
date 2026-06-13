#!/usr/bin/env python3
"""Entrypoint de la app CDK de StebCutz.

Lee la configuracion sensible de variables de entorno:
  - En local: del archivo .env (via python-dotenv).
  - En CI (GitHub Actions): de los GitHub Secrets inyectados como env vars.
"""

import os

import aws_cdk as cdk
from dotenv import load_dotenv

from stebcutz.stebcutz_stack import StebcutzStack

# Carga .env si existe (desarrollo local). En CI no hay .env y no pasa nada.
load_dotenv()


def require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(
            f"Falta la variable de entorno '{name}'. "
            "Definela en .env (local) o en GitHub Secrets (CI)."
        )
    return value


config = {
    "WHATSAPP_TOKEN": require("WHATSAPP_TOKEN"),
    "WHATSAPP_PHONE_NUMBER_ID": require("WHATSAPP_PHONE_NUMBER_ID"),
    "WHATSAPP_VERIFY_TOKEN": require("WHATSAPP_VERIFY_TOKEN"),
    "GRAPH_API_VERSION": os.environ.get("GRAPH_API_VERSION", "v21.0"),
    # Google Sheets: ID del Sheet y clave JSON de la service account (una sola linea).
    "SHEET_ID": require("SHEET_ID"),
    "GOOGLE_SERVICE_ACCOUNT_JSON": require("GOOGLE_SERVICE_ACCOUNT_JSON"),
    # OpenAI (agente): API key (obligatoria) y modelo (opcional, default gpt-4o-mini).
    "OPENAI_API_KEY": require("OPENAI_API_KEY"),
    "OPENAI_MODEL": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
}

app = cdk.App()

StebcutzStack(
    app,
    "StebcutzStack",
    config=config,
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
    ),
)

app.synth()
