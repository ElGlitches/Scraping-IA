from datetime import datetime

def normalizar_texto(valor, por_defecto=""):
    if valor is None:
        return por_defecto
    try:
        return str(valor).strip()
    except Exception:
        return por_defecto

def fecha_actual():
    return datetime.now().strftime("%Y-%m-%d")

def calc_prioridad(modalidad: str) -> str:
    m = (modalidad or "").lower()
    if any(x in m for x in ["remote", "remoto"]):
        return "Alta"
    if any(x in m for x in ["hybrid", "híbrido", "hibrido"]):
        return "Media"
    return "Baja"
