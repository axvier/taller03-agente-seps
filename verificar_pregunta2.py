"""Taller 03 — Parte 5, pregunta 2: reúne las cifras que pide la pregunta (sin llamar al modelo).

Lee resultados_agente.csv, resultados_andamiaje.csv, la traza del F2 y el .env, y calcula el
peor caso de tokens al duplicar el tope de pasos.
Uso:  python verificar_pregunta2.py
"""
import csv
import glob
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def resumen(ruta):
    filas = list(csv.DictReader(open(ruta, encoding="utf-8")))
    pasos = [int(f["pasos"]) for f in filas if f["pasos"].isdigit()]
    tokens = [int(f["tokens_entrada"]) for f in filas if f["tokens_entrada"].isdigit()]
    return len(filas), sum(pasos) / len(pasos), sum(tokens), (sum(tokens) / len(tokens) if tokens else None)


print("== 1. Tus CSV ==")
for nombre in ("resultados_agente.csv", "resultados_grafo.csv", "resultados_andamiaje.csv"):
    if Path(nombre).exists():
        n, pasos, tok, prom = resumen(nombre)
        print(f"{nombre}: {n} preguntas · pasos medios {pasos:.2f} · tokens de entrada {tok:,}"
              + (f" · {prom:,.0f} por pregunta" if prom else " · la traza no trae tokens"))

print("\n== 2. Traza del F2 (presupuesto) ==")
f2 = None
for t in sorted(glob.glob("traces/frenos/traza-*.json")):
    d = json.load(open(t, encoding="utf-8"))
    if d["question"].startswith("[F2]"):
        f2 = d
por_paso = [p["tokens_entrada"] for p in f2["trace"] if p["tokens_entrada"]]
difs = [b - a for a, b in zip(por_paso, por_paso[1:])]
base, pendiente = por_paso[0], round(sum(difs) / len(difs))
print(f"tokens por paso: {por_paso}")
print(f"diferencia entre pasos: {difs} → pendiente media {pendiente}")
acum = lambda n: base * n + pendiente * n * (n - 1) // 2
print(f"fórmula acumulado(n) = {base}·n + {pendiente}·n(n−1)/2 → con {len(por_paso)} pasos da {acum(len(por_paso)):,} "
      f"(medido: {sum(por_paso):,})")

print("\n== 3. Duplicar el tope de pasos ==")
tope = int(os.getenv("AGENT_MAX_PASOS", 8))
presupuesto = int(os.getenv("AGENT_PRESUPUESTO_TOKENS", 60_000))
print(f"tope actual: {tope} · presupuesto: {presupuesto:,}")
print(f"peor caso con {tope} pasos: {acum(tope):,} · con {2 * tope}: {acum(2 * tope):,} · razón {acum(2 * tope) / acum(tope):.2f}")
corte = next(n for n in range(1, 200) if acum(n + 1) > presupuesto)
print(f"el presupuesto corta después de {corte} llamadas (la siguiente llevaría el acumulado a {acum(corte + 1):,})")

print("\n== 4. Pendiente real en tu evaluación (traces/agente) ==")
pend = []
for t in glob.glob("traces/agente/traza-*.json"):
    v = [p["tokens_entrada"] for p in json.load(open(t, encoding="utf-8"))["trace"] if p["tokens_entrada"]]
    pend += [b - a for a, b in zip(v, v[1:])]
if pend:
    print(f"diferencia media entre pasos en preguntas reales: {sum(pend) / len(pend):.0f} tokens ({len(pend)} pares de pasos)")