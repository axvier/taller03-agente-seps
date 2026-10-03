"""Taller 03 — Construye la base SQLite del agente a partir del archivo de saldos de la SEPS.

Fuente: saldos contables mensuales de las cooperativas de ahorro y crédito (datos abiertos
de la SEPS), enero–agosto de 2026, en data/input/. El archivo crudo no se versiona (pesa
~280 MB): este script es lo que va al repositorio.

Diseño (3 tablas, esquema estrella mínimo):
    entidades(ruc PK, razon_social, segmento)
    cuentas(codigo PK, descripcion, nivel, codigo_padre)
    saldos(fecha, ruc, cuenta, saldo)  PK (fecha, ruc, cuenta)

Limpieza: fecha «2026-2-28» → «2026-02-28»; saldo «216959,86» → 216959.86; saldo vacío → NULL.

Uso:  python src/construir_base.py
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "input"
DB_PATH = ROOT / "data" / "output" / "seps.sqlite"
NIVEL = {1: 1, 2: 2, 4: 3, 6: 4}          # largo del código → nivel del catálogo
LARGO_PADRE = {2: 1, 4: 2, 6: 4}          # largo del código → largo del código padre

ESQUEMA = """
CREATE TABLE entidades (
    ruc          TEXT PRIMARY KEY,
    razon_social TEXT NOT NULL,
    segmento     TEXT NOT NULL
);
CREATE TABLE cuentas (
    codigo       TEXT PRIMARY KEY,
    descripcion  TEXT NOT NULL,
    nivel        INTEGER NOT NULL,
    codigo_padre TEXT REFERENCES cuentas(codigo)
);
CREATE TABLE saldos (
    fecha  TEXT NOT NULL,                                -- AAAA-MM-DD, último día del mes
    ruc    TEXT NOT NULL REFERENCES entidades(ruc),
    cuenta TEXT NOT NULL REFERENCES cuentas(codigo),
    saldo  REAL,                                         -- USD; NULL si venía vacío
    PRIMARY KEY (fecha, ruc, cuenta)
);
CREATE INDEX ix_saldos_cuenta_fecha ON saldos(cuenta, fecha);
CREATE INDEX ix_saldos_ruc ON saldos(ruc);
"""


def leer_crudo() -> pd.DataFrame:
    archivos = sorted(p for p in RAW_PATH.glob("*") if p.suffix.lower() in {".txt", ".csv"})
    if not archivos:
        sys.exit(f"No hay .txt ni .csv en {RAW_PATH}")
    partes = [pd.read_csv(a, sep="\t", dtype=str, encoding="utf-8", quotechar='"') for a in archivos]
    df = pd.concat(partes, ignore_index=True)
    df.columns = ["fecha", "segmento", "ruc", "razon_social", "cuenta", "descripcion", "saldo"]
    print(f"leídas {len(df):,} filas de {len(archivos)} archivo(s)")
    return df


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d").dt.strftime("%Y-%m-%d")
    s = df["saldo"].str.strip()
    if s.str.contains(r"\.", na=False).any():
        sys.exit("Hay saldos con punto: revisar el separador de miles antes de convertir.")
    df["saldo"] = pd.to_numeric(s.str.replace(",", ".", regex=False), errors="coerce")
    for c in ("segmento", "ruc", "razon_social", "cuenta", "descripcion"):
        df[c] = df[c].str.strip()
    return df


def tablas(df: pd.DataFrame):
    # entidades: si una cooperativa cambió de segmento o de nombre, queda el del último mes
    cambios = df.groupby("ruc")["segmento"].nunique()
    print(f"entidades que cambiaron de segmento en el período: {int((cambios > 1).sum())}")
    entidades = (df.sort_values("fecha").groupby("ruc")[["razon_social", "segmento"]].last().reset_index())

    # cuentas: la descripción más frecuente de cada código
    varias = df.groupby("cuenta")["descripcion"].nunique()
    print(f"cuentas con más de una descripción: {int((varias > 1).sum())}")
    cuentas = (df.groupby(["cuenta", "descripcion"]).size().reset_index(name="n")
                 .sort_values("n").groupby("cuenta").last().reset_index()[["cuenta", "descripcion"]]
                 .rename(columns={"cuenta": "codigo"}))
    largo = cuentas["codigo"].str.len()
    cuentas["nivel"] = largo.map(NIVEL)
    cuentas["codigo_padre"] = [c[:LARGO_PADRE[len(c)]] if len(c) in LARGO_PADRE else None for c in cuentas["codigo"]]
    huerfanas = set(cuentas["codigo_padre"].dropna()) - set(cuentas["codigo"])
    print(f"códigos padre que no existen en el catálogo: {len(huerfanas)} {sorted(huerfanas)[:10]}")

    dup = df.duplicated(["fecha", "ruc", "cuenta"]).sum()
    print(f"filas duplicadas (fecha, ruc, cuenta): {dup}")
    saldos = df.drop_duplicates(["fecha", "ruc", "cuenta"])[["fecha", "ruc", "cuenta", "saldo"]]
    return entidades, cuentas, saldos


def control_jerarquia(conn: sqlite3.Connection) -> None:
    """El catálogo es jerárquico: sumar niveles distintos cuenta dos veces el mismo dinero."""
    fecha = conn.execute("SELECT MAX(fecha) FROM saldos").fetchone()[0]
    total_1 = conn.execute("SELECT SUM(saldo) FROM saldos WHERE fecha=? AND cuenta='1'", (fecha,)).fetchone()[0]
    hijos = conn.execute("""SELECT SUM(s.saldo) FROM saldos s JOIN cuentas c ON c.codigo=s.cuenta
                            WHERE s.fecha=? AND c.codigo_padre='1'""", (fecha,)).fetchone()[0]
    todo = conn.execute("""SELECT SUM(s.saldo) FROM saldos s WHERE s.fecha=? AND s.cuenta LIKE '1%'""",
                        (fecha,)).fetchone()[0]
    print(f"\ncontrol de jerarquía al {fecha} (todas las entidades):")
    print(f"  cuenta 1 (ACTIVO):                     {total_1:,.2f}")
    print(f"  suma de sus hijas de nivel 2:          {hijos:,.2f}")
    print(f"  suma ingenua de todo lo que empieza por 1: {todo:,.2f}  ← cuenta el activo varias veces")


if __name__ == "__main__":
    df = limpiar(leer_crudo())
    entidades, cuentas, saldos = tablas(df)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.unlink(missing_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(ESQUEMA)
        entidades.to_sql("entidades", conn, if_exists="append", index=False)
        cuentas.to_sql("cuentas", conn, if_exists="append", index=False)
        saldos.to_sql("saldos", conn, if_exists="append", index=False, chunksize=50_000)
        for t in ("entidades", "cuentas", "saldos"):
            print(f"{t}: {conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:,} filas")
        print(f"saldos NULL: {conn.execute('SELECT COUNT(*) FROM saldos WHERE saldo IS NULL').fetchone()[0]:,}")
        print("niveles del catálogo:", conn.execute(
            "SELECT nivel, COUNT(*) FROM cuentas GROUP BY nivel ORDER BY nivel").fetchall())
        control_jerarquia(conn)
    print(f"\nbase escrita en {DB_PATH} · {DB_PATH.stat().st_size / 1e6:.1f} MB")