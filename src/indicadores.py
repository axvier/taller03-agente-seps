"""Taller 03 — Indicadores financieros de la SEPS, como SQL sobre la tabla `saldos`.

Fuente: «Fichas Metodológicas de Indicadores Financieros», SEPS, versión 3.0 (última
actualización 31-07-2026), apartado D10 «Sintaxis del indicador», metodología vigente
(desde mayo 2021; la cobertura, desde marzo 2025). La sintaxis original es SPSS; aquí se
traduce a SQL sin cambiar cuentas ni reglas.

Todos los indicadores se guardan en PORCENTAJE (5.23 = 5,23 %). Reglas de las fichas que se
respetan: provisiones (1499) en negativo; anualización ×12/mes; activo y patrimonio
promedio con el diciembre del año anterior, divididos para (mes + 1); denominador ≤ 0 → 0.
"""

IMPRODUCTIVA = {   # cartera que no devenga intereses + vencida, por línea (ficha 5)
    "productivo": ["1425", "1433", "1441", "1449", "1457", "1465"],
    "consumo":    ["1426", "1434", "1442", "1450", "1458", "1466"],
    "inmobiliario": ["1427", "1435", "1443", "1451", "1459", "1467"],
    "vivienda_ip": ["1432", "1440", "1448", "1456", "1464", "1472"],
    "microcredito": ["1428", "1436", "1444", "1452", "1460", "1468"],
    "educativo":  ["1479", "1481", "1483", "1485", "1487", "1489"],
}
BRUTA_CONSUMO = ["1402", "1410", "1418"] + IMPRODUCTIVA["consumo"]          # ficha 16
OTRAS = ["1", "3", "4", "5", "11", "14", "1499", "2101", "2102", "2103", "210305", "210310",
         "3603", "3604", "41", "42", "43", "44", "45", "46", "47", "48",
         "51", "52", "53", "54", "55", "56"]

CODIGOS = sorted(set(OTRAS + BRUTA_CONSUMO + [c for l in IMPRODUCTIVA.values() for c in l]))


def _c(codigo: str) -> str:
    return f"c_{codigo}"


def _suma(codigos) -> str:
    return "(" + " + ".join(_c(c) for c in codigos) + ")"


def _ratio(num: str, den: str) -> str:
    """Regla de las fichas: si el numerador o el denominador es ≤ 0, el indicador vale 0."""
    return f"CASE WHEN ({num}) <= 0 OR ({den}) <= 0 THEN 0 ELSE 100.0 * ({num}) / ({den}) END"


SQL_BASE = (
    "CREATE TABLE _base AS SELECT fecha, ruc, "
    + ", ".join(f"COALESCE(SUM(CASE WHEN cuenta = '{c}' THEN saldo END), 0) AS {_c(c)}" for c in CODIGOS)
    + " FROM saldos WHERE cuenta IN (" + ", ".join(f"'{c}'" for c in CODIGOS) + ") GROUP BY fecha, ruc;"
)

IMPR_TOTAL = _suma([c for l in IMPRODUCTIVA.values() for c in l])
BRUTA = "(c_14 - c_1499)"                       # 1499 es negativa: restarla la suma de vuelta
RES_ROE = "(c_51 + c_52 + c_53 + c_54 + c_55 + c_56 - c_41 - c_42 - c_43 - c_44 - c_45 - c_46 - c_47 - c_48)"

