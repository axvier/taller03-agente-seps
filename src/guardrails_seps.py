"""Taller 04 — Parte 3: los tres guardrails del agente SEPS.

Contrato, el de `guardrails.py` del laboratorio (lo usa probar_guardrails.py):
    validar_entrada(texto) -> (ok, texto_resultante)     ok=False → bloquear
    validar_salida(texto)  -> (ok, texto_resultante)     texto distinto → redactar

Los tres guardrails:
    G1 · inyección de instrucciones en la ENTRADA, por intención y sobre texto normalizado
         (minúsculas, sin tildes): «actúa» y «actua» son la misma intención (A02/A03).
    G2 · datos personales en la ENTRADA, la SALIDA y la TRAZA: correo, cédula y teléfono
         ecuatorianos, sin confundir fechas (2026-08-31), RUC de cooperativas (13 dígitos),
         códigos de cuenta (130210) ni montos (1.444.769.050,54). La traza se protege con la
         misma función, usada como máscara de Langfuse (`enmascarar`).
    G3 · claves en la SALIDA por su FORMA (sk-…, pk-lf-…, sk-lf-…, Bearer …, api_key=…), no por
         su longitud: un hash de 32 caracteres no es una clave (S03).
Lo que NO detectan (dicho, no escondido): nombres de personas (haría falta un modelo de
entidades como Presidio), el RUC de una persona natural (cédula + 001) y ataques escritos en
otro idioma que no sea español o inglés.
"""
from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------------- utilidades
def normalizar(texto: str) -> str:
    """minúsculas, sin tildes ni diéresis, espacios colapsados."""
    t = unicodedata.normalize("NFKD", texto or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().lower()


# ---------------------------------------------------------------------------------- G1 inyección
# Cada patrón es una INTENCIÓN, no una frase: verbo + objeto, en cualquier orden razonable.
_OBJ_REGLAS = r"(instrucciones|reglas|indicaciones|restricciones|prompt|directrices)"
INTENCIONES = {
    "ignorar_reglas": rf"\b(ignora\w*|ignore|olvida\w*|forget|omite|salta\w*|desobedece)\b.{{0,40}}\b{_OBJ_REGLAS}\b"
                      r"|\bignore (all )?(previous|prior|above)\b",
    "sin_restricciones": r"\b(actua|comportate|responde|eres|seras|act)\b.{0,30}\b(sin|without|no) (tuvieras |tienes |any )?"
                         r"(restricciones|reglas|limites|filtros|restrictions|rules)\b"
                         r"|\byou are now\b|\bdesde ahora eres\b|\bmodo (desarrollador|dios|developer)\b",
    "extraer_prompt": r"\b(revela\w*|muestra\w*|ensena\w*|dime|imprime|print|traduce\w*|repite|copia|reveal|show|translate)\b"
                      r".{0,40}\b(system prompt|prompt del sistema|tu prompt|tus (reglas|instrucciones)( internas)?|"
                      r"reglas internas|instrucciones internas|your (rules|instructions|prompt))\b",
    "extraer_credenciales": r"\b(dame|revela\w*|muestra\w*|dime|imprime|give|show|print)\b.{0,30}"
                            r"\b(clave|api key|apikey|contrasena|password|token|credencial\w*)\b",
    # Órdenes de escritura: imperativo («actualiza»), no reflexivo («se actualiza»), o SQL de escritura.
    "orden_de_escritura": r"(?<!\bse )\b(borra|elimina|actualiza|modifica|cambia|pon|inserta|trunca)\b.{0,40}"
                          r"\b(tabla|saldo|saldos|registro|registros|dato|datos|cuenta|base)\b"
                          r"|\b(update|delete|drop|insert|alter|truncate)\b\s+(\w+\s+)?(table|from|into|set|\w+\s+set)\b",
}
_INTENCIONES_RE = {k: re.compile(v) for k, v in INTENCIONES.items()}


def detectar_inyeccion(texto: str) -> list[str]:
    t = normalizar(texto)
    return [k for k, rx in _INTENCIONES_RE.items() if rx.search(t)]


# ---------------------------------------------------------------------------------- G2 datos personales
CORREO = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
# Celular ecuatoriano: 09 + 8 dígitos (o +593 9 …), con espacios o guiones opcionales.
CELULAR = re.compile(r"(?<![\w-])(?:\+?593[\s-]?|0)9\d(?:[\s-]?\d){7}(?![\w-])")
# Fijo: 0[2-7] + 7 dígitos, con separadores opcionales. Exige el 0 inicial: «101 102 103» no es.
FIJO = re.compile(r"(?<![\w-])0[2-7][\s-]?\d{3}[\s-]?\d{4}(?![\w-])")
# Cédula: 10 dígitos SUELTOS (ni parte de un RUC de 13, ni de un monto con decimales), provincia
# 01–24 o 30 y tercer dígito 0–5 (personas naturales). No se exige el dígito verificador: una
# cédula mal escrita sigue siendo un dato personal.
CEDULA = re.compile(r"(?<![\w.,-])(?:0[1-9]|1\d|2[0-4]|30)[0-5]\d{7}(?![\w-]|[.,]\d)")

ETIQUETAS = (("CORREO", CORREO), ("TELEFONO", CELULAR), ("TELEFONO", FIJO), ("CEDULA", CEDULA))


def redactar(texto: str) -> str:
    for etiqueta, rx in ETIQUETAS:
        texto = rx.sub(f"[{etiqueta}_REDACTADO]", texto)
    return texto


def enmascarar(*, data, **_):
    """Máscara de Langfuse: corre ANTES de enviar cada observation. Recorre dict, list y TUPLAS
    (@observe guarda los argumentos como {"args": (…), "kwargs": {…}})."""
    if isinstance(data, str):
        return redactar(data)
    if isinstance(data, dict):
        return {k: enmascarar(data=v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [enmascarar(data=v) for v in data]
    return data


# ---------------------------------------------------------------------------------- G3 claves
CLAVE = re.compile(
    r"\bsk-(proj-|ant-|lf-)?[A-Za-z0-9_\-]{16,}"          # OpenAI, Anthropic, Langfuse secreta
    r"|\bpk-lf-[A-Za-z0-9_\-]{8,}"                         # Langfuse pública
    r"|\bBearer\s+[A-Za-z0-9._\-]{20,}"
    r"|\b(api[_-]?key|secret[_-]?key|password|contrasena|token)\s*[=:]\s*\S{8,}",
    re.IGNORECASE)


def detectar_clave(texto: str) -> bool:
    return CLAVE.search(texto or "") is not None


# ---------------------------------------------------------------------------------- el contrato
MENSAJE_BLOQUEO = "Solicitud rechazada por el guardrail de entrada"


def validar_entrada(texto: str) -> tuple[bool, str]:
    """G1 bloquea; si pasa, G2 redacta los datos personales."""
    motivos = detectar_inyeccion(texto)
    if motivos:
        return False, f"{MENSAJE_BLOQUEO} ({', '.join(motivos)})."
    return True, redactar(texto)


def validar_salida(texto: str) -> tuple[bool, str]:
    """G3 bloquea una clave; si no hay, G2 redacta los datos personales."""
    if detectar_clave(texto):
        return False, "Salida bloqueada: contenía algo con forma de credencial."
    return True, redactar(texto)
