# src/utils.py

from datetime import datetime
# Importamos calc_prioridad si usa otra utilidad interna, pero aquí solo necesita datetime

def fecha_actual():
    """Devuelve la fecha actual en formato YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")

def normalizar_texto(texto):
    """Limpia texto de None o espacios extra"""
    if not texto:
        return ""
    return str(texto).strip()

def calc_prioridad(modalidad):
    """Asigna prioridad según modalidad u otras reglas"""
    # Esta lógica es reutilizable y no es una constante, por eso va aquí.
    modalidad = (modalidad or "").lower()
    if "remoto" in modalidad:
        return "Alta"
    elif "híbrido" in modalidad:
        return "Media"
    return "Baja"