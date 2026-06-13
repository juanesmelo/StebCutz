"""Tools de agenda: consultar disponibilidad y agendar citas en el Google Sheet.

Las funciones decoradas con @function_tool se exponen automaticamente al modelo; su
firma y docstring generan el JSON schema de la tool (el SDK usa griffe/inspect).
"""

from agents import function_tool

import availability
import sheets


@function_tool
def consultar_disponibilidad(dia: str = "") -> str:
    """Consulta los horarios LIBRES de la barberia en el Google Sheet.

    Args:
        dia: dia de la semana a consultar (ej. "sabado"). Si se omite, devuelve el
            resumen de disponibilidad de toda la semana.
    """
    rows = sheets.read_range(availability.DEFAULT_RANGE)
    data = availability.parse(rows)
    if dia and dia.strip():
        day = availability.find_day(dia) or dia
        return availability.free_slots_text(day, data=data)
    return availability.summary_text(data=data)


@function_tool
def agendar_cita(dia: str, hora: str, nombre: str) -> str:
    """Agenda (reserva) una cita marcando la celda del Sheet con el nombre del cliente.

    Usa SIEMPRE una de las horas exactas que devuelve `consultar_disponibilidad`
    (por ejemplo "10:00AM"). Verifica que el horario siga libre antes de escribir.

    Args:
        dia: dia de la semana (ej. "sabado").
        hora: franja horaria exacta (ej. "10:00AM").
        nombre: nombre del cliente para la reserva.
    """
    rows = sheets.read_range(availability.DEFAULT_RANGE)
    cell = availability.find_cell(rows, dia, hora)
    if cell is None:
        return f"No encontre el dia '{dia}' o la hora '{hora}' en la agenda."
    if not cell["is_free"]:
        return f"Ese horario ({cell['day']} {cell['hour']}) ya esta ocupado."
    sheets.update_range(cell["a1"], [[nombre.strip()]])
    return f"Cita confirmada: {cell['day']} a las {cell['hour']} a nombre de {nombre.strip()}."
