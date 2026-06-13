"""Tools de agenda: consultar disponibilidad y agendar citas en el Google Sheet.

Las funciones decoradas con @function_tool se exponen automaticamente al modelo; su
firma y docstring generan el JSON schema de la tool (el SDK usa griffe/inspect).
"""

import traceback

from agents import RunContextWrapper, function_tool

import availability
import sheets


def _fmt_phone(telefono):
    """Normaliza el numero para guardarlo (antepone '+' si son solo digitos)."""
    telefono = (telefono or "").strip()
    if telefono and not telefono.startswith("+"):
        telefono = "+" + telefono
    return telefono


@function_tool
def consultar_disponibilidad(dia: str = "") -> str:
    """Consulta los horarios LIBRES de la barberia en el Google Sheet.

    Args:
        dia: dia de la semana a consultar (ej. "sabado"). Si se omite, devuelve el
            resumen de disponibilidad de toda la semana.
    """
    print(f"[tool] consultar_disponibilidad dia={dia!r}")
    try:
        rows = sheets.read_range(availability.DEFAULT_RANGE)
        data = availability.parse(rows)
        if dia and dia.strip():
            day = availability.find_day(dia) or dia
            out = availability.free_slots_text(day, data=data)
        else:
            out = availability.summary_text(data=data)
    except Exception:  # noqa: BLE001
        print("[tool] consultar_disponibilidad ERROR:")
        traceback.print_exc()
        raise
    print(f"[tool] consultar_disponibilidad -> {out!r}")
    return out


@function_tool
def agendar_cita(ctx: RunContextWrapper, dia: str, hora: str, nombre: str) -> str:
    """Agenda (reserva) una cita marcando la celda del Sheet con el nombre y el telefono.

    El telefono del cliente se toma automaticamente de WhatsApp (NO lo pidas ni lo
    pases como argumento). Usa SIEMPRE una de las horas exactas que devuelve
    `consultar_disponibilidad` (por ejemplo "10:00AM"). Verifica que el horario siga
    libre antes de escribir.

    Args:
        dia: dia de la semana (ej. "sabado").
        hora: franja horaria exacta (ej. "10:00AM").
        nombre: nombre del cliente para la reserva.
    """
    telefono = _fmt_phone(ctx.context if ctx else None)
    print(f"[tool] agendar_cita dia={dia!r} hora={hora!r} nombre={nombre!r} tel={telefono!r}")
    try:
        rows = sheets.read_range(availability.DEFAULT_RANGE)
        cell = availability.find_cell(rows, dia, hora)
        if cell is None:
            out = f"No encontre el dia '{dia}' o la hora '{hora}' en la agenda."
        elif not cell["is_free"]:
            out = f"Ese horario ({cell['day']} {cell['hour']}) ya esta ocupado."
        else:
            etiqueta = f"{nombre.strip()} ({telefono})" if telefono else nombre.strip()
            sheets.update_range(cell["a1"], [[etiqueta]])
            out = f"Cita confirmada: {cell['day']} a las {cell['hour']} a nombre de {nombre.strip()}."
    except Exception:  # noqa: BLE001
        print("[tool] agendar_cita ERROR:")
        traceback.print_exc()
        raise
    print(f"[tool] agendar_cita -> {out!r}")
    return out
