"""Taller 03 — Parte 2.b: tabla comparativa de los dos agentes, derivada de los CSV crudos de evaluar.py.

Uso:  python comparar_resultados.py resultados_agente.csv resultados_andamiaje.csv
"""
import csv
import sys
from pathlib import Path

RESPONDIBLES, NEGATIVAS = {"simple", "multi"}, {"negativa", "adversarial"}
si = lambda v: str(v).strip().lower() == "true"


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tasa(filas, campo):
    return f"{sum(si(f[campo]) for f in filas) / len(filas):.3f} ({sum(si(f[campo]) for f in filas)} de {len(filas)})" if filas else "—"


def resumen(filas):
    resp = [f for f in filas if f["tipo"] in RESPONDIBLES]
    neg = [f for f in filas if f["tipo"] in NEGATIVAS]
    adv = [f for f in filas if f["tipo"] == "adversarial"]
    pasos = [int(f["pasos"]) for f in filas if f["pasos"].isdigit()]
    tokens = [int(f["tokens_entrada"]) for f in filas if f["tokens_entrada"].isdigit()]
    return {
        "Exactitud (respondibles)": tasa(resp, "acierto"),
        "Abstención correcta (negativas + adversariales)": tasa(neg, "abstencion"),
        "Abstención indebida (respondibles)": tasa(resp, "abstencion"),
        "Base intacta en adversariales": tasa(adv, "base_intacta"),
        "Pasos medios": f"{sum(pasos) / len(pasos):.1f}" if pasos else "—",
        "Errores de herramienta (total)": sum(int(f["errores_herramienta"] or 0) for f in filas if f["errores_herramienta"].isdigit()),
        "Excepciones": sum(1 for f in filas if f["estado"] == "excepcion"),
        "Tokens de entrada (total)": f"{sum(tokens):,}" if tokens else "la traza no trae tokens",
        "Segundos (total)": f"{sum(float(f['segundos'] or 0) for f in filas):.1f}",
        "Modelo": ", ".join(sorted({f["modelo"] for f in filas if f["modelo"]})) or "—",
    }


archivos = sys.argv[1:] or ["resultados_agente.csv", "resultados_andamiaje.csv"]
datos = {Path(a).stem: leer(a) for a in archivos}
res = {n: resumen(f) for n, f in datos.items()}
print("| Métrica | " + " | ".join(res) + " |")
print("|---|" + "---|" * len(res))
for m in next(iter(res.values())):
    print(f"| {m} | " + " | ".join(str(r[m]) for r in res.values()) + " |")

print("\n| id | tipo | " + " | ".join(f"{n} (acierto · pasos · errores)" for n in datos) + " |")
print("|---|---|" + "---|" * len(datos))
por_id = {n: {f["id"]: f for f in filas} for n, filas in datos.items()}
for f in next(iter(datos.values())):
    celdas = []
    for n in datos:
        g = por_id[n].get(f["id"], {})
        celdas.append(f"{'✔' if si(g.get('acierto')) else '✘'} · {g.get('pasos', '')} · {g.get('errores_herramienta', '')}"
                      + (f" · {g.get('estado')}" if g.get("estado") not in ("completed", None) else ""))
    print(f"| {f['id']} | {f['tipo']} | " + " | ".join(celdas) + " |")