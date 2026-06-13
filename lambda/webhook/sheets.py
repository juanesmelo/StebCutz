"""Cliente minimo de Google Sheets para StebCutz.

Autenticacion con una *service account* de GCP: la clave JSON viene en la env var
GOOGLE_SERVICE_ACCOUNT_JSON (una sola linea) y el Sheet objetivo en SHEET_ID.

Se habla directo con la API REST v4 (https://sheets.googleapis.com) usando google-auth
para firmar/renovar el token; no hace falta google-api-python-client.

El scope es de lectura+escritura para soportar tanto consultar disponibilidad como
agendar/confirmar citas mas adelante.
"""

import json
import os

from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

# Sesion HTTP autenticada, perezosa y cacheada entre invocaciones (warm starts).
_session = None


def _session_for(sheet_id=None):
    global _session
    if _session is None:
        info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        _session = AuthorizedSession(creds)
    return _session


def _sheet_id(sheet_id=None):
    return sheet_id or os.environ["SHEET_ID"]


def read_range(a1_range, sheet_id=None):
    """Devuelve las filas (lista de listas de strings) del rango A1 indicado.

    Ej.: read_range("Disponibilidad!A1:C10").
    """
    url = f"{_BASE}/{_sheet_id(sheet_id)}/values/{a1_range}"
    resp = _session_for().get(url, timeout=10)
    resp.raise_for_status()
    return resp.json().get("values", [])


def append_row(a1_range, row, sheet_id=None):
    """Agrega una fila al final de la tabla que contiene el rango indicado."""
    url = f"{_BASE}/{_sheet_id(sheet_id)}/values/{a1_range}:append"
    params = {"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"}
    resp = _session_for().post(url, params=params, json={"values": [row]}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def update_range(a1_range, values, sheet_id=None):
    """Sobrescribe el rango con la matriz de valores dada (lista de filas)."""
    url = f"{_BASE}/{_sheet_id(sheet_id)}/values/{a1_range}"
    params = {"valueInputOption": "USER_ENTERED"}
    resp = _session_for().put(url, params=params, json={"values": values}, timeout=10)
    resp.raise_for_status()
    return resp.json()
