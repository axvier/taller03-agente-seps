# 1. Datos — Perfil del archivo 
## Salida perfilar_datos.py:
carpeta: C:\Documentos\Cursos\Maestria\IA  USFQ\IA Generativa y Agentes\Taller 3\data\input · 1 archivo(s)

======================================================================
archivo: archivo.txt · 277.5 MB
codificación: utf-8
filas: 1,967,603 · columnas: ['FECHA DE CORTE', 'SEGMENTO', 'RUC', 'RAZON SOCIAL', 'CUENTA', 'DESCRIPCION CUENTA', 'SALDO (USD)']

fechas de corte (filas por mes):
FECHA DE CORTE
2026-1-31    247588
2026-2-28    246397
2026-3-31    246397
2026-4-30    246397
2026-5-31    246397
2026-6-30    245206
2026-7-31    245206
2026-8-31    244015

segmentos (filas):
SEGMENTO
SEGMENTO 3               900396
SEGMENTO 2               616938
SEGMENTO 1               413277
SEGMENTO 1 MUTUALISTA     36992

entidades distintas: 208 · cuentas distintas: 1,214

longitud del código de cuenta (niveles del catálogo):
CUENTA
1      11571
2      66152
4     422976
6    1466904

saldos distintos de 0: 596,002 de 1,967,603
muestra cruda de saldos: ['216959,86', '92341917,31', '101884007,2', nan, '119340,39', '9691,51', '5003,61', '1658,3']
¿alguno con coma? True · ¿alguno negativo? True

cuentas de primer nivel (1 dígito) con su descripción:
CUENTA   DESCRIPCION CUENTA
     6 CUENTAS CONTINGENTES
     1               ACTIVO
     2              PASIVOS
     3           PATRIMONIO
     4               GASTOS
     5             INGRESOS
     7     CUENTAS DE ORDEN

# 2. # Datos — Construcción de la base
## Salida construir_base.py:
leídas 1,967,603 filas de 1 archivo(s)
entidades que cambiaron de segmento en el período: 4
cuentas con más de una descripción: 0
códigos padre que no existen en el catálogo: 0 []
filas duplicadas (fecha, ruc, cuenta): 0
entidades: 208 filas
cuentas: 1,214 filas
saldos: 1,967,603 filas
saldos NULL: 79,895
niveles del catálogo: [(1, 7), (2, 41), (3, 264), (4, 902)]

control de jerarquía al 2026-08-31 (todas las entidades):
  cuenta 1 (ACTIVO):                     31,907,399,132.18
  suma de sus hijas de nivel 2:          31,907,399,132.18
  suma ingenua de todo lo que empieza por 1: 126,336,207,107.12  ← cuenta el activo varias veces

base escrita en C:\Documentos\Cursos\Maestria\IA  USFQ\IA Generativa y Agentes\Taller 3\data\output\seps.sqlite · 275.5 MB

## Salida versión 2 con agregacion de indicadores al 31 de diciembre de 2025 construir.py:
  2025_Trimestres.txt: 474,418 filas · fechas: ['2025-12-31', '2025-3-31', '2025-6-30', '2025-9-30']               
  archivo.txt: 1,967,603 filas · fechas: ['2026-1-31', '2026-2-28', '2026-3-31', '2026-4-30', '2026-5-31', '2026-6-30', '2026-7-31', '2026-8-31']
leídas 2,442,021 filas de 2 archivo(s)
filtro fecha >= 2025-12-31: se descartan 358,995 filas · quedan los cortes ['2025-12-31', '2026-01-31', '2026-02-28', '2026-03-31', '2026-04-30', '2026-05-31', '2026-06-30', '2026-07-31', '2026-08-31']
entidades que cambiaron de segmento en el período: 4
cuentas con más de una descripción: 0
códigos padre que no existen en el catálogo: 0 []
filas duplicadas (fecha, ruc, cuenta): 0
entidades: 381 filas
cuentas: 1,214 filas
saldos: 2,083,026 filas
saldos NULL: 84,883
niveles del catálogo: [(1, 7), (2, 41), (3, 264), (4, 902)]

