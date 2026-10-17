"""Taller 04 · Parte 2.c — escribe taller04/prompt_v2.txt (la mejora). No llama al modelo.

Diagnóstico (spans de la corrida base): el 93,8 % del tiempo está en el modelo, y 16 de las 18
corridas que llegaron al agente gastaron una vuelta completa de modelo solo para llamar a
describir_esquema, cuya respuesta es SIEMPRE la misma. La v2 trae ese esquema dentro del
prompt (lo genera la misma herramienta, así no se escribe a mano ni se desactualiza) y agrega
una regla para preguntas ambiguas: declarar la lectura elegida en la primera oración.
"""
import json
from pathlib import Path

from src import agente as base
from src.herramientas import Sesion

ROOT = Path(__file__).resolve().parent
esquema = Sesion("prompt-v2").describir_esquema()

v1 = base.SYSTEM_PROMPT
paso1_v1 = ("1. Si no conoces las tablas, llama primero a describir_esquema. No adivines nombres de "
            "tablas ni columnas.")
paso1_v2 = ("1. El esquema de la base está al final de estas instrucciones: úsalo directamente y NO "
            "llames a describir_esquema, salvo que una consulta falle por un nombre de tabla o columna.")
v2 = v1.replace(paso1_v1, paso1_v2)
if v2 == v1:
    raise SystemExit("No encontré la regla 1 del prompt v1 en src/agente.py: no se generó la v2.")
v2 += ("\n\nPreguntas ambiguas: si la pregunta admite más de una lectura (qué cartera, qué mes, qué "
       "criterio de tamaño), elige la más razonable y DECLÁRALA en la primera oración, por ejemplo "
       "«Tomo la cartera bruta entre enero y agosto de 2026: …».\n\n"
       "ESQUEMA DE LA BASE (lo mismo que devuelve describir_esquema):\n"
       + json.dumps(esquema, ensure_ascii=False, separators=(",", ":")))

salida = ROOT / "taller04" / "prompt_v2.txt"
salida.write_text(v2, encoding="utf-8")
print(f"v1: {len(v1):,} caracteres (~{len(v1)//4:,} tokens) · v2: {len(v2):,} caracteres (~{len(v2)//4:,} tokens)")
print(f"regla 1 reemplazada: {'NO llames a describir_esquema' in v2} · regla de ambiguas: {'DECLÁRALA' in v2}")
print(f"✓ {salida.relative_to(ROOT)}")
