from datetime import datetime

# --- 1. Configuración de Google Sheets ---
SHEET_NAME = "Vacantes_Automatizadas" 

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- 2. Parámetros de Búsqueda ---
# 💬 Palabras clave para buscar vacantes
PALABRAS_CLAVE = [
    "python",
    "data scientist",
    "automatización",
    "etl",
    "backend",
    "devops",
    "cloud",
    "java",
    "sql"
]

MAX_VACANTES_POR_PALABRA = 50 # Límite para cada keyword/portal

# 🌐 URLs Base para Scraping (Usar {} para formato de string)
URL_GETONBRD = "https://www.getonbrd.com/api/v0/search/jobs?query={}"
# URL_LINKEDIN = "..." 
# URL_COMPUTRABAJO = "..." 

