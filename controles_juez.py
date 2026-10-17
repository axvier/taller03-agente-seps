"""Taller 04 · Parte 2.b — casos de CONTROL para que la calibración del juez tenga dos clases.

Con el agente acertando 20/20, el juez aprobando 20/20 y las etiquetas humanas 10/10 «aprueba»,
el acuerdo es 1,0 pero kappa queda indefinido: no hay ni un solo «falla» con el que medir si el
juez sabe reprobar. Un juez que aprueba todo tendría el mismo resultado. Los controles son
respuestas escritas a propósito para las mismas preguntas del golden set, con un error conocido
(o con un redondeo que el criterio admite), y se juzgan con el MISMO juez, prompt y criterio.

    python controles_juez.py generar    # sin modelo: taller04/controles.csv + para_etiquetar_controles.md
                                        #             + etiquetas_controles.csv (plantilla para ti)
    python controles_juez.py juzgar     # ~19 llamadas al juez (Ollama, costo cero) y las dos calibraciones

Tipos de control:
  · trampa      la cifra del camino equivocado (sql_trampa del Taller 3: LIKE '1%', promedio de
                indicadores, cartera neta en vez de bruta)                     → debería fallar
  · desviada    la cifra correcta multiplicada por 1,12                        → debería fallar
  · inventada   una negativa respondida con una cifra inventada                → debería fallar
  · redondeada  la cifra correcta con un decimal («aproximadamente 5,2 %»)     → el criterio del
                juez admite redondeo; el verificador determinístico (tolerancia 0,05 %) no
"""
import csv
import importlib.util
import json
import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DIR = ROOT / "taller04"
DB = ROOT / os.getenv("AGENT_DB_PATH", "data/output/seps.sqlite")
REDONDEADAS = {"S2", "S3", "M5", "P2"}


