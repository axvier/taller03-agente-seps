"""Taller 03 — Perfil rápido de los archivos de saldos de la SEPS, antes de diseñar la base.

Lee todos los .txt / .csv de data/input (o el archivo que pases como argumento).
Solo lee y resume: no modifica nada.

Uso:  python perfilar_datos.py                      (todos los archivos de data/input)
      python perfilar_datos.py archivo.txt          (uno solo)
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "data" / "input"


def leer(ruta: Path) -> pd.DataFrame:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(ruta, sep="\t", dtype=str, encoding=enc, quotechar='"')
            print(f"codificación: {enc}")
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No pude leer {ruta.name} con utf-8 ni latin-1")


def perfilar(ruta: Path) -> None:
    print(f"\n{'=' * 70}\narchivo: {ruta.name} · {ruta.stat().st_size / 1e6:.1f} MB")
    df = leer(ruta)
    print(f"filas: {len(df):,} · columnas: {list(df.columns)}")
    fecha, seg, ruc, cuenta, desc, saldo = (df.columns[i] for i in (0, 1, 2, 4, 5, 6))

    print("\nfechas de corte (filas por mes):")
    print(df[fecha].value_counts().sort_index().to_string())
    print("\nsegmentos (filas):")
    print(df[seg].value_counts().to_string())
    print(f"\nentidades distintas: {df[ruc].nunique():,} · cuentas distintas: {df[cuenta].nunique():,}")
    print("\nlongitud del código de cuenta (niveles del catálogo):")
    print(df[cuenta].str.len().value_counts().sort_index().to_string())

    no_cero = df[df[saldo].str.strip() != "0"][saldo]
    print(f"\nsaldos distintos de 0: {len(no_cero):,} de {len(df):,}")
    if len(no_cero):
        print("muestra cruda de saldos:", no_cero.sample(min(8, len(no_cero)), random_state=1).tolist())
        print("¿alguno con coma?", no_cero.str.contains(",").any(),
              "· ¿alguno negativo?", no_cero.str.startswith("-").any())
    print("\ncuentas de primer nivel (1 dígito) con su descripción:")
    print(df[df[cuenta].str.len() == 1][[cuenta, desc]].drop_duplicates().to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        archivos = [Path(sys.argv[1])]
    else:
        archivos = sorted(p for p in RAW_PATH.glob("*") if p.suffix.lower() in {".txt", ".csv"})
        print(f"carpeta: {RAW_PATH} · {len(archivos)} archivo(s)")
        if not archivos:
            sys.exit(f"No hay .txt ni .csv en {RAW_PATH}. ¿Desde qué carpeta lo ejecutas?")
    for a in archivos:
        perfilar(a)