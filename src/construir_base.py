"""Taller 03 — Construye la base SQLite del agente a partir del archivo de saldos de la SEPS.

Fuente: saldos contables mensuales de las cooperativas de ahorro y crédito (datos abiertos
de la SEPS), enero–agosto de 2026, en data/input/. El archivo crudo no se versiona (pesa
~280 MB): este script es lo que va al repositorio.

Diseño (3 tablas, esquema estrella mínimo):
    entidades(ruc PK, razon_social, segmento)
    cuentas(codigo PK, descripcion, nivel, codigo_padre)
    saldos(fecha, ruc, cuenta, saldo)  PK (fecha, ruc, cuenta)

Limpieza: fecha «2026-2-28» → «2026-02-28»; saldo «216959,86» → 216959.86; saldo vacío → NULL.

Además crea la tabla `indicadores` (8 indicadores de las fichas metodológicas de la SEPS,
ver src/indicadores.py) y `indicadores_catalogo`, que describe cada fórmula.
Para los promedios de ROA, ROE y eficiencia hace falta el diciembre del año anterior:
data/input debe traer también el archivo de diciembre de 2025.

Uso:  python src/construir_base.py
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

import indicadores as ind

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "input"
DB_PATH = ROOT / "data" / "output" / "seps.sqlite"
# Del archivo 2025 (cortes trimestrales) solo se usa diciembre: es el mes previo que piden los
# promedios de ROA, ROE y eficiencia. Los trimestres anteriores romperían la ventana mensual.
FECHA_MINIMA = "2025-12-31"
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
    partes = []
    for a in archivos:
        p = pd.read_csv(a, sep="\t", dtype=str, encoding="utf-8", quotechar='"')
        print(f"  {a.name}: {len(p):,} filas · fechas: {sorted(p.iloc[:, 0].str.strip().unique())}")
        partes.append(p)
    df = pd.concat(partes, ignore_index=True)
    df.columns = ["fecha", "segmento", "ruc", "razon_social", "cuenta", "descripcion", "saldo"]
    print(f"leídas {len(df):,} filas de {len(archivos)} archivo(s)")
    return df


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    df["fecha"] = pd.to_datetime(df["fecha"].str.strip(), format="%Y-%m-%d").dt.strftime("%Y-%m-%d")
    antes = len(df)
    df = df[df["fecha"] >= FECHA_MINIMA].copy()
    print(f"filtro fecha >= {FECHA_MINIMA}: se descartan {antes - len(df):,} filas · "
          f"quedan los cortes {sorted(df['fecha'].unique())}")
    # El diciembre previo solo sirve para las entidades que reportan en 2026: las que aparecen
    # únicamente en diciembre inflarían la tabla entidades y no tienen ningún indicador del año.
    del_anio = df["fecha"] > FECHA_MINIMA
    rucs_anio = set(df.loc[del_anio, "ruc"].str.strip())
    solo_dic = df[~del_anio & ~df["ruc"].str.strip().isin(rucs_anio)]
    print(f"entidades que solo aparecen en {FECHA_MINIMA}: {solo_dic['ruc'].nunique()} "
          f"(por segmento: {solo_dic.drop_duplicates('ruc')['segmento'].value_counts().to_dict()}) → se descartan")
    df = df[del_anio | df["ruc"].str.strip().isin(rucs_anio)].copy()
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


def crear_indicadores(conn: sqlite3.Connection) -> None:
    existentes = {r[0] for r in conn.execute("SELECT codigo FROM cuentas")}
    faltan = [c for c in ind.CODIGOS if c not in existentes]
    print(f"\ncuentas de las fichas que no están en el catálogo: {len(faltan)} {faltan}")
    conn.executescript(ind.SQL_BASE + ind.SQL_INDICADORES + ind.SQL_CATALOGO)
    conn.executemany("INSERT INTO indicadores_catalogo VALUES (?, ?, ?, ?)", ind.CATALOGO)
    sin_prom = conn.execute("SELECT COUNT(*) FROM indicadores WHERE roa IS NULL").fetchone()[0]
    print(f"indicadores: {conn.execute('SELECT COUNT(*) FROM indicadores').fetchone()[0]:,} filas "
          f"(entidad × mes) · filas sin ROA por falta del diciembre previo: {sin_prom:,}")
    fecha = conn.execute("SELECT MAX(fecha) FROM indicadores").fetchone()[0]
    print(f"\ncontrol contra el boletín de la SEPS, al {fecha} (agregado por segmento):")
    print(f"  {'segmento':<24}{'entidades':>10}{'morosidad %':>13}{'cobertura %':>13}")
    for seg, n, mor, cob in conn.execute("""
            SELECT e.segmento, COUNT(*),
                   100.0 * SUM(i.cartera_improductiva) / SUM(i.cartera_bruta),
                   100.0 * SUM(i.provisiones_cartera) / SUM(i.cartera_improductiva)
            FROM indicadores i JOIN entidades e USING (ruc)
            WHERE i.fecha = ? GROUP BY e.segmento ORDER BY e.segmento""", (fecha,)):
        print(f"  {seg:<24}{n:>10}{mor:>13.2f}{cob:>13.2f}")


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
        crear_indicadores(conn)
    print(f"\nbase escrita en {DB_PATH} · {DB_PATH.stat().st_size / 1e6:.1f} MB")