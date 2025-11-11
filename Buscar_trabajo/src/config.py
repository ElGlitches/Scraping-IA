from datetime import datetime

# 🧾 Nombre del archivo de Google Sheets
SHEET_NAME = "Vacantes_Automatizadas"  # Puedes cambiarlo al nombre de tu hoja en Drive

# 🔐 Scopes necesarios para Google Sheets y Drive API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 🌐 URL base para GetOnBrd
URL_GETONBRD = "https://www.getonbrd.com/api/v0/search/jobs?query={}"

# 💬 Palabras clave para buscar vacantes
PALABRAS_CLAVE = [
    "python",
    "data",
    "automatización",
    "etl",
    "backend",
    "devops",
    "cloud"
]

MAX_VACANTES_POR_PALABRA = 30

# ⚙️ Utilidades generales (puedes tenerlas en utils.py, pero dejo algunas aquí por claridad)
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
    modalidad = (modalidad or "").lower()
    if "remoto" in modalidad:
        return "Alta"
    elif "híbrido" in modalidad:
        return "Media"
    return "Baja"
