"""Parser de disponibilidad de la barberia a partir de la matriz del Google Sheet.

Estructura esperada del Sheet (primera hoja):

    Fila 1 (cabecera):  Horas | Lunes | Martes | ... | Domingo
    Filas siguientes :  <hora> | <celda por dia>

Regla de interpretacion de cada celda de dia:
    - celda VACIA (o ausente)  -> el horario esta LIBRE
    - celda CON TEXTO ("Ocupado", un nombre, etc.) -> el horario esta OCUPADO

Ojo: la API de Sheets omite las celdas vacias al final de cada fila, por lo que las
filas pueden venir "cortas". Los dias que falten se completan como vacios = LIBRES.

El modulo no depende de google-auth a nivel de import: `sheets` se importa de forma
perezosa dentro de load_matrix(), asi parse()/free_slots() son testeables en aislado.
"""

import re
import unicodedata

# Cubre la columna de Horas (A) + 7 dias (B..H) y franjas de sobra.
DEFAULT_RANGE = "A1:H100"

# Dias canonicos en espanol (clave normalizada -> nombre visible) para detectar el dia
# mencionado en un mensaje, independientemente de como este escrita la cabecera.
_CANON_DAYS = {
    "lunes": "Lunes",
    "martes": "Martes",
    "miercoles": "Miércoles",
    "jueves": "Jueves",
    "viernes": "Viernes",
    "sabado": "Sábado",
    "domingo": "Domingo",
}

# Palabras que disparan el resumen completo de disponibilidad.
_SUMMARY_WORDS = {
    "disponibilidad",
    "disponible",
    "disponibles",
    "horario",
    "horarios",
    "citas",
    "cita",
    "agenda",
    "cupos",
    "cupo",
}


def _norm(text):
    """minusculas, sin tildes y sin espacios sobrantes (para comparar dias/palabras)."""
    text = (text or "").strip().lower()
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _words(text):
    """Tokens alfanumericos del texto normalizado (ignora puntuacion: '¿sábado?' -> 'sabado')."""
    return re.findall(r"[a-z0-9]+", _norm(text))


def load_matrix(a1_range=DEFAULT_RANGE):
    """Lee la matriz cruda del Sheet (lista de filas). Import perezoso de `sheets`."""
    import sheets  # noqa: PLC0415 - perezoso a proposito (evita cargar google-auth si no se usa)

    return sheets.read_range(a1_range)


def parse(rows):
    """Convierte la matriz cruda en disponibilidad estructurada.

    Devuelve un dict:
        {
          "days":  ["Lunes", ..., "Domingo"],            # nombres tal cual la cabecera
          "hours": ["9:00AM", ...],                      # franjas en orden de aparicion
          "free":  {"<dia normalizado>": ["9:00AM", ...]},
          "by_day": {"Lunes": ["9:00AM", ...], ...},     # idem con el nombre visible
        }
    """
    empty = {"days": [], "hours": [], "free": {}, "by_day": {}}
    if not rows:
        return empty

    header = rows[0]
    days = [d.strip() for d in header[1:] if d and d.strip()]
    if not days:
        return empty
    n_days = len(days)

    hours = []
    free = {_norm(d): [] for d in days}
    by_day = {d: [] for d in days}

    for row in rows[1:]:
        if not row or not (row[0] or "").strip():
            continue  # fila sin etiqueta de hora -> se ignora
        hour = row[0].strip()
        hours.append(hour)

        # Celdas de los dias; las que falten al final se rellenan vacias (= libres).
        cells = list(row[1:1 + n_days])
        cells += [""] * (n_days - len(cells))

        for day, cell in zip(days, cells):
            if not (cell or "").strip():  # vacio => libre
                free[_norm(day)].append(hour)
                by_day[day].append(hour)

    return {"days": days, "hours": hours, "free": free, "by_day": by_day}


def free_slots(day, data=None, rows=None):
    """Lista de horas libres para un dia (acepta nombre con/sin tilde y mayus/minus)."""
    if data is None:
        data = parse(rows if rows is not None else load_matrix())
    return data["free"].get(_norm(day), [])


def find_day(text):
    """Devuelve el nombre de dia (visible) mencionado en el texto, o None."""
    tokens = set(_words(text))
    for key, display in _CANON_DAYS.items():
        if key in tokens:
            return display
    return None


def free_slots_text(day, data=None, rows=None):
    """Texto listo para responder con los horarios libres de un dia."""
    slots = free_slots(day, data=data, rows=rows)
    if not slots:
        return f"No hay horarios libres el {day.lower()}. 😕"
    cuerpo = "\n".join(f"• {s}" for s in slots)
    return f"Horarios libres el {day.lower()}:\n{cuerpo}"


def summary_text(data=None, rows=None):
    """Resumen de disponibilidad por dia, listo para responder."""
    if data is None:
        data = parse(rows if rows is not None else load_matrix())
    if not data["days"]:
        return "No pude leer la disponibilidad."
    lineas = []
    for day in data["days"]:
        slots = data["by_day"][day]
        if slots:
            lineas.append(f"*{day}*: {', '.join(slots)}")
        else:
            lineas.append(f"*{day}*: sin cupos libres")
    return "Disponibilidad:\n" + "\n".join(lineas)


def reply_for(text):
    """Enruta un mensaje a una respuesta de disponibilidad.

    Devuelve el texto de respuesta si el mensaje es una consulta de disponibilidad
    (menciona un dia o una palabra clave); si no aplica, devuelve None.
    """
    day = find_day(text)
    if day:
        data = parse(load_matrix())
        return free_slots_text(day, data=data)
    if any(w in _SUMMARY_WORDS for w in _words(text)):
        return summary_text()
    return None