control de jerarquía al 2026-08-31 (todas las entidades):
  cuenta 1 (ACTIVO):                     31,907,399,132.18
  suma de sus hijas de nivel 2:          31,907,399,132.18
  suma ingenua de todo lo que empieza por 1: 126,336,207,107.12  ← cuenta el activo varias veces

cuentas de las fichas que no están en el catálogo: 0 []
indicadores: 2,034 filas (entidad × mes) · filas sin ROA por falta del diciembre previo: 0

control contra el boletín de la SEPS, al 2026-08-31 (agregado por segmento):
  segmento                 entidades  morosidad %  cobertura %
  SEGMENTO 1                      44         8.29       107.37
  SEGMENTO 1 MUTUALISTA            4         6.49        96.13
  SEGMENTO 2                      66         6.87       102.26
  SEGMENTO 3                      91         7.98        93.89

base escrita en C:\Documentos\Cursos\Maestria\IA  USFQ\IA Generativa y Agentes\Taller 3\data\output\seps.sqlite · 292.8 MB


## Salida version 3:

(.venv) PS C:\Documentos\Cursos\Maestria\IA  USFQ\IA Generativa y Agentes\Taller 3> python src/construir_base.py
  2025_Trimestres.txt: 474,418 filas · fechas: ['2025-12-31', '2025-3-31', '2025-6-30', '2025-9-30']
  archivo.txt: 1,967,603 filas · fechas: ['2026-1-31', '2026-2-28', '2026-3-31', '2026-4-30', '2026-5-31', '2026-6-30', '2026-7-31', '2026-8-31']
leídas 2,442,021 filas de 2 archivo(s)
filtro fecha >= 2025-12-31: se descartan 358,995 filas · quedan los cortes ['2025-12-31', '2026-01-31', '2026-02-28', '2026-03-31', '2026-04-30', '2026-05-31', '2026-06-30', '2026-07-31', '2026-08-31']
entidades que solo aparecen en 2025-12-31: 173 (por segmento: {'SEGMENTO 4': 128, 'SEGMENTO 5': 45}) → se descartan
entidades que cambiaron de segmento en el período: 4
cuentas con más de una descripción: 0
códigos padre que no existen en el catálogo: 0 []
filas duplicadas (fecha, ruc, cuenta): 0
entidades: 208 filas
cuentas: 1,214 filas
saldos: 2,030,607 filas
saldos NULL: 82,461
niveles del catálogo: [(1, 7), (2, 41), (3, 264), (4, 902)]

control de jerarquía al 2026-08-31 (todas las entidades):
  cuenta 1 (ACTIVO):                     31,907,399,132.18
  suma de sus hijas de nivel 2:          31,907,399,132.18
  suma ingenua de todo lo que empieza por 1: 126,336,207,107.12  ← cuenta el activo varias veces

cuentas de las fichas que no están en el catálogo: 0 []
indicadores: 1,861 filas (entidad × mes) · filas sin ROA por falta del diciembre previo: 0

control contra el boletín de la SEPS, al 2026-08-31 (agregado por segmento):
  segmento                 entidades  morosidad %  cobertura %
  SEGMENTO 1                      44         8.29       107.37
  SEGMENTO 1 MUTUALISTA            4         6.49        96.13
  SEGMENTO 2                      66         6.87       102.26
  SEGMENTO 3                      91         7.98        93.89

- El archivo 2025_Trimestres.txt consolida los segmentos 1 a 5; archivo.txt (2026) solo trae los segmentos 1 a 3. Se descartan 173 entidades (128 del segmento 4 y 45 del 5) que solo aparecen en el corte 2025-12-31.
- Al 2026-08-31 reportan 205 de las 208 entidades.

