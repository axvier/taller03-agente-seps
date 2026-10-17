"""Taller 04 — registra el prompt del agente en Langfuse (Prompt Management), con su mensaje.

    python registrar_prompt.py v1                      # el prompt del Taller 3 → etiqueta production
    python registrar_prompt.py v2 --archivo taller04/prompt_v2.txt --mensaje "por qué cambia"
                                                       # el candidato → etiqueta candidata

No llama al modelo. Langfuse numera las versiones solo (1, 2, …); el agente las lee por etiqueta
y anota en cada traza la versión con la que corrió (prompt_version).
"""
import argparse
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
from langfuse import get_client  # noqa: E402

from src import agente as base  # noqa: E402
from src.agente_t4 import PROMPT_NOMBRE  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("cual", choices=["v1", "v2"])
ap.add_argument("--archivo")
ap.add_argument("--mensaje")
a = ap.parse_args()

lf = get_client()
if a.cual == "v1":
    texto, etiqueta = base.SYSTEM_PROMPT, "production"
    mensaje = a.mensaje or "v1: el prompt del Taller 3 tal cual (línea base)"
else:
    if not a.archivo or not a.mensaje:
        ap.error("v2 necesita --archivo y --mensaje")
    texto, etiqueta, mensaje = Path(a.archivo).read_text(encoding="utf-8").strip(), "candidata", a.mensaje

p = lf.create_prompt(name=PROMPT_NOMBRE, type="text", prompt=texto, labels=[etiqueta],
                     commit_message=mensaje)
lf.flush()
print(f"Registrado {PROMPT_NOMBRE} versión {p.version} con etiqueta «{etiqueta}»: {mensaje}")
