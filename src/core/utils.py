"""
Utilidades generales del proyecto.
"""
import re
import unicodedata
from typing import Optional, Any


def normalize_text(text: str) -> str:
    """
    Normaliza texto eliminando acentos y espacios extras.
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado en mayúsculas
    """
    if not text:
        return ""
    
    # Elimina acentos
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    
    # Convierte a mayúsculas y limpia espacios
    text = text.upper()
    text = re.sub(r"\s+", " ", text)
    
    return text.strip()


def is_empty(value: Any) -> bool:
    """
    Verifica si un valor está vacío.
    
    Args:
        value: Valor a verificar
        
    Returns:
        True si el valor está vacío
    """
    if value is None:
        return True
    
    if isinstance(value, str):
        return value.strip().lower() in {"", "nan", "none", "null"}
    
    try:
        import math
        import pandas as pd
        if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
            return True
    except:
        pass
    
    return False


def format_rut(rut: str) -> str:
    """
    Formatea un RUT chileno.
    
    Args:
        rut: RUT sin formato
        
    Returns:
        RUT formateado (ej: "12.345.678-9")
    """
    # Limpia el RUT
    rut = re.sub(r"[^\dkK]", "", rut)
    
    if len(rut) < 2:
        return rut
    
    # Separa cuerpo y dígito verificador
    cuerpo = rut[:-1]
    dv = rut[-1].upper()
    
    # Formatea el cuerpo con puntos
    cuerpo_invertido = cuerpo[::-1]
    partes = [cuerpo_invertido[i:i+3] for i in range(0, len(cuerpo_invertido), 3)]
    cuerpo_formateado = ".".join(partes)[::-1]
    
    return f"{cuerpo_formateado}-{dv}"


def clean_name(name: str) -> str:
    """
    Limpia un nombre eliminando paréntesis y contenido.
    
    Args:
        name: Nombre a limpiar
        
    Returns:
        Nombre limpio
    """
    if not name:
        return ""
    
    # Elimina paréntesis y su contenido
    name = re.sub(r"[（(][^）)]*[）)]", "", name, flags=re.UNICODE)
    
    # Limpia espacios múltiples
    name = re.sub(r"\s+", " ", name).strip()
    
    return name


def parse_age_to_months(age_str: str) -> int:
    """
    Convierte una cadena de edad a meses totales.
    
    Args:
        age_str: Cadena con la edad (ej: "2 años 3 meses")
        
    Returns:
        Edad total en meses
    """
    years = 0
    months = 0
    
    # Busca años
    match_years = re.search(r"(\d+)\s*años?", age_str, re.IGNORECASE)
    if match_years:
        years = int(match_years.group(1))
    
    # Busca meses
    match_months = re.search(r"(\d+)\s*mes(es)?", age_str, re.IGNORECASE)
    if match_months:
        months = int(match_months.group(1))
    
    return years * 12 + months