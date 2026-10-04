"""Taller 03 — Herramientas del agente SEPS, con las correcciones de la Parte 1 señaladas.

    [C1] catálogo con contrato: nombre, descripción y esquema de entrada para cada herramienta,
         más `describir_esquema`, que le cuenta al modelo tablas, columnas e indicadores.
    [C2] solo lectura garantizada por el motor: mode=ro + autorizador de SQLite + una sentencia.
    [C3] los límites viven en el servidor: tope de filas, tamaño de la observación y ruta de
         los gráficos los fija este código; no son parámetros de la herramienta.
    [C4] fuente compartida: cada consulta se guarda con un id (q1, q2…) y su CSV; las
         estadísticas y el gráfico reciben ese id, no los datos.
    [C5] un error es una observación: `ejecutar` valida contra el esquema y nunca lanza.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("AGENT_DB_PATH", ROOT / "data" / "output" / "seps.sqlite"))
SALIDA = ROOT / "data" / "output"

MAX_FILAS_CONSULTA = 5_000      # [C3] lo que se guarda de una consulta
MAX_FILAS_OBSERVACION = 20      # [C3] lo que vuelve al modelo
MAX_CARACTERES_OBSERVACION = 6_000

# ---------------------------------------------------------------------------------- [C1]
CATALOGO = [
    {"type": "function", "function": {
        "name": "describir_esquema",
        "description": ("Devuelve las tablas y columnas de la base, el rango de fechas, las reglas del "
                        "catálogo de cuentas y la fórmula de cada indicador financiero de la SEPS. "
                        "Úsala antes de escribir SQL si no conoces los nombres exactos."),
        "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False}}},
    {"type": "function", "function": {
        "name": "consultar_sql",
        "description": ("Ejecuta UNA consulta SQL de solo lectura (SELECT o WITH … SELECT) sobre la base "
                        "SQLite de saldos de cooperativas. Devuelve un consulta_id, las columnas, el total "
                        f"de filas y las primeras {MAX_FILAS_OBSERVACION}. El servidor guarda hasta "
                        f"{MAX_FILAS_CONSULTA} filas para usarlas con calcular_estadisticas y generar_grafico."),
        "parameters": {"type": "object",
                       "properties": {"sql": {"type": "string", "description": "Una sola sentencia SELECT."}},
                       "required": ["sql"], "additionalProperties": False}}},
    {"type": "function", "function": {
        "name": "calcular_estadisticas",
        "description": ("Estadísticas descriptivas (n, media, mediana, desviación estándar, mínimo, máximo) "
                        "de una columna numérica de una consulta ya ejecutada."),
        "parameters": {"type": "object",
                       "properties": {"consulta_id": {"type": "string", "description": "Ej.: q1"},
                                      "columna": {"type": "string"}},
                       "required": ["consulta_id", "columna"], "additionalProperties": False}}},
    {"type": "function", "function": {
        "name": "generar_grafico",
        "description": ("Genera un gráfico PNG de barras o de líneas con dos columnas de una consulta ya "
                        "ejecutada. El servidor decide dónde se guarda y devuelve la ruta."),
        "parameters": {"type": "object",
                       "properties": {"consulta_id": {"type": "string"},
                                      "x": {"type": "string", "description": "Columna del eje X"},
                                      "y": {"type": "string", "description": "Columna numérica del eje Y"},
                                      "tipo": {"type": "string", "enum": ["barras", "lineas"]},
                                      "titulo": {"type": "string"}},
                       "required": ["consulta_id", "x", "y", "tipo", "titulo"], "additionalProperties": False}}},
]
ESQUEMAS = {h["function"]["name"]: h["function"]["parameters"] for h in CATALOGO}


def validar(nombre: str, args) -> str | None:
    """[C5] Valida los argumentos contra el esquema antes de ejecutar. Devuelve el error o None."""
    if nombre not in ESQUEMAS:
        return f"herramienta no registrada: {nombre}. Disponibles: {sorted(ESQUEMAS)}"
    if not isinstance(args, dict):
        return "los argumentos deben ser un objeto JSON"
    esquema = ESQUEMAS[nombre]
    faltan = [k for k in esquema["required"] if k not in args]
    sobran = [k for k in args if k not in esquema["properties"]]
    if faltan or sobran:
        return f"argumentos inválidos: faltan {faltan}, sobran {sobran}"
    for k, v in args.items():
        prop = esquema["properties"][k]
        if prop["type"] == "string" and not isinstance(v, str):
            return f"«{k}» debe ser texto"
        if "enum" in prop and v not in prop["enum"]:
            return f"«{k}» debe ser uno de {prop['enum']}"
    return None


# ---------------------------------------------------------------------------------- [C2]
_PERMITIDO = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}


def _autorizador(accion, *_):
    return sqlite3.SQLITE_OK if accion in _PERMITIDO else sqlite3.SQLITE_DENY


def _conexion() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH.resolve()}?mode=ro", uri=True)   # el motor no deja escribir
    conn.set_authorizer(_autorizador)                                        # ni PRAGMA, ni ATTACH, ni DDL
    return conn


def _una_sentencia(sql: str) -> str | None:
    limpio = sql.strip().rstrip(";").strip()
    if not limpio:
        return "la consulta está vacía"
    if ";" in limpio or not sqlite3.complete_statement(limpio + ";"):
        return "solo se acepta UNA sentencia SQL"
    if limpio.split(None, 1)[0].upper() not in {"SELECT", "WITH"}:
        return "solo se aceptan consultas SELECT o WITH … SELECT"
    return None


def _acotar(obj: dict) -> dict:
    """[C3] Ninguna observación pasa de MAX_CARACTERES_OBSERVACION, decida lo que decida el modelo."""
    texto = json.dumps(obj, ensure_ascii=False, default=str)
    if len(texto) <= MAX_CARACTERES_OBSERVACION:
        return obj
    obj = dict(obj)
    obj["filas"] = obj.get("filas", [])[:5]
    obj["nota"] = f"observación recortada por el servidor a {MAX_CARACTERES_OBSERVACION} caracteres"
    return obj


# ---------------------------------------------------------------------------------- [C4]
class Sesion:
    """Estado de una corrida: las consultas ejecutadas y los gráficos generados."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.consultas: dict[str, pd.DataFrame] = {}
        self.dir_consultas = SALIDA / "consultas"
        self.dir_graficos = SALIDA / "graficos"

    # -- herramientas ------------------------------------------------------------------------
    def describir_esquema(self) -> dict:
        with _conexion() as conn:
            conn.set_authorizer(None)        # solo para leer el catálogo de sqlite_master
            tablas = {}
            for (t,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
                tablas[t] = [f"{c[1]} {c[2]}" for c in conn.execute(f'PRAGMA table_info("{t}")')]
            fechas = [r[0] for r in conn.execute("SELECT DISTINCT fecha FROM saldos ORDER BY fecha")]
            indicadores = [dict(zip(("indicador", "ficha_seps", "formula", "interpretacion"), r))
                           for r in conn.execute("SELECT * FROM indicadores_catalogo")]
        return {
            "tablas": tablas,
            "fechas_de_corte": fechas,
            "reglas": [
                "saldos.saldo está en USD; fecha es el último día del mes (AAAA-MM-DD).",
                "El catálogo de cuentas es jerárquico: nivel 1 = 1 dígito (1 ACTIVO, 2 PASIVOS, 3 PATRIMONIO, "
                "4 GASTOS, 5 INGRESOS, 6 CONTINGENTES, 7 ORDEN), nivel 2 = 2 dígitos, nivel 3 = 4, nivel 4 = 6. "
                "NUNCA sumes cuentas de niveles distintos: el saldo de una cuenta ya incluye a sus hijas. "
                "Filtra por el código exacto (cuenta = '14'), no con LIKE '14%'.",
                "Las provisiones (cuenta 1499) se registran con signo negativo.",
                "La tabla indicadores ya trae los 8 indicadores calculados por entidad y mes, en PORCENTAJE "
                "(8.29 significa 8,29 %). Úsala en lugar de recalcularlos.",
                "Para agregados por segmento o del sistema, un indicador NO se promedia: se recalcula con "
                "sumas, por ejemplo 100*SUM(cartera_improductiva)/SUM(cartera_bruta).",
                "entidades.segmento es el del último mes reportado.",
                "El corte 2025-12-31 solo existe como insumo de los promedios; las preguntas del año usan 2026.",
            ],
            "indicadores": indicadores,
        }

    def consultar_sql(self, sql: str) -> dict:
        error = _una_sentencia(sql)
        if error:
            return {"error": error}
        try:
            with _conexion() as conn:
                cur = conn.execute(sql)
                columnas = [d[0] for d in cur.description]
                filas = cur.fetchmany(MAX_FILAS_CONSULTA + 1)          # [C3] tope del servidor
        except sqlite3.Error as e:
            return {"error": f"SQLite: {e}"}
        truncado = len(filas) > MAX_FILAS_CONSULTA
        filas = filas[:MAX_FILAS_CONSULTA]
        cid = f"q{len(self.consultas) + 1}"
        df = pd.DataFrame(filas, columns=columnas)
        self.consultas[cid] = df
        self.dir_consultas.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.dir_consultas / f"{self.run_id}-{cid}.csv", index=False)
        return _acotar({"consulta_id": cid, "columnas": columnas, "filas_total": len(df),
                        "truncado_en_servidor": truncado,
                        "filas": [list(f) for f in filas[:MAX_FILAS_OBSERVACION]]})

    def _columna(self, consulta_id: str, columna: str):
        if consulta_id not in self.consultas:
            return None, {"error": f"no existe la consulta {consulta_id}; disponibles: {sorted(self.consultas)}"}
        df = self.consultas[consulta_id]
        if columna not in df.columns:
            return None, {"error": f"la consulta {consulta_id} no tiene la columna «{columna}»; tiene {list(df.columns)}"}
        return df, None

    def calcular_estadisticas(self, consulta_id: str, columna: str) -> dict:
        df, error = self._columna(consulta_id, columna)
        if error:
            return error
        s = pd.to_numeric(df[columna], errors="coerce").dropna()
        if s.empty:
            return {"error": f"la columna «{columna}» no tiene valores numéricos"}
        return {"consulta_id": consulta_id, "columna": columna, "n": int(s.size),
                "media": round(float(s.mean()), 4), "mediana": round(float(s.median()), 4),
                "desviacion_estandar": round(float(s.std(ddof=1)), 4) if s.size > 1 else 0.0,
                "minimo": round(float(s.min()), 4), "maximo": round(float(s.max()), 4)}

    def generar_grafico(self, consulta_id: str, x: str, y: str, tipo: str, titulo: str) -> dict:
        df, error = self._columna(consulta_id, x)
        if error:
            return error
        if y not in df.columns:
            return {"error": f"la consulta {consulta_id} no tiene la columna «{y}»"}
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        datos = df[[x, y]].head(50)
        fig, ax = plt.subplots(figsize=(9, 4.5))
        (ax.bar if tipo == "barras" else ax.plot)(datos[x].astype(str), pd.to_numeric(datos[y], errors="coerce"))
        ax.set_title(titulo[:120]); ax.set_xlabel(x); ax.set_ylabel(y)
        ax.tick_params(axis="x", rotation=60, labelsize=7)
        fig.tight_layout()
        self.dir_graficos.mkdir(parents=True, exist_ok=True)
        n = len(list(self.dir_graficos.glob(f"{self.run_id}-*.png"))) + 1
        ruta = self.dir_graficos / f"{self.run_id}-{n:02d}.png"      # [C3] la ruta la fija el servidor
        fig.savefig(ruta, dpi=110); plt.close(fig)
        return {"grafico": str(ruta.relative_to(ROOT)), "puntos": len(datos)}

    # -- despacho ----------------------------------------------------------------------------
    def ejecutar(self, nombre: str, args) -> dict:
        """[C5] Valida y ejecuta. Cualquier excepción vuelve como {"error": …}: nunca mata la corrida."""
        error = validar(nombre, args)
        if error:
            return {"error": error}
        try:
            return getattr(self, nombre)(**args)
        except Exception as e:  # noqa: BLE001 — a propósito: el error es una observación
            return {"error": f"{type(e).__name__}: {e}"[:500]}