def _lab():
    spec = importlib.util.spec_from_file_location(
        "evaluar_llmops", ROOT / "codigoreferencia" / "Lab-04-LLMOps" / "evaluar_llmops.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def es(x: float, dec: int = 2) -> str:
    """Formato español: 1.234.567,89"""
    s = f"{x:,.{dec}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def es_pct(c) -> bool:          # indicadores en %, montos en USD
    return any(k in c["pregunta"].lower() for k in ("roe", "roa", "morosidad", "liquidez"))


def generar():
    golden = json.loads((DIR / "golden_set.json").read_text(encoding="utf-8"))["preguntas"]
    base = {f["id"]: f for f in csv.DictReader(open(DIR / "resultados_base.csv", encoding="utf-8"))}
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    filas = []
    for c in golden:
        if c["tipo"] in {"simple", "multi"}:
            esperado = float(base[c["id"]]["esperado"])
            conteo = esperado.is_integer() and esperado < 1000 and not es_pct(c)
            unidad = lambda v: (f"{es(v)} %" if es_pct(c) else            # noqa: E731
                                f"{round(v)}" if conteo else f"USD {es(v)}")
            if c.get("sql_trampa"):
                v = con.execute(c["sql_trampa"]).fetchone()[0]
                filas.append(dict(id=f"C-{c['id']}-t", base=c["id"], tipo=c["tipo"], control="trampa",
                                  respuesta=f"La respuesta es {unidad(v)}, según la consulta a la base de la SEPS."))
            else:
                filas.append(dict(id=f"C-{c['id']}-d", base=c["id"], tipo=c["tipo"], control="desviada",
                                  respuesta=f"La respuesta es {unidad(esperado * 1.12)}, según la consulta a la base de la SEPS."))
            if c["id"] in REDONDEADAS:
                filas.append(dict(id=f"C-{c['id']}-r", base=c["id"], tipo=c["tipo"], control="redondeada",
                                  respuesta=f"Aproximadamente {es(round(esperado, 1), 1)} %, según la tabla de indicadores de la SEPS."))
        elif c["tipo"] == "negativa":
            filas.append(dict(id=f"C-{c['id']}-i", base=c["id"], tipo=c["tipo"], control="inventada",
                              respuesta="Fue de 7,45 %, según los registros de la SEPS."))
    con.close()
    for f in filas:
        f["pregunta"] = next(c["pregunta"] for c in golden if c["id"] == f["base"])
        f["esperado"] = base[f["base"]]["esperado"]
    cols = ["id", "base", "tipo", "control", "pregunta", "esperado", "respuesta"]
    with open(DIR / "controles.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    md = ["# Controles para etiquetar a mano (sin el veredicto del juez)\n",
          "Mismo criterio que antes: ¿la respuesta contesta lo preguntado con la cifra de referencia "
          "(se admite redondeo)? Negativas: ¿se abstiene sin inventar? Escribe aprueba o falla en "
          "taller04/etiquetas_controles.csv.\n"]
    for f in filas:
        ref = (f"Cifra correcta: {f['esperado']}" if f["esperado"] else
               "Debe abstenerse: la base no tiene el dato.")
        md.append(f"\n## {f['id']}\n\n**Pregunta:** {f['pregunta']}\n\n**Referencia:** {ref}\n\n"
                  f"**Respuesta:** {f['respuesta']}\n")
    (DIR / "para_etiquetar_controles.md").write_text("".join(md), encoding="utf-8")
    plantilla = DIR / "etiquetas_controles.csv"
    if not plantilla.exists():
        plantilla.write_text("id,etiqueta\n" + "".join(f"{f['id']},\n" for f in filas), encoding="utf-8")
    print(f"✓ {len(filas)} controles → taller04/controles.csv · para_etiquetar_controles.md · etiquetas_controles.csv")
    for f in filas:
        print(f"  {f['id']:10s} {f['control']:10s} {f['respuesta'][:70]}")


def juzgar():
    ev = _lab()
    juez = ev.Juez(os.getenv("JUEZ_MODEL"), os.getenv("JUEZ_BASE_URL"), os.getenv("JUEZ_API_KEY"))
    print(f"juez: {juez.modelo} · prompt {ev.JUEZ_VERSION} · temperature={juez.temperatura}")
    golden = {c["id"]: c for c in json.loads((DIR / "golden_set.json").read_text(encoding="utf-8"))["preguntas"]}
    filas = list(csv.DictReader(open(DIR / "controles.csv", encoding="utf-8")))
    for f in filas:
        c = golden[f["base"]]
        esperado = float(f["esperado"]) if f["esperado"] else None
        f.update(juez.evaluar(c["pregunta"], f["respuesta"], ev.CRITERIO_POR_TIPO[c["tipo"]],
                              ev._referencia(c, esperado)))
        abst = ev.T3.se_abstiene(f["respuesta"])
        f["acierto"] = (not abst and ev.T3.contiene_numero(f["respuesta"], esperado)) if esperado is not None else abst
        print(f"  {f['id']:10s} {f['control']:10s} verificador={'aprueba' if f['acierto'] else 'falla':8s} "
              f"juez={f['juez_veredicto']:8s} {f['juez_motivo'][:60]}")
    cols = list(filas[0].keys())
    with open(DIR / "controles_juez.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)

    base = list(csv.DictReader(open(DIR / "resultados_base.csv", encoding="utf-8")))
    todas = base + [{"id": f["id"], "juez_veredicto": f["juez_veredicto"]} for f in filas]
    ver = {f["id"]: ("aprueba" if f["acierto"] == "True" else "falla") for f in base if f["acierto"] in {"True", "False"}}
    ver |= {f["id"]: ("aprueba" if f["acierto"] else "falla") for f in filas}
    hum = ev.leer_etiquetas(DIR / "etiquetas.csv") | ev.leer_etiquetas(DIR / "etiquetas_controles.csv")
    print("\n== Juez vs verificador determinístico (20 casos reales + controles) ==")
    print(json.dumps(ev.calibrar(todas, ver), ensure_ascii=False, indent=2))
    print("\n== Juez vs etiquetas humanas (10 reales + controles) ==")
    print(json.dumps(ev.calibrar(todas, hum), ensure_ascii=False, indent=2))
    print("✓ taller04/controles_juez.csv")


if __name__ == "__main__":
    {"generar": generar, "juzgar": juzgar}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
