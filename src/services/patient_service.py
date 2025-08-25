"""
Servicio de lógica de negocio para pacientes.
"""
import re
from datetime import date
from typing import List, Optional, Dict, Tuple

from src.domain.models import Paciente, TipoAtencion, Sexo, RangoFechas
from src.core.logging import get_logger
from src.core.utils import normalize_text, parse_age_to_months
from src.config.constants import TIPOS_ATENCION, TIPOS_DEFICIT, RANGOS_EDAD


logger = get_logger(__name__)


class PatientService:
    """Servicio para operaciones con pacientes."""
    
    @staticmethod
    def extract_age_range(age_text: str) -> str:
        """
        Extrae el rango de edad desde un texto.
        
        Args:
            age_text: Texto con información de edad
            
        Returns:
            Rango de edad categorizado
        """
        total_months = parse_age_to_months(age_text)
        
        if total_months == 0:
            # Verifica si hay días
            if re.search(r"(\d+)\s*d[ií]as?", age_text):
                return "Menor de 7 meses"
            return ""
        
        # Busca el rango correspondiente
        for (min_months, max_months), label in RANGOS_EDAD.items():
            if min_months <= total_months <= max_months:
                return label
        
        return ""
    
    @staticmethod
    def detect_attention_type(text: str) -> Optional[TipoAtencion]:
        """
        Detecta el tipo de atención desde un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Tipo de atención detectado o None
        """
        normalized = normalize_text(text)
        
        # Busca coincidencias (de más larga a más corta)
        for key in sorted(TIPOS_ATENCION.keys(), key=len, reverse=True):
            if key in normalized:
                value = TIPOS_ATENCION[key]
                # Mapea al enum
                for tipo in TipoAtencion:
                    if tipo.value == value:
                        return tipo
        
        return None
    
    @staticmethod
    def detect_deficit(text: str) -> Optional[str]:
        """
        Detecta déficit desde un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Déficit detectado o None
        """
        normalized = normalize_text(text)
        
        for deficit in TIPOS_DEFICIT:
            if deficit in normalized:
                return deficit
        
        return None
    
    @staticmethod
    def parse_sex(text: str) -> Optional[Sexo]:
        """
        Parsea el sexo desde un texto.
        
        Args:
            text: Texto con información de sexo
            
        Returns:
            Sexo parseado o None
        """
        normalized = normalize_text(text)
        
        if any(word in normalized for word in ["HOMBRE", "MASCULINO", "VARON"]):
            return Sexo.MASCULINO
        elif any(word in normalized for word in ["MUJER", "FEMENINO", "MUJER"]):
            return Sexo.FEMENINO
        
        return None
    
    @staticmethod
    def should_assign_lme(age_text: str) -> bool:
        """
        Determina si se debe asignar consejería LME.
        
        Args:
            age_text: Texto con información de edad
            
        Returns:
            True si la edad es menor a 4 meses
        """
        total_months = parse_age_to_months(age_text)
        return total_months < 4
    
    @staticmethod
    def analyze_anamnesis(text: str) -> Tuple[Optional[TipoAtencion], Optional[str]]:
        """
        Analiza el texto de anamnesis para extraer tipo de atención y déficit.
        
        Args:
            text: Texto de anamnesis
            
        Returns:
            Tupla con (tipo_atencion, deficit)
        """
        tipo = PatientService.detect_attention_type(text)
        deficit = PatientService.detect_deficit(text) if tipo != TipoAtencion.NSP else None
        
        return tipo, deficit
    
    @staticmethod
    def create_from_scraped_data(data: Dict) -> Paciente:
        """
        Crea un paciente desde datos scrapeados.
        
        Args:
            data: Diccionario con datos del paciente
            
        Returns:
            Instancia de Paciente
        """
        # Parsea fecha si viene como string
        fecha = data.get("fecha")
        if isinstance(fecha, str):
            try:
                from datetime import datetime
                fecha = datetime.strptime(fecha, "%d-%m-%Y").date()
            except:
                fecha = None
        
        # Parsea tipo de atención
        tipo_atencion = None
        if data.get("tipo_atencion"):
            tipo_atencion = PatientService.detect_attention_type(data["tipo_atencion"])
        
        # Parsea sexo
        sexo = None
        if data.get("sexo"):
            sexo = PatientService.parse_sex(data["sexo"])
        
        return Paciente(
            run=data.get("run", ""),
            nombre=data.get("nombre", ""),
            fecha=fecha,
            sector=data.get("sector"),
            edad_rango=data.get("edad_rango"),
            sexo=sexo,
            tipo_atencion=tipo_atencion,
            deficit=data.get("deficit"),
            consejeria=data.get("consejeria")
        )