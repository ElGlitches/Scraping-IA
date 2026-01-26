from datetime import datetime

SHEET_NAME = "Vacantes_Automatizadas" 

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

PALABRAS_CLAVE = [
    "Python",
    "Ingeniero de Datos",
    "ETL",
    "Automatización",
    "SQL",
    "DevOps",
    "SRE",
    "Backend",
    "AWS",
    "Scripting",         
    "Linux",             
    "Cloud Engineer",    
    "Infraestructura",   
    "Integración",       
    "API Rest",          
    "Bash",              
    "Ansible",           
    "Docker"
]

PALABRAS_EXCLUIDAS = [
    # Roles Comerciales (La mayor fuente de ruido)
    "Ventas", "Sales", "Comercial", "Account", "Ejecutivo", "Business",
    "Manager", "Líder", "Lead", "Jefe", # Evita roles de gestión de personas si no buscas eso

    # Roles de Diseño/Producto
    "Designer", "Diseñador", "UX", "UI", "Product", "Marketing", "Growth",
    "Multimedia", "Grafico", "Audiovisual",

    # Roles Técnicos que NO quieres
    "Frontend", "Front-end",
    "Full Stack", "Fullstack", "Full-Stack", # Dijiste explícitamente que no te sientes cómodo
    "Mobile", "Android", "iOS", "Flutter", "React Native",
    "CMS", "Wordpress", # Evita desarrollo web básico
    "Soporte", "Help Desk", "Mesa de ayuda", # Evita roles de nivel 1

    # Seniority/Idioma (Opcional, según tu filtro)
    "Intern", "Práctica", "Trainee",
    "Bilingüe", "English Only" # Si quieres filtrar el inglés desde la raíz
]

MAX_VACANTES_POR_PALABRA = 20

URL_GETONBRD = "https://www.getonbrd.com/api/v0/search/jobs?query={}&expand=[\"company\",\"location_cities\",\"seniority\",\"modality\"]"

RUTA_CV = "cv.pdf" 

