"""
Constantes del dominio.
"""

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

# Mapeo de tipos de atención
TIPOS_ATENCION = {
    "ATENCION PRESENCIAL": "ASISTE",
    "NO SE PRESENT": "NSP",
    "NSP": "NSP",
    "LLAMADO TELEFONICO EFECTIVO": "LLAMADO TELEFÓNICO EFECTIVO",
    "LLAMADO TELEFONICO INEFECTIVO": "LLAMADO TELEFÓNICO INEFECTIVO",
    "VIDEOLLAMADA EFECTIVA": "VIDEOLLAMADA EFECTIVA",
    "VIDEOLLAMADA INEFECTIVA": "VIDEOLLAMADA INEFECTIVA",
    "MENSAJERIA DE TEXTO": "MENSAJERÍA DE TEXTO",
    "VISITA DOMICILARIA INTEGRAL EFECTIVA": "V.D.I EFECTIVA",
    "VISITA DOMICILARIA INTEGRAL INEFECTIVA": "V.D.I INEFECTIVA",
    "EGRESO ADMINISTRATIVO": "EGRESO ADMINISTRATIVO",
}

# Tipos de déficit
TIPOS_DEFICIT = ["REZAGO", "RIESGO", "RETRASO", "RBPS", "NANEAS"]

# Rangos de edad
RANGOS_EDAD = {
    (0, 6): "Menor de 7 meses",
    (7, 11): "7-11 MESES",
    (12, 17): "12-17 MESES",
    (18, 23): "18-23 MESES",
    (24, 47): "24-47 MESES",
    (48, 59): "48-59 MESES",
    (60, float('inf')): "60 MESES O MÁS"
}