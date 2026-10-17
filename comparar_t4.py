"""Taller 04 · Parte 2.c — antes (v1) y después (v2), caso por caso. No llama al modelo.

    python comparar_t4.py taller04/resultados_base.csv taller04/resultados_v2.csv

Mismo golden set, mismo evaluador, mismo modelo y mismo juez: solo cambia el prompt. Para
separar el cambio del azar no basta comparar totales: se cuenta en cuántos de los casos
pareados bajaron los tokens y se calcula la prueba de signos (binomial, dos colas). Con 20
casos, una diferencia de exactitud de un caso (5 %) está dentro de la resolución del golden set.
"""
import csv
import sys
from math import comb


def leer(ruta):
    return {f["id"]: f for f in csv.DictReader(open(ruta, encoding="utf-8"))}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def signos(bajan: int, suben: int) -> float:
    n, k = bajan + suben, min(bajan, suben)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0


a, b = leer(sys.argv[1]), leer(sys.argv[2])
ids = [i for i in a if i in b]
print(f"{'id':5} {'tipo':11} {'acierto':>13} {'juez':>17} {'pasos':>7} {'tok_entrada':>15} {'seg':>11}")
for i in ids:
    x, y = a[i], b[i]
    print(f"{i:5} {x['tipo']:11} {x['acierto'] or '—':>6}→{y['acierto'] or '—':<6} "
          f"{x['juez_veredicto']:>8}→{y['juez_veredicto']:<8} {x['pasos']:>3}→{y['pasos']:<3} "
          f"{x['tokens_entrada']:>7}→{y['tokens_entrada']:<7} {x['segundos']:>5}→{y['segundos']:<5}")


def total(d, k):
    return sum(num(d[i][k]) or 0 for i in ids)


def tasa(d, k, tipos):
    xs = [d[i] for i in ids if d[i]["tipo"] in tipos and d[i][k] != ""]
    return f"{sum(x[k] in ('True', 'aprueba') for x in xs)}/{len(xs)}"


print("\nresumen                 v1 → v2")
print(f"exactitud respondibles  {tasa(a,'acierto',{'simple','multi'})} → {tasa(b,'acierto',{'simple','multi'})}")
print(f"abstención correcta     {tasa(a,'acierto',{'negativa','adversarial'})} → {tasa(b,'acierto',{'negativa','adversarial'})}")
print(f"juez aprueba (todos)    {tasa(a,'juez_veredicto',{'simple','multi','negativa','adversarial','ambigua'})} → "
      f"{tasa(b,'juez_veredicto',{'simple','multi','negativa','adversarial','ambigua'})}")
for k in ("pasos", "tokens_entrada", "tokens_salida", "segundos"):
    print(f"{k:23} {total(a,k):,.0f} → {total(b,k):,.0f}  ({100*(total(b,k)/total(a,k)-1):+.1f} %)" if total(a, k) else k)
for k in ("tokens_entrada", "pasos"):
    pares = [(num(a[i][k]), num(b[i][k])) for i in ids if num(a[i][k]) and num(b[i][k]) is not None]
    bajan = sum(y < x for x, y in pares)
    suben = sum(y > x for x, y in pares)
    print(f"{k}: bajan en {bajan}, suben en {suben}, iguales en {len(pares)-bajan-suben} de {len(pares)} "
          f"casos con agente · prueba de signos p = {signos(bajan, suben):.4f}")
