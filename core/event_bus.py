"""
event_bus.py — Bus de eventos reactivo con patrón Pub/Sub.

Permite que componentes del Swarm se comuniquen de manera desacoplada
mediante eventos, sin contaminar la consola durante ejecución interactiva.
"""

from typing import Callable, Dict, List, Optional, Any
import time
from datetime import datetime

try:
    from core.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class EventBus:
    """Bus de eventos reactivo con patrón Pub-Sub.
    
    Características:
    - Suscripción a eventos específicos
    - Control de verbosidad para no contaminar output
    - Historial de eventos para auditoría
    - Manejo de excepciones en callbacks
    """

    def __init__(self, verbose: bool = False) -> None:
        """Inicializa el EventBus.
        
        Args:
            verbose: Si True, imprime eventos en consola. Por defecto False.
        """
        self._listeners: Dict[str, List[Callable]] = {}
        self.verbose = verbose
        self._log_history: List[Dict[str, Any]] = []
        logger.info("EventBus inicializado")

    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Suscribe una función callback a un evento específico.
        
        Args:
            event_type: Tipo de evento (ej. 'handoff_agente', 'stock_exitoso')
            callback: Función callable que recibe un diccionario de datos.
        
        Raises:
            ValueError: Si event_type o callback son inválidos.
            TypeError: Si callback no es llamable.
        """
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError(f"event_type inválido: {event_type}")
        if not callable(callback):
            raise TypeError(f"callback debe ser callable, recibido: {type(callback)}")
        
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        logger.debug(f"Callback suscrito a evento '{event_type}'")

    def publish(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Publica un evento a todos los suscriptores registrados.
        
        Args:
            event_type: Tipo de evento.
            data: Diccionario de datos asociados al evento. Por defecto {}.
        """
        if not isinstance(event_type, str) or not event_type.strip():
            logger.warning(f"Intento de publicar evento con type inválido: {event_type}")
            return
        
        data = data or {}
        timestamp = datetime.now().isoformat()
        
        entrada = {
            "timestamp": timestamp,
            "event_type": event_type,
            "data_keys": list(data.keys()) if data else []
        }
        self._log_history.append(entrada)

        if self.verbose:
            print(f"  [EVENT BUS] '{event_type}' @ {timestamp}")

        if event_type in self._listeners:
            for idx, callback in enumerate(self._listeners[event_type]):
                try:
                    callback(data)
                except Exception as e:
                    logger.error(
                        f"Error ejecutando callback #{idx} para evento '{event_type}': "
                        f"{type(e).__name__}: {str(e)[:100]}"
                    )
                    if self.verbose:
                        print(f"  [EVENT BUS ERROR] Callback error: {e}")

    def set_verbose(self, verbose: bool) -> None:
        """Activa o desactiva el logging en consola.
        
        Args:
            verbose: True para activar, False para desactivar.
        """
        self.verbose = bool(verbose)
        logger.info(f"Verbosidad del EventBus establecida a: {self.verbose}")

    def get_log_history(self) -> List[Dict[str, Any]]:
        """Retorna todos los eventos publicados (para auditoría).
        
        Returns:
            Lista de diccionarios con información de eventos.
        """
        return self._log_history.copy()

    def clear_history(self) -> None:
        """Limpia el historial de eventos."""
        count = len(self._log_history)
        self._log_history.clear()
        logger.debug(f"Historial de {count} eventos limpiado")
