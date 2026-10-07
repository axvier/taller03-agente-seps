# Taller 03 — Agente analítico SEPS

MMIA 6013 IA Generativa y Agentes · USFQ

Agente analítico con herramientas sobre los saldos contables mensuales de las cooperativas de
ahorro y crédito supervisadas por la SEPS (segmentos 1 a 3 y mutualistas, enero–agosto de 2026).
El informe en PDF documenta cada parte; aquí está cómo reproducirla.

## Entorno
- Python 3.12 · dependencias con versiones fijadas en `requirements.txt` (las del laboratorio, con `langgraph==1.2.12`).
- Ruta del modelo: H200 de la USFQ con VPN GlobalProtect. El id del modelo no está en el código: se lee de `/v1/models`.
- `.env` (excluido por `.gitignore`):
  ```
  OPENAI_BASE_URL=http://172.28.230.10:12555/v1
  OPENAI_API_KEY=local
  AGENT_DB_PATH=data/output/seps.sqlite
  AGENT_TRACE_DIR=traces
  ```

## Datos (Opción B)
Los archivos de datos abiertos de la SEPS no se versionan por su tamaño (~280 MB). Descárgalos del portal
de estadísticas de la SEPS y guárdalos en `data/input/`:
- `archivo.txt`: saldos mensuales de 2026 (enero–agosto).
- `2025_Trimestres.txt`: cortes trimestrales de 2025 (solo se usa 2025-12-31, insumo de los promedios).

```powershell
python perfilar_datos.py           # perfil del archivo crudo
python src/construir_base.py       # crea data/output/seps.sqlite (saldos + 8 indicadores de la SEPS)
```

## Estructura
| Ruta | Qué es |
|---|---|
| `src/construir_base.py`, `src/indicadores.py` | Construcción de la base y los 8 indicadores (fichas metodológicas de la SEPS, sintaxis D10) |
| `src/herramientas.py` | Catálogo de 4 herramientas y correcciones C1–C5 |
| `src/agente.py` | `AgenteSEPS`: el baseline, con C6 y los frenos F1–F3 |
| `src/agente_grafo.py` | `AgenteSEPSGrafo`: la extensión D en LangGraph, con aprobación |
| `golden_set.json` | 13 preguntas; la verdad de cada respondible es una consulta SQL |
| `evaluar.py` | Copia sin modificar del laboratorio |
| `resultados_*.csv` | CSV crudos de `evaluar.py` (agente, andamiaje y grafo) |
| `traces/` | Trazas: `parte1/`, `agente/`, `andamiaje/`, `frenos/` y `grafo/` |
| `codigoreferencia/Lab-03-Agentes/` | Andamiaje del laboratorio, para la Parte 0 y la comparación de la 2.b |

## Cómo reproducir cada parte
```powershell
# Parte 0 (desde codigoreferencia/Lab-03-Agentes, con su propio .env)
python crear_base.py
python evaluar.py --solo P1 P3 --salida parte0.csv
python guion.py ataque
python guion.py limite

# Parte 1
python -m src.agente "¿Cuántas cooperativas del segmento 2 reportaron en agosto de 2026?"

# Parte 2
python verificar_golden.py
$env:AGENT_TRACE_DIR="traces/agente"
python evaluar.py --golden golden_set.json --agente src.agente:AgenteSEPS --db data/output/seps.sqlite --salida resultados_agente.csv
#   andamiaje: sobre una copia de la base en comparacion_andamiaje/data/database.sqlite (ver informe, Parte 2.b)
python comparar_resultados.py resultados_agente.csv resultados_andamiaje.csv
python ver_traza.py M6 S2 S3

# Parte 3 (sin modelo: cliente de guion)
python probar_frenos.py

# Parte 4
python -m src.agente_grafo --diagrama
$env:AGENT_TRACE_DIR="traces/grafo"
python evaluar.py --golden golden_set.json --agente src.agente_grafo:AgenteSEPSGrafo --db data/output/seps.sqlite --salida resultados_grafo.csv

# Parte 5
python verificar_pregunta2.py
```