SQL_INDICADORES = f"""
CREATE TABLE indicadores AS
WITH b AS (
    SELECT *, CAST(substr(fecha, 1, 4) AS INTEGER) AS anio, CAST(substr(fecha, 6, 2) AS INTEGER) AS mes
    FROM _base
),
p AS (
    SELECT b.*,
        (SUM(b.c_1) OVER w + d.c_1) / (mes + 1.0) AS activo_promedio,       -- NULL si falta el diciembre previo
        (SUM(b.c_3) OVER w + d.c_3) / (mes + 1.0) AS patrimonio_promedio
    FROM b
    LEFT JOIN _base d ON d.ruc = b.ruc AND d.fecha = printf('%d-12-31', b.anio - 1)
    WINDOW w AS (PARTITION BY b.ruc, b.anio ORDER BY b.fecha ROWS UNBOUNDED PRECEDING)
)
SELECT
    fecha, ruc,
    c_1 AS activo, c_3 AS patrimonio, {BRUTA} AS cartera_bruta, {IMPR_TOTAL} AS cartera_improductiva, -c_1499 AS provisiones_cartera,
    (c_2101 + c_2103) AS depositos_vista_y_plazo,
    {_ratio(IMPR_TOTAL, BRUTA)} AS morosidad_total,
    {_ratio(_suma(IMPRODUCTIVA['consumo']), _suma(BRUTA_CONSUMO))} AS morosidad_consumo,
    {_ratio('-c_1499', IMPR_TOTAL)} AS cobertura_cartera_problematica,
    CASE WHEN activo_promedio IS NULL THEN NULL
         ELSE {_ratio('c_45 * 12.0 / mes', 'activo_promedio')} END AS eficiencia_operativa,
    CASE WHEN {BRUTA} > 0 AND (c_2101 > 0 OR c_2103 > 0)
         THEN 100.0 * {BRUTA} / (c_2101 + c_2103) END AS intermediacion_financiera,
    CASE WHEN mes = 12 THEN CASE WHEN c_1 > 0 THEN 100.0 * (c_3603 + c_3604) / c_1 END
         WHEN activo_promedio > 0 THEN 100.0 * ((c_5 - c_4) * 12.0 / mes) / activo_promedio
         WHEN activo_promedio IS NOT NULL THEN 0 END AS roa,
    CASE WHEN mes = 12 THEN CASE WHEN (c_3 - c_3603 - c_3604) > 0
                                 THEN 100.0 * (c_3603 + c_3604) / (c_3 - c_3603 - c_3604) END
         WHEN patrimonio_promedio > 0 THEN 100.0 * ({RES_ROE} * 12.0 / mes) / patrimonio_promedio
         WHEN patrimonio_promedio IS NOT NULL THEN 0 END AS roe,
    {_ratio('c_11', 'c_2101 + c_2102 + c_210305 + c_210310')} AS liquidez
FROM p;
CREATE INDEX ix_indicadores ON indicadores(fecha, ruc);
DROP TABLE _base;
"""

# Lo que la herramienta de esquema le contará al agente (corrección 1 de la Parte 1)
CATALOGO = [
    ("morosidad_total", 5, "Cartera improductiva / cartera bruta. Cartera improductiva = no devenga + vencida de todas las líneas; cartera bruta = cuenta 14 − cuenta 1499.", "más bajo es mejor"),
    ("morosidad_consumo", 16, "Cartera improductiva de consumo / cartera bruta de consumo.", "más bajo es mejor"),
    ("cobertura_cartera_problematica", 18, "Provisiones de cartera (−1499) / cartera improductiva.", "más alto es mejor"),
    ("eficiencia_operativa", 31, "Gastos de operación (45) anualizados ×12/mes / activo promedio (con el diciembre previo, ÷ (mes+1)).", "más bajo es mejor"),
    ("intermediacion_financiera", 36, "Cartera bruta / (depósitos a la vista 2101 + depósitos a plazo 2103).", "mide cuánto de lo captado se presta"),
    ("roa", 35, "Resultado (5 − 4) anualizado ×12/mes / activo promedio. En diciembre: (3603 + 3604) / activo.", "más alto es mejor"),
    ("roe", 34, "Resultado (51…56 − 41…48) anualizado ×12/mes / patrimonio promedio. En diciembre: (3603 + 3604) / (3 − 3603 − 3604).", "más alto es mejor"),
    ("liquidez", 52, "Fondos disponibles (11) / depósitos a corto plazo (2101 + 2102 + 210305 + 210310).", "más alto es más líquido"),
]

SQL_CATALOGO = """
CREATE TABLE indicadores_catalogo (indicador TEXT PRIMARY KEY, ficha_seps INTEGER, formula TEXT, interpretacion TEXT);
"""