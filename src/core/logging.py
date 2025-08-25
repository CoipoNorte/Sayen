"""
Sistema de logging centralizado.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.config.settings import settings


class ColoredFormatter(logging.Formatter):
    """Formatter con colores para consola."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class LoggerManager:
    """Gestor centralizado de logging."""
    
    _instance: Optional['LoggerManager'] = None
    _loggers: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.setup_root_logger()
    
    def setup_root_logger(self):
        """Configura el logger raíz."""
        root_logger = logging.getLogger()
        root_logger.setLevel(settings.LOG_LEVEL)
        
        # Handler para consola con colores
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(settings.LOG_FORMAT))
        root_logger.addHandler(console_handler)
        
        # Handler para archivo
        log_file = settings.LOG_DIR / f"sayen_{datetime.now():%Y%m%d}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
        root_logger.addHandler(file_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Obtiene o crea un logger con el nombre especificado."""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]


# Instancia global
logger_manager = LoggerManager()
get_logger = logger_manager.get_logger