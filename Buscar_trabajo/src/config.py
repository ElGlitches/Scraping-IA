from datetime import datetime

# --- 1. Configuración de Google Sheets ---
SHEET_NAME = "Vacantes_Automatizadas" 

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

PALABRAS_CLAVE = [
    # ------------------
    # CORE: Tu Stack Actual (Mantener)
    # ------------------
    "python",
    "automatización",
    "backend",
    "cloud",
    "sql",

    # ------------------
    # ENFOQUE: Arquitectura y Plataforma (Nuevas)
    # ------------------
    "Arquitecto",          # Buscando explícitamente roles de diseño de alto nivel.
    "Kubernetes",          # Tecnología premium de Cloud/DevOps.
    "Microservicios",      # Arquitectura Senior/Patrones de Diseño.
    "Plataforma",          # Roles de Ingeniería de Plataforma (sin gestión de personas).
    "Infraestructura",     # Roles de diseño de la base Cloud/Infra.
    "SRE",                 # Site Reliability Engineer (Ingeniería de Fiabilidad, muy técnico).
    
    # ------------------
    # ENFOQUE: Datos y Especialización (Nuevas)
    # ------------------
    "Ingeniero de Datos",  # Rol de BCI y tu especialidad en ETL/Tuning.
    "Databricks",          # Tecnología de Data de alta demanda.
    "data scientist",      # Aunque no es tu foco, te expone a roles de MLOps/DataOps.
    "ETL",                 # Tu expertise en flujos de datos.
]

MAX_VACANTES_POR_PALABRA = 20 # Límite para cada keyword/portal

# 🌐 URLs Base para Scraping (Usar {} para formato de string)
URL_GETONBRD = "https://www.getonbrd.com/api/v0/search/jobs?query={}"
# URL_LINKEDIN = "..." 
# URL_COMPUTRABAJO = "..." 

