"""Taller 04 · Fase 0: comprueba que el Langfuse local recibe trazas (no llama al modelo)."""
from dotenv import load_dotenv
load_dotenv()

from langfuse import get_client

lf = get_client()
print("Servidor:", __import__("os").getenv("LANGFUSE_BASE_URL"))
print("Credenciales válidas:", lf.auth_check())
with lf.start_as_current_observation(name="prueba-conexion", as_type="span",
                                     input="hola", output="ok"):
    print("traza_id:", lf.get_current_trace_id())
lf.flush()
print("Listo: busca 'prueba-conexion' en Tracing (rango Past 1 day).")