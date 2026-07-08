"""
swarm.py — Motor de ejecución Swarm con modelo Gemini.

Ejecuta consultas contra el modelo Google Gemini con reintentos automáticos,
metricas de latencia, y manejo robusto de errores.
"""

import time
import google.genai as genai
import google.genai.types as types
from typing import Tuple, Optional, List, Dict, Any
from config.settings import MODELO, MAX_REINTENTOS, ESPERA_REINTENTO, get_client
from core.agent import Agent
from core.metrics import MetricsTracker

try:
    from core.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def run_swarm_gemini(
    agent: Agent,
    messages: List[Dict[str, str]],
    metrics_tracker: MetricsTracker,
    event_bus: Optional[Any] = None,
    verbose: bool = False
) -> Tuple[Agent, str]:
    """Ejecuta una consulta al modelo Gemini usando un agente especializado.
    
    Implementa:
    - Reintentos automáticos con backoff exponencial para errores 429
    - Captura de métricas (tokens, latencia)
    - Publicación de eventos a través del EventBus
    - Logging estructurado de operaciones
    
    Args:
        agent: Agente especializado que define la instrucción de sistema.
        messages: Historial de mensajes en formato [{"role": "user/assistant", "content": "..."}].
        metrics_tracker: Rastreador para registrar métricas de rendimiento.
        event_bus: Bus de eventos opcional para notificaciones de sistema (por defecto None).
        verbose: Si True, imprime logs detallados (por defecto False).
    
    Returns:
        Tupla (agent, respuesta_texto) donde respuesta_texto es la salida del modelo.
    
    Raises:
        RuntimeError: Si se agota el número máximo de reintentos sin éxito.
    """
    client = get_client()

    if not isinstance(agent, Agent):
        raise ValueError(f"agent debe ser instancia de Agent, recibido: {type(agent)}")
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages debe ser una lista no vacía de mensajes")
    if not isinstance(metrics_tracker, MetricsTracker):
        raise ValueError("metrics_tracker debe ser instancia de MetricsTracker")

    if event_bus:
        event_bus.publish("llamada_gemini_iniciada", {
            "agente": agent.name,
            "total_mensajes": len(messages)
        })

    # Construir historial compatible con google.genai
    contents = []
    for msg in messages:
        role = "user" if msg.get("role") == "user" else "model"
        contenido = msg.get("content", "")
        if not contenido:
            logger.warning(f"Mensaje vacío detectado, saltando")
            continue
        contents.append(types.Content(
            role=role,
            parts=[types.Part(text=str(contenido))]
        ))

    # Configuración de generación con instrucciones de sistema del agente
    config = types.GenerateContentConfig(
        system_instruction=agent.instructions,
        temperature=0.7,
    )

    # Reintentos con backoff exponencial
    ultima_excepcion: Optional[Exception] = None
    for intento in range(1, MAX_REINTENTOS + 1):
        if verbose:
            logger.info(f"Motor Swarm: Llamando a {MODELO} como [{agent.name}] (intento {intento}/{MAX_REINTENTOS})")
        
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
            except (AttributeError, Exception) as e:
                logger.debug(f"No se pudo obtener token count: {e}")

            metrics_tracker.registrar_llamada(tokens, latencia)

            if verbose:
                logger.info(f"Éxito: latencia={latencia:.2f}s | tokens={tokens}")

            # Extraer texto de respuesta
            try:
                texto = response.text
                if not texto or not isinstance(texto, str):
                    texto = "[SISTEMA: El modelo no generó una respuesta de texto válida]"
                    logger.warning("Respuesta del modelo está vacía o inválida")
            except (ValueError, AttributeError) as e:
                texto = f"[SISTEMA: Error extrayendo respuesta: {type(e).__name__}]"
                logger.error(f"Error extrayendo texto: {e}")

            if event_bus:
                event_bus.publish("llamada_gemini_exito", {
                    "agente": agent.name,
                    "tokens": tokens,
                    "latencia": latencia
                })

            logger.info(f"Llamada Gemini exitosa ({agent.name})")
            return agent, texto

        except Exception as e:
            t1 = time.time()
            error_str = str(e)
            ultima_excepcion = e

            if event_bus:
                event_bus.publish("llamada_gemini_error", {
                    "agente": agent.name,
                    "error": error_str[:100],
                    "intento": intento
                })

            # Detectar error 429 (cuota agotada)
            if "429" in error_str and intento < MAX_REINTENTOS:
                espera = ESPERA_REINTENTO * intento
                logger.warning(f"Error 429 detectado. Esperando {espera}s antes de reintentar...")
                if verbose:
                    print(f"  [REINTENTO] Error 429 (cuota). Esperando {espera}s...")
                time.sleep(espera)
            else:
                logger.error(
                    f"Error en llamada Gemini (intento {intento}): "
                    f"{type(e).__name__}: {error_str[:120]}"
                )
                if intento < MAX_REINTENTOS:
                    continue
                else:
                    # Último intento falló
                    error_msg = (
                        f"Error tras {MAX_REINTENTOS} intentos - {type(e).__name__}. "
                        f"Contacta a soporte o reintenta en unos minutos."
                    )
                    logger.critical(f"Fallo crítico en Swarm: {error_msg}")
                    return agent, f"[SISTEMA: {error_msg}]"
    
    # Fallback final (no debería llegar aquí)
    logger.critical(f"Salida inesperada después de {MAX_REINTENTOS} intentos")
    return agent, "[SISTEMA: Error fatal en motor Swarm. Por favor, reinicia.]"
