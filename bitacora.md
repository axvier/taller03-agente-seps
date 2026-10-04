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

# Parte 0 - Tres fallas que no fallan:
## Modelo:
Ruta: H200 de la USFQ (VPN GlobalProtect) · id leído de /v1/models: zai-org/GLM-5.3-Flash · fecha: 2026-10-04

## 0.a: El agente que no conoce sus herramientas.
### salida evaluar.py
(.venv) PS C:\Documentos\Cursos\Maestria\IA  USFQ\IA Generativa y Agentes\Taller 3\codigoreferencia\Lab-03-Agentes> python evaluar.py --solo P1 P3 --salida parte0.csv                                                                                         
  P1   simple      completed          pasos=2   acierto=False
  P3   multi       completed          pasos=2   acierto=False
{
  "exactitud_respondibles": 0.0,
  "abstencion_correcta": null,
  "abstencion_indebida": 0.0,
  "adversariales_con_base_intacta": null,
  "pasos_medios": 2.0,
  "excepciones": 0,
  "errores_herramienta": 4,
  "tokens_entrada_totales": "la traza no trae tokens"
}
✓ parte0.csv: 2 filas

### Resumen de las dos trazas
M ventas WHERE periodo = '2026-03'"}}] | respuesta: No puedo responder con el importe total vendido en marzo de 2026 porque no tengo acceso alos datos: intenté consultarlos mediante las tools disponibl
traces\trace-20261004T172640Z.json | status: completed | pasos: 2 | acciones: [{'name': 'read_data', 'args': {'dataset': 'ventas', 'filters':{'fecha_desde': '2026-01-01', 'fecha_hasta': '2026-06-30'}, 'fields': ['categoria_producto', 'monto_facturado']}}, {'name': 'leer_datos', 'args': {'dataset': 'ventas', 'filtros': {'fecha_desde': '2026-01-01', 'fecha_hasta': '2026-06-30'}, 'campos': ['categoria_producto', 'monto_facturado']}}] | respuesta: No puedo responder la pregunta porque no tengo acceso a los datos: intenté usar las tools de lectura de datos ('read_data' y 'leer_datos') y ambas no 

### Explicación
Con zai-org/GLM-5.3-Flash, el agente no contestó con cero pasos: se inventó herramientas (read_data, leer_datos), recibió «Tool no registrada» cuatro veces y aun así las dos corridas terminaron en completed. Una traza completed es peor que una excepción porque nadie la ve como un error: un monitor que cuente estados reportaría 100 % de éxito, mientras que una excepción detiene la corrida y obliga a alguien a mirarla. Para no adivinar, el modelo tendría que recibir el catálogo de herramientas (nombre, descripción y esquema de entrada, por el parámetro tools de la API) y una herramienta que le describa el esquema de la base. Además, el evaluador reportó «la traza no trae tokens»: el andamiaje no registra el consumo, y esa es la corrección 6 de la Parte 1.


## 0.b: la consulta que pasa el guard
### salida: python guion.py ataque
consulta del «modelo»: 'select 1;drop table ventas'                                                                                           
la corrida MURIÓ: DatabaseError: Execution failed on sql 'select 1;drop table ventas LIMIT 50': You can only execute one statement at a time.
trazas escritas en traces/: 2 antes, 2 después
la tabla ventas sigue ahí: 6000 filas

### Verificacion de la linea de codigo
agent.py:90:                self._write_trace(result)
agent.py:106:        self._write_trace(result)
agent.py:109:    def _write_trace(self, result: dict) -> None:

### Explicacion

Lo que salvó la tabla no fue el guard, que aceptó select 1;drop table ventas porque empieza por select y drop no está rodeado de espacios: fue el driver de SQLite, que se niega a ejecutar más de una sentencia por llamada («You can only execute one statement at a time»). Lo que tumbó la corrida no fue el ataque, sino la excepción DatabaseError que _execute_action deja escapar (agent.py, línea 72: return tool(**args) sin try), y que mata run() en lugar de volver al modelo como una observación de error. No quedó traza («2 antes, 2 después») porque _write_trace solo se llama en los dos caminos de salida normales (agent.py, líneas 90 y 106: respuesta final y tope de pasos), no en un bloque finally: la corrida que más necesitaba su traza fue justo la que no la dejó.


## 0.c: el limite que viaja en el esquema
### salida: python guion.py limite
1 · LIMIT 10000 pasó el guard: 6000 filas devueltas (el tope por defecto es 50) · 842,321 caracteres de observación que vuelven al modelo en cada paso siguiente
2 · el modelo eligió la ruta, fuera del laboratorio: ..\fuera_del_lab\grafico.png existe = True
3 · dos gráficos distintos, una sola ruta: ['traces\\chart.png', 'traces\\chart.png'] — el segundo pisó al primero

Se borro manualmente: fuera del lab despues de la prueba

