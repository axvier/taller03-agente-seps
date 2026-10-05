"""Taller 03 — Revisa el golden set ANTES de evaluar: ejecuta cada sql_verificacion en modo solo
lectura, comprueba que devuelva un número, muestra la entidad que debe nombrar la respuesta y
la cifra que daría el camino equivocado (sql_trampa).

Uso:  python verificar_golden.py              (solo revisa)
      python verificar_golden.py --completar   (además escribe en golden_set.json el
                                                debe_contener de las preguntas con sql_entidad)
"""
import json
import os
import sys
import sqlite3
import unicodedata
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
DB = Path(os.getenv("AGENT_DB_PATH", "data/output/seps.sqlite"))
RUTA = Path("golden_set.json")
datos = json.loads(RUTA.read_text(encoding="utf-8"))
golden = datos["preguntas"]
COMPLETAR = "--completar" in sys.argv
conn = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)


def uno(sql):
    filas = conn.execute(sql).fetchall()
    return filas, (filas[0][0] if filas else None)


def sugerir(nombre) -> str:
    if not nombre:
        return "(sin entidad)"
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().upper()
    for prefijo in ("COOPERATIVA DE AHORRO Y CREDITO ", "ASOCIACION MUTUALISTA DE AHORRO Y CREDITO PARA LA VIVIENDA "):
        s = s.replace(prefijo, "")
    return s.replace(" LTDA", "").replace(" LIMITADA", "").strip().lower()


conteo = {}
for p in golden:
    conteo[p["tipo"]] = conteo.get(p["tipo"], 0) + 1
    print(f"\n[{p['id']}] {p['tipo']} · {p['pregunta']}")
    if p["tipo"] in ("negativa", "adversarial"):
        print("    sin sql_verificacion: el acierto es abstenerse" + (" y dejar la base intacta" if p["tipo"] == "adversarial" else ""))
        continue
    filas, v = uno(p["sql_verificacion"])
    estado = "OK" if v is not None else "ERROR: no devuelve nada"
    if len(filas) > 1:
        estado += f" · AVISO: devuelve {len(filas)} filas, evaluar.py usa la primera"
    print(f"    verdad: {v}  [{estado}]")
    if "sql_entidad" in p:
        _, ent = uno(p["sql_entidad"])
        print(f"    entidad: {ent}")
        print(f"    debe_contener sugerido: [\"{sugerir(ent)}\"]  (actual: {p.get('debe_contener')})")
        if COMPLETAR and ent:
            p["debe_contener"] = [sugerir(ent)]
    if "sql_trampa" in p:
        _, t = uno(p["sql_trampa"])
        print(f"    camino equivocado daría: {t}  ← {p.get('_trampa', '')}")
print(f"\nconteo por tipo: {conteo} · total {len(golden)}")
if COMPLETAR:
    RUTA.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ {RUTA} actualizado con el debe_contener de las preguntas con sql_entidad")
pendientes = [p["id"] for p in golden if "COMPLETAR" in json.dumps(p.get("debe_contener", []))]
print("pendientes de completar:", pendientes or "ninguno")