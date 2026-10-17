"""Taller 04 — corre un script del Lab 04 del profesor SIN copiarlo, desde la raíz del Taller 3.

    python lab04.py evaluar_llmops --golden taller04/golden_set.json --agente src.agente_t4:AgenteSEPSObs
    python lab04.py probar_guardrails --entrada src.guardrails_seps:validar_entrada ...
    python lab04.py exportar_trazas --sesion seps-base -o taller04/spans_base.jsonl
    python lab04.py resumir_trazas taller04/spans_base.jsonl --precio propietario_economico

Por qué: los scripts viven en codigoreferencia/Lab-04-LLMOps y Python solo busca módulos junto
al script; aquí se agrega la raíz del Taller 3 al path para que `src.agente_t4` se encuentre.
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAB04 = ROOT / "codigoreferencia" / "Lab-04-LLMOps"

if len(sys.argv) < 2:
    sys.exit(__doc__)
script = LAB04 / f"{sys.argv[1]}.py"
if not script.exists():
    sys.exit(f"No existe {script}")
sys.path[:0] = [str(LAB04), str(ROOT)]   # los módulos del lab y src/ del Taller 3
sys.argv = [str(script)] + sys.argv[2:]
runpy.run_path(str(script), run_name="__main__")