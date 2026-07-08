"""
logger.py — Sistema de logging estructurado para el chatbot multiagente.

Proporciona logging centralizado con niveles configurables y rotación de archivos.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class StructuredLogger:
    """Logger centralizado con soporte para múltiples niveles y handlers."""
    
    _instance: Optional['StructuredLogger'] = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs) -> 'StructuredLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, name: str = "veltri_chatbot", level: int = logging.INFO):
        """Inicializa el logger singleton.
        
        Args:
            name: Nombre del logger.
            level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        """
        if self._initialized:
            return
            
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Crear directorio de logs si no existe
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Formato estructurado
        formatter = logging.Formatter(
            fmt='[%(asctime)s] %(name)s - %(levelname)-8s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Handler archivo con rotación
        file_handler = RotatingFileHandler(
            log_dir / "chatbot.log",
            maxBytes=5_242_880,  # 5MB
            backupCount=3
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Handler para errores
        error_handler = RotatingFileHandler(
            log_dir / "chatbot_errors.log",
            maxBytes=5_242_880,
            backupCount=2
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
        
        self._initialized = True
    
    def debug(self, msg: str, **kwargs) -> None:
        """Log a debug message."""
        self.logger.debug(msg, **kwargs)
    
    def info(self, msg: str, **kwargs) -> None:
        """Log an info message."""
        self.logger.info(msg, **kwargs)
    
    def warning(self, msg: str, **kwargs) -> None:
        """Log a warning message."""
        self.logger.warning(msg, **kwargs)
    
    def error(self, msg: str, **kwargs) -> None:
        """Log an error message."""
        self.logger.error(msg, **kwargs)
    
    def critical(self, msg: str, **kwargs) -> None:
        """Log a critical message."""
        self.logger.critical(msg, **kwargs)
    
    def exception(self, msg: str, **kwargs) -> None:
        """Log an exception with traceback."""
        self.logger.exception(msg, **kwargs)


def get_logger(name: str = "veltri_chatbot") -> StructuredLogger:
    """Obtiene instancia del logger singleton.
    
    Args:
        name: Nombre del logger (por defecto es el nombre global).
    
    Returns:
        Instancia singleton del logger estructurado.
    """
    return StructuredLogger(name)
