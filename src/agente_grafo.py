"""Taller 03 — Parte 4, Opción D: el bucle del AgenteSEPS como grafo de LangGraph, con aprobación.

Cinco nodos y sus aristas condicionales:

    START → router ─┬─(pide modificar datos)──────────────────────────────→ cierre → END
                    └─(consulta)→ modelo ─┬─(respuesta final o freno)──────→ cierre
                                          ├─(herramienta con efecto)→ aprobacion → herramientas
                                          └─(herramienta de lectura)───────────────→ herramientas
                                  herramientas ─┬─(repetición: freno F3)→ cierre
                                                └─(sigue)→ modelo

- router: regla de código (no LLM) que detecta pedidos de escritura y los manda a abstenerse
  sin gastar una sola llamada al modelo.
- modelo: una llamada con `tools=CATALOGO`; antes comprueba el tope de pasos [F1] y el
  presupuesto [F2].
- aprobacion: `interrupt` + checkpointer delante de lo que deja un efecto fuera de la
  conversación (generar_grafico escribe un archivo). La corrida se pausa y se reanuda desde
  el punto de control con la decisión de una persona.
- herramientas: ejecuta, con el detector de repetición [F3].
- cierre: arma la respuesta final, la abstención o el aviso de freno.

El grafo vive dentro de la clase del contrato con el Taller 4: AgenteSEPSGrafo().run(pregunta).
Decisión de aprobación (AGENT_APROBACION): "auto" (por defecto, para evaluar.py), "rechazar" o
"humano" (pregunta en la consola).
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .agente import ABSTENCION, SYSTEM_PROMPT, AgenteSEPS, _estimar_tokens, _limpiar
from .herramientas import CATALOGO, Sesion

REQUIERE_APROBACION = {"generar_grafico"}          # deja un archivo en disco: lo confirma una persona
PATRON_ESCRITURA = re.compile(
    r"\b(borr\w*|elimin\w*|actualiz\w*|modific\w*|insert\w*|cambi\w* (el|los|la|las) (saldo|dato|valor)\w*|"
    r"pon\w* (en|a) cero|delete|drop|update|truncate)\b", re.IGNORECASE)


class Estado(TypedDict, total=False):
    pregunta: str
    messages: list
    traza: list
    usage: dict
    llamadas: dict
    pendientes: list
    status: str
    answer: str
    paso: int


class AgenteSEPSGrafo(AgenteSEPS):
    """Mismo modelo, mismas herramientas, mismos frenos y mismo prompt que el baseline: lo único
    que cambia es que el bucle es un grafo explícito, con router y nodo de aprobación."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modo_aprobacion = os.getenv("AGENT_APROBACION", "auto")
        self.sesion: Sesion | None = None
        self.app = self._construir()

    # ---------------------------------------------------------------------------- nodos
    def _router(self, e: Estado) -> dict:
        if PATRON_ESCRITURA.search(e["pregunta"]):
            paso = self._paso(1, error=None, action={"name": "router", "args": {"decision": "modificacion"}},
                              observation={"ruta": "abstencion", "motivo": "la pregunta pide modificar datos"})
            return {"status": "abstencion_router", "traza": e["traza"] + [paso]}
        return {"status": "en_curso"}

    def _modelo(self, e: Estado) -> dict:
        paso = e["paso"] + 1
        if paso > self.max_pasos:                                                            # [F1]
            return {"status": "max_pasos"}
        previsto = e["usage"]["tokens_entrada"] + _estimar_tokens(e["messages"])
        if previsto > self.presupuesto:                                                      # [F2]
            return {"status": "presupuesto_agotado", "traza": e["traza"] + [
                self._paso(paso, error=f"presupuesto: {previsto} > {self.presupuesto} tokens")]}
        t0 = time.perf_counter()
        try:
            resp = self.cliente.chat.completions.create(
                model=self.model, messages=e["messages"], tools=CATALOGO, tool_choice="auto", temperature=0)
        except Exception as ex:  # noqa: BLE001
            return {"status": "error_modelo", "traza": e["traza"] + [
                self._paso(paso, latencia=time.perf_counter() - t0, error=f"{type(ex).__name__}: {ex}"[:300])]}
        lat = time.perf_counter() - t0
        te, ts = getattr(resp.usage, "prompt_tokens", 0) or 0, getattr(resp.usage, "completion_tokens", 0) or 0
        usage = {"tokens_entrada": e["usage"]["tokens_entrada"] + te, "tokens_salida": e["usage"]["tokens_salida"] + ts}
        msg = resp.choices[0].message
        if not msg.tool_calls:
            texto = _limpiar(msg.content)
            if not texto:
                return {"paso": paso, "usage": usage,
                        "traza": e["traza"] + [self._paso(paso, te, ts, lat, error="respuesta vacía")],
                        "messages": e["messages"] + [{"role": "user", "content": "Responde ahora, en máximo tres oraciones."}]}
            return {"paso": paso, "usage": usage, "status": "completed", "answer": texto,
                    "traza": e["traza"] + [self._paso(paso, te, ts, lat)]}
        llamadas = [{"id": c.id, "name": c.function.name, "arguments": c.function.arguments,
                     "tokens": (te, ts, lat) if i == 0 else (0, 0, 0.0)} for i, c in enumerate(msg.tool_calls)]
        asistente = {"role": "assistant", "content": msg.content or "",
                     "tool_calls": [{"id": c["id"], "type": "function",
                                     "function": {"name": c["name"], "arguments": c["arguments"]}} for c in llamadas]}
        return {"paso": paso, "usage": usage, "pendientes": llamadas, "messages": e["messages"] + [asistente]}

    def _aprobacion(self, e: Estado) -> dict:
        """Pausa el grafo. Lo que devuelve `interrupt` es la decisión de la persona al reanudar."""
        sensibles = [c for c in e["pendientes"] if c["name"] in REQUIERE_APROBACION]
        decision = interrupt({"pregunta": e["pregunta"],
                              "acciones": [{"herramienta": c["name"], "args": c["arguments"]} for c in sensibles]})
        if decision:
            return {}
        for c in sensibles:
            c["rechazada"] = True
        return {"pendientes": e["pendientes"]}

    def _herramientas(self, e: Estado) -> dict:
        llamadas, traza, mensajes = Counter(e["llamadas"]), list(e["traza"]), list(e["messages"])
        status = e["status"]
        for c in e["pendientes"]:
            te, ts, lat = c["tokens"]
            try:
                args = json.loads(c["arguments"] or "{}")
                clave = c["name"] + "|" + json.dumps(args, sort_keys=True, ensure_ascii=False)
                llamadas[clave] += 1
                if c.get("rechazada"):
                    obs = {"error": "una persona no aprobó esta acción; continúa sin ella"}
                elif llamadas[clave] > self.max_repeticiones:                                    # [F3]
                    obs = {"error": f"repetición: {c['name']} con los mismos argumentos más de {self.max_repeticiones} veces"}
                    status = "repeticion_detectada"
                else:
                    obs = self.sesion.ejecutar(c["name"], args)                                   # [C5]
            except json.JSONDecodeError as ex:
                args, obs = c["arguments"], {"error": f"argumentos con JSON inválido: {ex}"}
            traza.append(self._paso(e["paso"], te, ts, lat, action={"name": c["name"], "args": args}, observation=obs))
            mensajes.append({"role": "tool", "tool_call_id": c["id"],
                             "content": json.dumps(obs, ensure_ascii=False, default=str)})
        return {"llamadas": dict(llamadas), "traza": traza, "messages": mensajes, "pendientes": [], "status": status}

    def _cierre(self, e: Estado) -> dict:
        if e["status"] == "completed":
            return {}
        if e["status"] == "abstencion_router":
            return {"status": "completed",
                    "answer": f"{ABSTENCION} La pregunta pide modificar datos y este agente solo puede leer la base."}
        return {"answer": super()._cierre(e["status"], e["traza"])}

    # ---------------------------------------------------------------------------- aristas
    @staticmethod
    def _ruta_router(e: Estado) -> str:
        return "cierre" if e["status"] == "abstencion_router" else "modelo"

    @staticmethod
    def _ruta_modelo(e: Estado) -> str:
        if e["status"] != "en_curso":
            return "cierre"
        if not e.get("pendientes"):
            return "modelo"                            # respuesta vacía: se le pide responder
        if any(c["name"] in REQUIERE_APROBACION for c in e["pendientes"]):
            return "aprobacion"
        return "herramientas"

    @staticmethod
    def _ruta_herramientas(e: Estado) -> str:
        return "cierre" if e["status"] != "en_curso" else "modelo"

    def _construir(self):
        g = StateGraph(Estado)
        for nombre, fn in (("router", self._router), ("modelo", self._modelo), ("aprobacion", self._aprobacion),
                           ("herramientas", self._herramientas), ("cierre", self._cierre)):
            g.add_node(nombre, fn)
        g.add_edge(START, "router")
        g.add_conditional_edges("router", self._ruta_router, ["modelo", "cierre"])
        g.add_conditional_edges("modelo", self._ruta_modelo, ["modelo", "aprobacion", "herramientas", "cierre"])
        g.add_edge("aprobacion", "herramientas")
        g.add_conditional_edges("herramientas", self._ruta_herramientas, ["modelo", "cierre"])
        g.add_edge("cierre", END)
        return g.compile(checkpointer=InMemorySaver())   # sin checkpointer, interrupt no puede pausar

    # ---------------------------------------------------------------------------- contrato
    def _decidir(self, pedido: dict) -> bool:
        if self.modo_aprobacion == "rechazar":
            return False
        if self.modo_aprobacion == "humano":
            print(f"\n¿Apruebas estas acciones? {json.dumps(pedido['acciones'], ensure_ascii=False)}")
            return input("[s/n] ").strip().lower().startswith("s")
        return True

    def run(self, pregunta: str) -> dict:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]
        self.sesion = Sesion(run_id)
        config = {"configurable": {"thread_id": run_id}, "recursion_limit": 4 * self.max_pasos + 10}
        inicial: Estado = {"pregunta": pregunta, "paso": 0, "traza": [], "llamadas": {}, "pendientes": [],
                           "usage": {"tokens_entrada": 0, "tokens_salida": 0}, "status": "en_curso", "answer": "",
                           "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": pregunta}]}
        t0, aprobaciones = time.perf_counter(), []
        estado: dict[str, Any] = dict(inicial)
        try:
            salida = self.app.invoke(inicial, config)
            while "__interrupt__" in salida:                                   # pausa en el nodo de aprobación
                pedido = salida["__interrupt__"][0].value
                decision = self._decidir(pedido)
                aprobaciones.append({"acciones": pedido["acciones"], "aprobado": decision, "modo": self.modo_aprobacion})
                salida = self.app.invoke(Command(resume=decision), config)    # se reanuda desde el checkpoint
            estado = self.app.get_state(config).values
        except Exception as ex:  # noqa: BLE001
            estado = {**self.app.get_state(config).values} or estado
            estado["status"], estado["answer"] = "excepcion", f"La corrida falló por un error interno: {type(ex).__name__}: {ex}"
        finally:
            resultado = {"question": pregunta, "answer": estado.get("answer", ""), "trace": estado.get("traza", []),
                         "status": estado.get("status", "excepcion"), "model": self.model,
                         "usage": estado.get("usage", {"tokens_entrada": 0, "tokens_salida": 0}),
                         "run_id": run_id, "aprobaciones": aprobaciones, "arquitectura": "langgraph",
                         "latencia_total_s": round(time.perf_counter() - t0, 3)}
            self._escribir_traza(resultado)                                    # [C6] en todo camino
        return resultado


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--diagrama"]:
        from pathlib import Path
        os.environ.setdefault("AGENT_MODEL", "diagrama")
        from types import SimpleNamespace as NS
        mermaid = AgenteSEPSGrafo(cliente=NS(chat=None, models=None)).app.get_graph().draw_mermaid()
        Path("data/output").mkdir(parents=True, exist_ok=True)
        Path("data/output/grafo.mmd").write_text(mermaid, encoding="utf-8")
        print(mermaid)
    else:
        r = AgenteSEPSGrafo().run(" ".join(sys.argv[1:]) or "¿Cuántas cooperativas hay en la base?")
        print(f"modelo: {r['model']} · status: {r['status']} · pasos: {len(r['trace'])} · tokens: {r['usage']} · "
              f"aprobaciones: {r['aprobaciones']}")
        for p in r["trace"]:
            if p.get("error"):
                print(f"  paso {p['paso']} · ERROR: {p['error']}")
        print(f"\nrespuesta:\n{r['answer']}")