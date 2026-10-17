"""Taller 04 — reemplaza en un resultados.csv las filas de los casos que se volvieron a correr.

    python reemplazar_filas.py taller04/resultados_v2.csv taller04/resultados_v2_rerun.csv

Se usa cuando unos pocos casos fallaron por la infraestructura (VPN, servidor) y no por el
agente: se corren solo esos con --solo y se reemplazan sus filas, sin repetir los demás.
"""
import csv
import sys

destino, nuevas = sys.argv[1], sys.argv[2]
filas = list(csv.DictReader(open(destino, encoding="utf-8")))
cols = list(filas[0].keys())
reemplazo = {f["id"]: f for f in csv.DictReader(open(nuevas, encoding="utf-8"))}
filas = [reemplazo.get(f["id"], f) for f in filas]
with open(destino, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(filas)
print(f"✓ {destino}: reemplazadas {sorted(reemplazo)}; excepciones que quedan: "
      f"{[f['id'] for f in filas if f['estado'] == 'excepcion']}")
