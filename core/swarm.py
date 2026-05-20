import time
import google.genai as genai
import google.genai.types as types
from config.settings import MODELO, MAX_REINTENTOS, ESPERA_REINTENTO, get_client
from core.agent import Agent
from core.metrics import MetricsTracker


def run_swarm_gemini(
    agent: Agent,
    messages: list,
    metrics_tracker: MetricsTracker,
    event_bus=None,
    verbose: bool = False
) -> tuple:
    """
    Ejecuta una consulta al modelo Gemini usando el agente activo (google.genai SDK).
    Implementa reintentos automáticos con backoff para errores 429.
    Notifica a través de un EventBus si se proporciona.
    Retorna (agente_activo, respuesta_texto).

    verbose=True: imprime logs del motor (para modo evaluación docente).
    verbose=False: operación silenciosa (para modo chat interactivo limpio).
    """
    client = get_client()

    if event_bus:
        event_bus.publish("llamada_gemini_iniciada", {
            "agente": agent.name,
            "total_mensajes": len(messages)
        })

    # Construir historial compatible con google.genai
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part(text=msg["content"])]
        ))

    # Configuración de generación con instrucciones de sistema del agente
    config = types.GenerateContentConfig(
        system_instruction=agent.instructions,
        temperature=0.7,
    )

    # Reintentos con backoff exponencial
    for intento in range(1, MAX_REINTENTOS + 1):
        if verbose:
            print(f"  -> [Motor Swarm]: Llamando a {MODELO} como [{agent.name}] (intento {intento})...", flush=True)
        t0 = time.time()
        try:
            response = client.models.generate_content(
                model=MODELO,
                contents=contents,
                config=config,
            )
            t1 = time.time()
            latencia = t1 - t0

            # Capturar métricas cuantitativas
            tokens = None
            try:
                tokens = response.usage_metadata.total_token_count
            except Exception:
                pass

            metrics_tracker.registrar_llamada(tokens, latencia)

            if verbose:
                print(f"  -> [Metrica] Latencia: {latencia:.2f}s | Tokens: {tokens} | Intento: {intento}/{MAX_REINTENTOS}")

            # Extraer texto de respuesta
            try:
                texto = response.text
            except (ValueError, AttributeError):
                texto = "[SISTEMA: El modelo no generó una respuesta de texto válida]"

            if event_bus:
                event_bus.publish("llamada_gemini_exito", {
                    "agente": agent.name,
                    "tokens": tokens,
                    "latencia": latencia
                })

            return agent, texto

        except Exception as e:
            t1 = time.time()
            error_str = str(e)

            if event_bus:
                event_bus.publish("llamada_gemini_error", {
                    "agente": agent.name,
                    "error": error_str,
                    "intento": intento
                })

            if "429" in error_str and intento < MAX_REINTENTOS:
                espera = ESPERA_REINTENTO * intento
                if verbose:
                    print(f"  -> [REINTENTO] Error 429 (cuota). Esperando {espera}s antes del intento {intento+1}...")
                time.sleep(espera)
            else:
                if verbose:
                    print(f"  -> [ERROR] Fallo en la llamada a Gemini (intento {intento}): {type(e).__name__}: {error_str[:120]}")
                if intento == MAX_REINTENTOS:
                    return agent, f"[SISTEMA: Error tras {MAX_REINTENTOS} intentos - {type(e).__name__}. Espera unos minutos y reintenta.]"
