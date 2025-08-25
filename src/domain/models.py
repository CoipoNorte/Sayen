"""
Modelos de dominio.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


class TipoAtencion(Enum):
    """Tipos de atención posibles."""
    ASISTE = "ASISTE"
    NSP = "NSP"
    LLAMADO_EFECTIVO = "LLAMADO TELEFÓNICO EFECTIVO"
    LLAMADO_INEFECTIVO = "LLAMADO TELEFÓNICO INEFECTIVO"
    VIDEOLLAMADA_EFECTIVA = "VIDEOLLAMADA EFECTIVA"
    VIDEOLLAMADA_INEFECTIVA = "VIDEOLLAMADA INEFECTIVA"
    MENSAJERIA = "MENSAJERÍA DE TEXTO"
    VDI_EFECTIVA = "V.D.I EFECTIVA"
    VDI_INEFECTIVA = "V.D.I INEFECTIVA"
    EGRESO_ADMIN = "EGRESO ADMINISTRATIVO"


class Sexo(Enum):
    """Sexo biológico."""
    MASCULINO = "MASCULINO"
    FEMENINO = "FEMENINO"
    NO_ESPECIFICADO = "NO ESPECIFICADO"


@dataclass
class Paciente:
    """Modelo de paciente."""
    run: str
    nombre: str
    fecha: Optional[date] = None
    sector: Optional[str] = None
    edad_rango: Optional[str] = None
    sexo: Optional[Sexo] = None
    tipo_atencion: Optional[TipoAtencion] = None
    deficit: Optional[str] = None
    consejeria: Optional[str] = None
    
    def __post_init__(self):
        """Valida y normaliza datos después de la inicialización."""
        from src.core.utils import format_rut, clean_name
        
        if self.run:
            self.run = format_rut(self.run)
        if self.nombre:
            self.nombre = clean_name(self.nombre)
    
    @property
    def is_complete(self) -> bool:
        """Verifica si el paciente tiene todos los datos."""
        return all([
            self.run,
            self.nombre,
            self.fecha,
            self.sexo,
            self.tipo_atencion
        ])
    
    def to_dict(self) -> dict:
        """Convierte el paciente a diccionario."""
        return {
            "RUN": self.run,
            "NOMBRE": self.nombre,
            "FECHA": self.fecha.strftime("%d-%m-%Y") if self.fecha else "",
            "SECTOR": self.sector or "",
            "EDAD": self.edad_rango or "",
            "SEXO": self.sexo.value if self.sexo else "",
            "TIPO DE ATENCIÓN": self.tipo_atencion.value if self.tipo_atencion else "",
            "DÉFICIT": self.deficit or "",
            "CONSEJERIA": self.consejeria or ""
        }


@dataclass
class RangoFechas:
    """Rango de fechas para búsqueda."""
    anio: int
    mes: int
    dia_inicio: int
    dia_fin: int
    
    def __post_init__(self):
        """Valida el rango de fechas."""
        if not 1 <= self.mes <= 12:
            raise ValueError(f"Mes inválido: {self.mes}")
        
        if not 1 <= self.dia_inicio <= 31:
            raise ValueError(f"Día de inicio inválido: {self.dia_inicio}")
        
        if not 1 <= self.dia_fin <= 31:
            raise ValueError(f"Día de fin inválido: {self.dia_fin}")
        
        if self.dia_inicio > self.dia_fin:
            raise ValueError("El día de inicio no puede ser mayor al día de fin")
    
    def get_dates(self) -> List[date]:
        """Obtiene lista de fechas en el rango (excluyendo fines de semana)."""
        dates = []
        for dia in range(self.dia_inicio, self.dia_fin + 1):
            try:
                fecha = date(self.anio, self.mes, dia)
                # Excluye sábados (5) y domingos (6)
                if fecha.weekday() < 5:
                    dates.append(fecha)
            except ValueError:
                continue
        return dates