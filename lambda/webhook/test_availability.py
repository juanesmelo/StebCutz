"""Tests del parser de disponibilidad.

No requieren red ni google-auth (parse() trabaja sobre filas en memoria).
Ejecuta:  python test_availability.py     (o con pytest si esta disponible)
"""

import availability as av

# Matriz de ejemplo con filas IRREGULARES (la API omite celdas vacias al final):
#   - 11:00AM: faltan Sábado y Domingo -> deben contar como LIBRES.
#   - fila sin hora -> se ignora.
ROWS = [
    ["Horas", "Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sábado", "Domingo"],
    ["9:00AM", "Ocupado", "Ocupado", "Ocupado", "Ocupado", "Ocupado", "", "Ocupado"],
    ["11:00AM", "Ocupado", "Ocupado", "Ocupado", "Ocupado", "Ocupado"],
    ["9:00PM", "", "Ocupado", "Ocupado", "", "", "", "Ocupado"],
    ["", "x"],
]


def test_ignora_fila_sin_hora():
    assert av.parse(ROWS)["hours"] == ["9:00AM", "11:00AM", "9:00PM"]


def test_fila_corta_cuenta_como_libre():
    data = av.parse(ROWS)
    assert av.free_slots("domingo", data=data) == ["11:00AM"]
    assert av.free_slots("sabado", data=data) == ["9:00AM", "11:00AM", "9:00PM"]


def test_acepta_tildes_y_mayusculas():
    data = av.parse(ROWS)
    assert av.free_slots("SÁBADO", data=data) == ["9:00AM", "11:00AM", "9:00PM"]


def test_dia_ocupado_todo_no_tiene_cupos():
    assert av.free_slots("martes", data=av.parse(ROWS)) == []


def test_find_day_ignora_puntuacion_y_tildes():
    assert av.find_day("¿tienes cita el sábado?") == "Sábado"
    assert av.find_day("quiero el VIERNES") == "Viernes"
    assert av.find_day("hola buenas") is None


def test_parse_matriz_vacia():
    data = av.parse([])
    assert data["days"] == [] and data["free"] == {}


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("ok:", fn.__name__)
    print(f"\n{len(tests)} tests OK")
