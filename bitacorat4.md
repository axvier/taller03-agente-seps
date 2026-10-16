# Taller 4 · Preparación → Repositorio
En la mismo git del taller 3 creamos una rama para el taller 04

## Salidas Git
git checkout -b taller04
Switched to a new branch 'taller04'
git push -u origin taller04
Total 0 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
remote: 
remote: Create a pull request for 'taller04' on GitHub by visiting:
remote:      https://github.com/axvier/taller03-agente-seps/pull/new/taller04
remote: 
To https://github.com/axvier/taller03-agente-seps.git
 * [new branch]      taller04 -> taller04
branch 'taller04' set up to track 'origin/taller04'.

## Salidas dir codigoreferencia
nv) PS C:\Documentos\Cursos\Maestria\IA  USFQ\IA Generativa y Agentes\Taller 3> dir codigoreferencia


    Directorio: C:\Documentos\Cursos\Maestria\IA  USFQ\IA Generativa y Agentes\Taller 3\codigoreferencia


Mode                 LastWriteTime         Length Name                                                                                                        
----                 -------------         ------ ----                                                                                                        
d-----        16/10/2026     16:59                Lab-03-Agentes                                                                                              
d-----         4/10/2026     12:26                Lab-03-Agentes-T3                                                                                           
d-----        16/10/2026     16:59                Lab-04-LLMOps                                                                                               
d-----        16/10/2026     16:59                langfuse                                                                                                    
d-----        16/10/2026     16:59                papers                                                                                                      
d-----        16/10/2026     16:59                ragas-langfuse                                                                                              
-a----         3/10/2026      9:43          22382 taller-03-agentes.zip                                                                                       
-a----         9/10/2026     11:19           3583 taller-03-opcion-libre.md                                                                                   
-a----         3/10/2026      9:44        7180548 taller-03-v2-solver-multiagente.zip                                                                         

## Entorno
Langfuse Version: 4.17.0

## DockerLangfuse:
La comprobacion se hizo de manera visual y con codigo.
langfuse-mmia-langfuse-web-1  Up 43 minutes
langfuse-langfuse-worker-1  Up 43 minutes
langfuse-langfuse-web-1  Up Less than a second
langfuse-clickhouse-1  Up 43 minutes (healthy)
langfuse-minio-1  Up 43 minutes (healthy)
langfuse-mmia-minio-1  Up 43 minutes (healthy)
langfuse-mmia-langfuse-worker-1  Up 43 minutes
langfuse-mmia-postgres-1  Up 43 minutes (healthy)
langfuse-mmia-redis-1  Up 43 minutes (healthy)
langfuse-mmia-clickhouse-1  Up 43 minutes (healthy)
langfuse-redis-1  Up 43 minutes (healthy)
langfuse-postgres-1  Up 43 minutes (healthy)


## Salida Languse probar_langfuse.py                   
Servidor: http://localhost:3000
Credenciales válidas: True
traza_id: 5f5077417e8911fab8ea8c4673f4d181
Listo: busca 'prueba-conexion' en Tracing (rango Past 1 day).

## Modelos:
16/10/2026
- agente: ['zai-org/GLM-5.3-Flash']
- juez: ['qwen2.5:latest', 'qwen3:latest', 'gpt-oss:120b', 'nomic-embed-text:latest', 'qwen3:235b-a22b', 'llama4:maverick', 'gemma3:27b', 'llama3.2-vision:latest', 'llama4:17b-scout-16e-instruct-q4_K_M', 'qwen3:235b', 'bge-m3:latest', 'qwen3:32b', 'granite3.3:latest', 'qwen3:8b', 'llama3.1:405b']

