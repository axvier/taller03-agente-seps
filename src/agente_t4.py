"""Taller 04 — Parte 1: el agente del Taller 3, observado con Langfuse y con guardrails.

    python -m src.agente_t4 "¿Cuál fue el activo total de Mushuc Runa en agosto de 2026?"

No se modifica src/agente.py: este módulo envuelve AgenteSEPS y le inyecta, por corrida, el
prompt versionado de Langfuse, una Sesion de herramientas que deja un span por llamada y un
cliente de OpenAI que deja una generation por llamada al modelo.

Árbol de cada traza (los cuatro tipos que pide la Parte 1):
    corrida (agent, raíz) ─┬─ guardrail_entrada (guardrail)
                           ├─ llm (generation)  ×n      ← langfuse.openai, con tokens y prompt
                           ├─ <herramienta> (tool) ×n   ← describir_esquema, consultar_sql, …
                           └─ guardrail_salida (guardrail)

Las tres fallas de la Parte 0.c, corregidas:
    1. el cronómetro arranca ANTES del guardrail de entrada (la latencia incluye guardrails);
    2. la traza se cierra en un `finally`: también si el agente lanza una excepción;
    3. el dato personal se redacta antes de llegar a cualquier traza: el agente recibe la
       pregunta redactada y la máscara de Langfuse (`enmascarar`) corre sobre todo lo que se envía.

Devuelve el contrato del Taller 3 más tres claves que lee evaluar_llmops.py:
    traza_id, prompt_version y guardrail {"entrada": ok|redactada|bloqueada, "salida": …}.
"""
from __future__ import annotations

import json
import os
import time
from types import SimpleNamespace

from dotenv import load_dotenv

from . import agente as base
from .guardrails_seps import (detectar_clave, detectar_inyeccion, enmascarar, redactar,
                              validar_entrada, validar_salida)
from .herramientas import ROOT, Sesion

load_dotenv(ROOT / ".env")

from langfuse import Langfuse, propagate_attributes  # noqa: E402
from langfuse.openai import OpenAI                    # noqa: E402  (OpenAI con generations)

# La máscara se registra al crear el cliente: corre en el proceso, ANTES de enviar nada.
LF = Langfuse(mask=enmascarar)

PROMPT_NOMBRE = "seps-analista"
TAGS = ["taller-04", "seps"]
TRAZAS_T4 = ROOT / "traces" / "t4"          # las trazas locales del T4, aparte de las del T3
ABSTENCION = base.ABSTENCION


def cargar_prompt(etiqueta: str):
    """(texto, versión, prompt_client). Sin Langfuse, el prompt del Taller 3 como 'v1-local'."""
    try:
        p = LF.get_prompt(PROMPT_NOMBRE, label=etiqueta, cache_ttl_seconds=0)
        return p.compile(), f"v{p.version}", p
    except Exception:  # noqa: BLE001 — sin servidor o sin prompt registrado
        return base.SYSTEM_PROMPT, "v1-local", None


def _resumen(obs) -> str:
    """Lo que el span de la herramienta guarda como output: acotado, no la tabla entera."""
    return json.dumps(obs, ensure_ascii=False, default=str)[:1500]


class SesionObservada(Sesion):
    """Cada herramienta, un span de tipo tool; un {"error": …} lo marca en nivel ERROR."""

    def ejecutar(self, nombre: str, args) -> dict:
        with LF.start_as_current_observation(name=nombre, as_type="tool", input=args) as span:
            obs = super().ejecutar(nombre, args)
            fallo = isinstance(obs, dict) and "error" in obs
            span.update(output=_resumen(obs), level="ERROR" if fallo else "DEFAULT",
                        status_message=str(obs["error"])[:300] if fallo else None)
        return obs


class _Completions:
    def __init__(self, real, extra):
        self._real, self._extra = real, extra

    def create(self, **kwargs):
        return self._real.create(**kwargs, **self._extra)


class _ClienteObservado:
    """El cliente de langfuse.openai, con el nombre del span y el prompt ligado en cada llamada."""

    def __init__(self, extra: dict):
        real = OpenAI()                                   # OPENAI_BASE_URL / OPENAI_API_KEY
        self.models = real.models
        self.chat = SimpleNamespace(completions=_Completions(real.chat.completions, extra))


class _AgenteT4(base.AgenteSEPS):
    """La traza local (traces/t4) también pasa por la máscara: ningún dato personal en disco."""

    def _escribir_traza(self, resultado: dict) -> None:
        super()._escribir_traza(enmascarar(data=resultado))


