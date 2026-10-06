"""Taller 03 — Parte 2.c: muestra, sin llamar al modelo, la traza de una pregunta del golden set.

Busca en traces/agente la traza más reciente cuya pregunta coincide con la del id, y muestra
qué pidió el modelo, qué observó y qué respondió, junto a la verdad de sql_verificacion.

Uso:  python ver_traza.py M6
      python ver_traza.py M6 S2 S3
      python ver_traza.py --carpeta traces/grafo M1     (trazas de otra corrida)
"""
import glob
import json
import sqlite3
import sys
from pathlib import Path

DB = "data/output/seps.sqlite"
args = sys.argv[1:]
CARPETA = "traces/agente"
if "--carpeta" in args:
    i = args.index("--carpeta")
    CARPETA = args[i + 1]
    del args[i:i + 2]
golden = {p["id"]: p for p in json.loads(Path("golden_set.json").read_text(encoding="utf-8"))["preguntas"]}
trazas = sorted(glob.glob(f"{CARPETA}/traza-*.json"))

for pid in args:
    p = golden[pid]
    candidatas = [t for t in trazas if json.loads(Path(t).read_text(encoding="utf-8"))["question"] == p["pregunta"]]
    print(f"\n{'=' * 90}\n[{pid}] {p['tipo']} · {p['pregunta']}")
    if p.get("sql_verificacion"):
        with sqlite3.connect(f"file:{Path(DB).resolve()}?mode=ro", uri=True) as c:
            print(f"verdad (sql_verificacion): {c.execute(p['sql_verificacion']).fetchone()[0]}")
    if not candidatas:
        print(f"no hay traza en {CARPETA} para esta pregunta")
        continue
    t = json.loads(Path(candidatas[-1]).read_text(encoding="utf-8"))
    print(f"traza: {candidatas[-1]} · status: {t['status']} · tokens: {t['usage']} · {t.get('latencia_total_s')} s")
    for paso in t["trace"]:
        a, o = paso.get("action"), paso.get("observation")
        if a:
            args = a["args"].get("sql", a["args"]) if isinstance(a["args"], dict) else a["args"]
            print(f"\n  paso {paso['paso']} · {a['name']} · tokens {paso['tokens_entrada']}/{paso['tokens_salida']}")
            print(f"    pidió:   {args}")
            if isinstance(o, dict) and "filas" in o:
                print(f"    observó: columnas {o['columnas']} · {o['filas_total']} filas · primeras: {o['filas'][:5]}")
            else:
                print(f"    observó: {json.dumps(o, ensure_ascii=False, default=str)[:400]}")
        else:
            print(f"\n  paso {paso['paso']} · (respuesta final){' · ERROR: ' + paso['error'] if paso.get('error') else ''}")
    print(f"\n  respondió: {t['answer'][:600]}")