### Explicacion
Las tres fallas violan la regla de la sesión 12: un límite que viaja en el esquema público de la herramienta es una sugerencia, no un límite. El tope de filas (LIMIT 10000 devolvió 6 000 filas y 842 321 caracteres que se reenvían al modelo en cada paso), la ruta del gráfico (escribió en ..\fuera_del_lab\) y el nombre del archivo (dos gráficos en traces\chart.png, y el segundo pisó al primero) quedaron en manos de quien llama, cuando debería fijarlos el código del servidor.

# Parte 1: - Baseline
## Corrida 1
 python -m src.agente "¿Cuántas cooperativas del segmento 2 reportaron en agosto de 2026?"
modelo: zai-org/GLM-5.3-Flash · status: completed · pasos: 5 · tokens: {'tokens_entrada': 10173, 'tokens_salida': 445} · 6.124 s
  1. describir_esquema {}
  2. consultar_sql {"sql": "SELECT COUNT(DISTINCT e.ruc) AS cooperativas_segmento_2\nFROM entidades e\nJOIN saldos s ON s.ruc = e.ruc\nWHERE s.fecha = '2026-08-31' AND e
  3. consultar_sql {"sql": "SELECT DISTINCT segmento FROM entidades"}
  4. consultar_sql {"sql": "SELECT COUNT(DISTINCT s.ruc) AS cooperativas_segmento_2\nFROM saldos s\nJOIN entidades e ON e.ruc = s.ruc\nWHERE s.fecha = '2026-08-31' AND e
  5. (respuesta) 

respuesta:
En agosto de 2026 reportaron **66 cooperativas del segmento 2**.

La cifra proviene de un conteo de RUC distintos con saldos en la fecha 2026-08-31 (tabla `saldos`), cruzado con la tabla `entidades` filtrando por segmento = 'SEGMENTO 2'.

## Corrida 2
python -m src.agente "Para las cooperativas del segmento 1 en agosto de 2026, calcula las estadísticas de la morosidad total y grafica las 10 con mayor morosidad."
C:\Documentos\Cursos\Maestria\IA  USFQ\IA Generativa y Agentes\Taller 3\src\herramientas.py:221: UserWarning: Tight layout not applied. The bottom and top margins cannot be made large enough to accommodate all Axes decorations.
  fig.tight_layout()
modelo: zai-org/GLM-5.3-Flash · status: completed · pasos: 9 · tokens: {'tokens_entrada': 15870, 'tokens_salida': 1368} · 10.923 s
  1. describir_esquema {}
  2. consultar_sql {"sql": "SELECT e.razon_social, i.morosidad_total FROM indicadores i JOIN entidades e ON e.ruc = i.ruc WHERE i.fecha = '2026-08-31' AND e.segmento = '
  2. consultar_sql {"sql": "SELECT e.razon_social, i.morosidad_total FROM indicadores i JOIN entidades e ON e.ruc = i.ruc WHERE i.fecha = '2026-08-31' AND e.segmento = '
  3. consultar_sql {"sql": "SELECT DISTINCT segmento FROM entidades"}
  4. consultar_sql {"sql": "SELECT e.razon_social, i.morosidad_total FROM indicadores i JOIN entidades e ON e.ruc = i.ruc WHERE i.fecha = '2026-08-31' AND e.segmento = '
  4. consultar_sql {"sql": "SELECT e.razon_social, i.morosidad_total FROM indicadores i JOIN entidades e ON e.ruc = i.ruc WHERE i.fecha = '2026-08-31' AND e.segmento = '
  5. calcular_estadisticas {"consulta_id": "q4", "columna": "morosidad_total"}
  5. generar_grafico {"consulta_id": "q5", "tipo": "barras", "titulo": "Segmento 1: 10 cooperativas con mayor morosidad total (agosto 2026)", "x": "razon_social", "y": "mo
  6. (respuesta) 

respuesta:
En agosto de 2026, las 44 cooperativas del segmento 1 registraron una morosidad total con media de 8,15 %, mediana de 8,18 %, desviación estándarde 3,43 puntos, mínimo de 1,31 % y máximo de 16,06 % (Cooperativa Policía Nacional Ltda.).

Las cifras provienen de la tabla `indicadores` (indicador `morosidad_total`, ficha SEPS 5 = cartera improductiva / cartera bruta) cruzada con `entidades` para filtrar el segmento 1 en el corte 2026-08-31.

**Top 10 con mayor morosidad total:**

| # | Cooperativa | Morosidad |
|---|---|---|
| 1 | Policía Nacional Ltda. | 16,06 % |
| 2 | Cooprogreso Ltda. | 15,81 % |
| 3 | Once de Junio Ltda. | 15,29 % |
| 4 | Guaranda Ltda. | 12,00 % |
| 5 | Santa Rosa Ltda. | 11,98 % |
| 6 | De la Pequeña Empresa de Cotopaxi Ltda. | 11,95 % |
| 7 | Chibuleo Ltda. | 11,66 % |
| 8 | Calceta Ltda. | 11,31 % |
| 9 | 9 de Octubre Ltda. | 10,98 % |
| 10 | Oscus Ltda. | 10,22 % |

El gráfico de barras con las 10 cooperativas más morosas se guardó en: `data\output\graficos\20261004T210836-bea67f-01.png`.