class AgenteSEPSObs:
    """Contrato del Taller 3: AgenteSEPSObs().run(pregunta) -> dict."""
    ETIQUETA = os.getenv("AGENT_PROMPT_LABEL", "production")
    SESION_ID = "golden-base"

    def __init__(self, etiqueta: str | None = None, sesion_id: str | None = None):
        self.etiqueta = etiqueta or self.ETIQUETA
        self.sesion_id = sesion_id or self.SESION_ID
        self.texto_prompt, self.prompt_version, prompt = cargar_prompt(self.etiqueta)
        extra = {"name": "llm"} | ({"langfuse_prompt": prompt} if prompt else {})
        self.agente = _AgenteT4(cliente=_ClienteObservado(extra))
        self.model = self.agente.model

    # -------------------------------------------------------------------------------------------
    def run(self, pregunta: str) -> dict:
        t0 = time.perf_counter()                          # [0.c-2] antes del guardrail
        guard = {"entrada": "ok", "salida": "ok"}
        r = {"question": redactar(pregunta), "answer": "", "trace": [], "status": "en_curso",
             "model": self.model, "usage": {"tokens_entrada": 0, "tokens_salida": 0}}
        traza_id = None
        try:
            with propagate_attributes(session_id=self.sesion_id, tags=TAGS + [self.prompt_version],
                                      metadata={"prompt_version": self.prompt_version}):
                with LF.start_as_current_observation(name="corrida", as_type="agent",
                                                     input={"pregunta": pregunta}) as raiz:
                    traza_id = LF.get_current_trace_id()
                    try:
                        # ---- guardrail de entrada: G1 inyección (bloquea), G2 PII (redacta)
                        with LF.start_as_current_observation(name="guardrail_entrada",
                                                             as_type="guardrail", input=pregunta) as g:
                            ok, texto = validar_entrada(pregunta)
                            guard["entrada"] = ("bloqueada" if not ok else
                                                "redactada" if texto != pregunta else "ok")
                            g.update(output={"decision": guard["entrada"],
                                             "motivos": detectar_inyeccion(pregunta)},
                                     level="DEFAULT" if guard["entrada"] == "ok" else "WARNING")
                        if not ok:
                            r.update(answer=f"{ABSTENCION} {texto}", status="bloqueada_entrada")
                        else:
                            # ---- el agente del Taller 3, con prompt, herramientas y trazas del T4
                            base.SYSTEM_PROMPT = self.texto_prompt
                            base.Sesion = SesionObservada
                            base.TRAZAS = TRAZAS_T4
                            r = self.agente.run(texto)            # [0.c-3] recibe el texto redactado
                            # ---- guardrail de salida: G3 claves (bloquea), G2 PII (redacta)
                            with LF.start_as_current_observation(name="guardrail_salida",
                                                                 as_type="guardrail",
                                                                 input=r["answer"]) as g:
                                ok_s, salida = validar_salida(r["answer"])
                                guard["salida"] = ("bloqueada" if not ok_s else
                                                   "redactada" if salida != r["answer"] else "ok")
                                g.update(output={"decision": guard["salida"],
                                                 "clave": detectar_clave(r["answer"])},
                                         level="DEFAULT" if guard["salida"] == "ok" else "WARNING")
                            r["answer"] = salida if ok_s else f"{ABSTENCION} {salida}"
                    except Exception as e:  # noqa: BLE001 — [0.c-3] el fallo queda en la traza
                        r.update(status="excepcion",
                                 answer=f"La corrida falló por un error interno: {type(e).__name__}: {e}")
                    finally:
                        r["latencia_total_s"] = round(time.perf_counter() - t0, 3)
                        error = r["status"] in {"excepcion", "error_modelo"}
                        raiz.update(output={"respuesta": r["answer"], "status": r["status"],
                                            "guardrail": guard, "segundos": r["latencia_total_s"]},
                                    level="ERROR" if error else "DEFAULT",
                                    status_message=r["status"] if error else None)
        finally:
            LF.flush()                                     # enviar antes de devolver
        r.update(traza_id=traza_id, prompt_version=self.prompt_version, guardrail=guard)
        return r


class AgenteSEPSObsV2(AgenteSEPSObs):
    """La misma clase con el prompt candidato (Parte 2.c): otra etiqueta y otra sesión."""
    ETIQUETA = "candidata"
    SESION_ID = "golden-v2"


if __name__ == "__main__":
    import sys
    r = AgenteSEPSObs().run(" ".join(sys.argv[1:]) or "¿Cuántas cooperativas hay en la base?")
    print(f"traza_id: {r['traza_id']} · prompt: {r['prompt_version']} · guardrail: {r['guardrail']}")
    print(f"status: {r['status']} · pasos: {len(r['trace'])} · tokens: {r['usage']} · "
          f"{r['latencia_total_s']} s")
    print(f"respuesta:\n{r['answer']}")