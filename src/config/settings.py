"""
Configuración central del proyecto.
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# Intenta cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class Settings:
    """Configuración de la aplicación."""
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOG_DIR: Path = BASE_DIR / "logs"
    
    # Rayen credentials
    RAYEN_LOCATION: str = os.getenv("RAYEN_LOCATION", "")
    RAYEN_USERNAME: str = os.getenv("RAYEN_USERNAME", "")
    RAYEN_PASSWORD: str = os.getenv("RAYEN_PASSWORD", "")
    
    # Selenium
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() in {"1", "true", "yes"}
    SELENIUM_TIMEOUT: int = 20
    
    # URLs
    BASE_URL: str = "https://clinico.rayenaps.cl/"
    
    # Excel
    DEFAULT_SHEET_NAME: str = "Sheet1"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def __post_init__(self):
        """Crea directorios necesarios."""
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOG_DIR.mkdir(exist_ok=True)
    
    @property
    def env_file_path(self) -> Path:
        """Ruta al archivo .env."""
        return self.BASE_DIR / ".env"
    
    def validate_credentials(self) -> bool:
        """Valida que las credenciales estén completas."""
        return all([self.RAYEN_LOCATION, self.RAYEN_USERNAME, self.RAYEN_PASSWORD])
    
    def update_env_file(self, data: dict) -> None:
        """Actualiza el archivo .env con nuevos valores."""
        lines = []
        for key, value in data.items():
            # Escapa valores con espacios o caracteres especiales
            if isinstance(value, str) and any(c in value for c in [" ", "#", "=", "\t"]):
                value = f'"{value}"'
            lines.append(f"{key}={value}")
        
        with open(self.env_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


settings = Settings()