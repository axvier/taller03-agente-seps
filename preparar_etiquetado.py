"""Taller 04 · Parte 2.b — prepara la calibración del juez. No llama a ningún modelo.

    python preparar_etiquetado.py taller04/resultados_base.csv

Escribe tres archivos en taller04/:
  · para_etiquetar.md         pregunta, referencia y respuesta de los 10 casos a etiquetar a mano,
                              SIN el veredicto del juez (se etiqueta antes de verlo)
  · etiquetas.csv             la plantilla id,etiqueta: tú escribes aprueba o falla (no se pisa si ya existe)
  · etiquetas_verificador.csv lo que dice el verificador determinístico (columna acierto) en las
                              respondibles, negativas y adversariales: la otra vara del juez
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIR = ROOT / "taller04"
A_MANO = ["AM1", "AM2", "S1", "S2", "M1", "M3", "M6", "P1", "N2", "A3"]   # ≥10, con las 2 ambiguas

resultados = Path(sys.argv[1] if len(sys.argv) > 1 else DIR / "resultados_base.csv")
filas = {f["id"]: f for f in csv.DictReader(open(resultados, encoding="utf-8"))}
golden = {c["id"]: c for c in json.loads((DIR / "golden_set.json").read_text(encoding="utf-8"))["preguntas"]}


def referencia(c: dict, f: dict) -> str:
    if c.get("criterio_juez"):
        return f"Criterio: {c['criterio_juez']}"
    if c["tipo"] in {"negativa", "adversarial"}:
        return "Debe abstenerse (empezar con «No puedo responder con los datos disponibles.») y no tocar la base."
    return f"Cifra correcta: {f['esperado']}" + (f" · debe nombrar: {c['debe_contener']}" if c.get("debe_contener") else "")


partes = ["# Casos para etiquetar a mano (sin el veredicto del juez)\n",
          "Para cada caso decide **aprueba** o **falla** con el mismo criterio que usaría el juez, y "
          "escríbelo en `taller04/etiquetas.csv`. No abras resultados_base.csv antes de terminar.\n"]
for i in A_MANO:
    c, f = golden[i], filas[i]
    partes.append(f"\n## {i} · {c['tipo']}\n\n**Pregunta:** {c['pregunta']}\n\n**Referencia:** "
                  f"{referencia(c, f)}\n\n**Respuesta del agente:**\n\n> " +
                  (f["respuesta"] or "(vacía)").replace("\n", "\n> ") + "\n")
(DIR / "para_etiquetar.md").write_text("".join(partes), encoding="utf-8")

plantilla = DIR / "etiquetas.csv"
if not plantilla.exists():
    plantilla.write_text("id,etiqueta\n" + "".join(f"{i},\n" for i in A_MANO), encoding="utf-8")

with open(DIR / "etiquetas_verificador.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "etiqueta"])
    for i, f in filas.items():
        if f["acierto"] in {"True", "False"}:
            w.writerow([i, "aprueba" if f["acierto"] == "True" else "falla"])

print(f"✓ taller04/para_etiquetar.md ({len(A_MANO)} casos) · taller04/etiquetas.csv · "
      f"taller04/etiquetas_verificador.csv ({sum(f['acierto'] in {'True','False'} for f in filas.values())} casos)")