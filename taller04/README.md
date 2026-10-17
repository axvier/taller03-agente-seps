# Taller 4 · LLMOps del agente analista SEPS (Opción A)

Rama `taller04` del repositorio del Taller 3. El agente del Taller 3 (`src/agente.py`) no se modifica:
`src/agente_t4.py` lo envuelve con Langfuse (spans corrida / llm / herramienta / guardrail, prompt
versionado, sesión y tags) y `src/guardrails_seps.py` agrega tres guardrails (inyección, datos
personales, claves).

## Requisitos
- `pip install -r requirements.txt` (incluye `langfuse==4.17.0`)
- Langfuse 4.50.0 en Docker (`levantar_langfuse.sh` del curso) y el laboratorio del curso en
  `codigoreferencia/` (Lab-03-Agentes y Lab-04-LLMOps; no se versiona)
- `.env` local (no versionado) con `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `AGENT_DB_PATH`,
  `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`, `JUEZ_BASE_URL`, `JUEZ_API_KEY`,
  `JUEZ_MODEL=gemma3:27b`, `PRECIO_FILA=local`
- Base `data/output/seps.sqlite` construida con `python src/construir_base.py` (Taller 3)

## Reproducir
```
python registrar_prompt.py v1
python armar_golden_t4.py
python lab04.py evaluar_llmops --golden taller04/golden_set.json --agente src.agente_t4:AgenteSEPSObs   --salida taller04/resultados_base.csv
python lab04.py exportar_trazas --sesion golden-base -o taller04/spans_base.jsonl
python lab04.py resumir_trazas taller04/spans_base.jsonl --precio propietario_economico
python preparar_etiquetado.py taller04/resultados_base.csv          # etiquetar a mano ANTES de ver al juez
python controles_juez.py generar && python controles_juez.py juzgar
python crear_prompt_v2.py
python registrar_prompt.py v2 --archivo taller04/prompt_v2.txt --mensaje "v2: esquema en el prompt y lectura declarada"
python lab04.py evaluar_llmops --golden taller04/golden_set.json --agente src.agente_t4:AgenteSEPSObsV2 --salida taller04/resultados_v2.csv
python comparar_t4.py taller04/resultados_base.csv taller04/resultados_v2.csv
python lab04.py probar_guardrails --entrada src.guardrails_seps:validar_entrada --salida src.guardrails_seps:validar_salida --casos taller04/ataques.json --csv taller04/guardrails.csv
python lab04.py probar_guardrails --casos taller04/ataques.json --csv taller04/guardrails_plantilla.csv
python demo_guardrails.py && python demo_fuga_salida.py
```

## Contenido de esta carpeta
| Archivo | Qué es |
|---|---|
| `golden_set.json` | 20 casos: 12 respondibles (2 con `pii`), 3 negativas, 3 adversariales, 2 ambiguas |
| `resultados_base.csv`, `resultados_v2.csv` | evaluación v1 (base) y v2 (prompt mejorado) con juez gemma3:27b |
| `etiquetas.csv`, `etiquetas_controles.csv`, `etiquetas_verificador.csv` | etiquetas humanas y del verificador para calibrar al juez |
| `controles.csv`, `controles_juez.csv` | casos de control con error conocido y su veredicto |
| `prompt_v2.txt` | la mejora versionada (Langfuse `seps-analista` v2, etiqueta `candidata`) |
| `ataques.json` | banco de guardrails: 17 de la plantilla + 4 del dominio SEPS |
| `guardrails.csv`, `guardrails_plantilla.csv` | resultados de los guardrails propios y de la plantilla |
| `spans_base.jsonl`, `spans_v2.jsonl` | spans exportados de Langfuse (sin datos personales) |

Ninguna clave está en el repositorio. Los datos personales de P1/P2 son ficticios y no aparecen en los spans.