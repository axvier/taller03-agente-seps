"""Taller 03 — Parte 3: los tres frenos, forzados con un «modelo» de guion (cero llamadas a la H200).

El freno es código del agente, no del modelo: aquí un cliente falso juega el papel del LLM y
devuelve siempre las mismas jugadas, para que cada freno salte de forma reproducible.
    F1 · tope de pasos         el guion nunca termina: consulta cosas distintas sin parar
    F2 · presupuesto de tokens el historial crece en cada paso hasta pasar el presupuesto
    F3 · detector de repetición el guion repite la misma herramienta con los mismos argumentos
    F3b · el bucle que F3 no ve: la misma consulta, escrita distinto cada vez; la detiene F1

Uso:  python probar_frenos.py            (los cuatro)
      python probar_frenos.py F2         (uno solo)
"""
import itertools
import json
import os
import sys
from types import SimpleNamespace as NS

os.environ["AGENT_MODEL"] = "guion-sin-llm"           # no se consulta /v1/models
os.environ["AGENT_TRACE_DIR"] = "traces/frenos"        # trazas separadas de la evaluación

from src.agente import AgenteSEPS  # noqa: E402  (después de fijar el entorno)


class ClienteGuion:
    """Imita al cliente de OpenAI. Los tokens de entrada se estiman del historial real que
    recibe, así que crecen igual que con un modelo de verdad: el historial se reenvía entero."""

    def __init__(self, jugadas):
        self.jugadas = jugadas
        self.n = 0
        self.chat = NS(completions=NS(create=self.create))
        self.models = NS(list=lambda: NS(data=[NS(id="guion-sin-llm")]))

    def create(self, messages, **_):
        self.n += 1
        nombre, args = next(self.jugadas)
        llamada = NS(id=f"c{self.n}", type="function", function=NS(name=nombre, arguments=json.dumps(args)))
        entrada = sum(len(json.dumps(m, ensure_ascii=False, default=str)) for m in messages) // 4
        return NS(choices=[NS(message=NS(content=None, tool_calls=[llamada]), finish_reason="tool_calls")],
                  usage=NS(prompt_tokens=entrada, completion_tokens=40))


ESCENARIOS = {
    "F1": dict(titulo="Tope de pasos: el guion nunca da una respuesta final",
               jugadas=(("consultar_sql", {"sql": f"SELECT COUNT(*) FROM entidades WHERE segmento = 'SEGMENTO {i % 3 + 1}' AND {i} = {i}"})
                        for i in itertools.count(1)),
               config=dict(max_pasos=4)),
    "F2": dict(titulo="Presupuesto de tokens: cada observación engorda el historial",
               jugadas=(("consultar_sql", {"sql": f"SELECT e.razon_social, i.* FROM indicadores i JOIN entidades e USING (ruc) WHERE i.fecha = '2026-08-31' AND {i} = {i}"})
                        for i in itertools.count(1)),
               config=dict(max_pasos=20, presupuesto_tokens=12_000)),
    "F3": dict(titulo="Detector de repetición: la misma herramienta con los mismos argumentos",
               jugadas=itertools.repeat(("consultar_sql", {"sql": "SELECT COUNT(*) FROM entidades"})),
               config=dict(max_pasos=10, max_repeticiones=2)),
    "F3b": dict(titulo="El bucle que F3 no ve: la misma consulta escrita distinto cada vez",
                jugadas=(("consultar_sql", {"sql": "SELECT COUNT(*) FROM entidades" + " " * i})
                         for i in itertools.count(0)),
                config=dict(max_pasos=5, max_repeticiones=2)),
}

for clave in sys.argv[1:] or ESCENARIOS:
    e = ESCENARIOS[clave]
    agente = AgenteSEPS(cliente=ClienteGuion(e["jugadas"]), **e["config"])
    r = agente.run(f"[{clave}] {e['titulo']}")
    print(f"\n{'=' * 90}\n{clave} · {e['titulo']}\nconfiguración: {e['config']}")
    print(f"status: {r['status']} · pasos: {len(r['trace'])} · tokens: {r['usage']} · traza: traces/frenos/traza-{r['run_id']}.json")
    acumulado = 0
    for p in r["trace"]:
        acumulado += p["tokens_entrada"]
        detalle = (p["observation"] or {}).get("error") if isinstance(p["observation"], dict) else None
        print(f"  paso {p['paso']}: tokens de entrada {p['tokens_entrada']:>6} · acumulado {acumulado:>6}"
              + (f" · {p['error']}" if p["error"] else "") + (f" · {detalle}" if detalle else ""))
    print(f"respuesta: {r['answer'][:300]}")