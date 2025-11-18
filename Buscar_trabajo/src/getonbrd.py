# --- Importaciones ---
import requests
import json
from .config import URL_GETONBRD, MAX_VACANTES_POR_PALABRA
from .utils import fecha_actual, calc_prioridad
from bs4 import BeautifulSoup
from datetime import datetime , timedelta# 👈 ¡IMPORTACIÓN FALTANTE!
# --- Fin Importaciones ---

# --- Constante de Límite ---
LIMITE_ANTIGUEDAD_DIAS = 60 # Máximo 2 meses

def _procesar_resultados_getonbrd(json_data: list, keyword: str):
    """
    Analiza la respuesta JSON de GetOnBrd, aplica el filtro de antigüedad, 
    y extrae las vacantes con el mapeo corregido.
    """
    vacantes_procesadas = []
    
    # 1. CALCULAR FECHA LÍMITE
    fecha_limite = datetime.now() - timedelta(days=LIMITE_ANTIGUEDAD_DIAS)
    
    for item in json_data[:MAX_VACANTES_POR_PALABRA]: 
  
        # 💡 Acceso a secciones principales del JSON
        attributes = item.get("attributes", {})
        links = item.get("links", {})
        timestamp_publicacion = attributes.get("published_at")

        # ⚠️ FILTRO DE ANTIGÜEDAD (Si es demasiado viejo, lo saltamos)
        if timestamp_publicacion:
            fecha_publicacion = datetime.fromtimestamp(timestamp_publicacion)
            
            if fecha_publicacion < fecha_limite:
                continue # Omitir y pasar a la siguiente vacante
        # 💡 NUEVA LÓGICA DE EXTRACCIÓN BASADA EN EL ID
        item_id = item.get("id", "")
        
        # El ID está formateado como: [Título-de-la-Vacante]-[NOMBRE-EMPRESA]-[UBICACION-OPCIONAL]-[ID]
        parts = item_id.split('-')
        
        # Opción segura (requiere la lógica de tu negocio)
        empresa_candidata = parts[-3] if len(parts) >= 3 else "No indicado" 
        
        # Opción que busca el nombre de la empresa directamente en el ID:
        empresa_en_id = item_id.split('-proyecto-')[-1].split('-')[0] if '-proyecto-' in item_id else parts[-3]
        
        # 2. UBICACIÓN: Si el ID termina con una ciudad, lo extraemos
        ubicacion_candidata = parts[-1] if parts[-1].isalpha() else "Remoto/No indicado"
        
        # --- 2. CORRECCIÓN DE UBICACIÓN Y NIVEL ---
        # Ubicación: Usamos el campo cities o regions si están disponibles
        cities_data = attributes.get("location_cities", {}).get("data", [])
        regions_data = attributes.get("location_regions", {}).get("data", [])
        
        if cities_data:
            ubicacion_str = "Ciudad Principal" # Simplificación, ya que el JSON solo da un ID aquí
        elif regions_data:
            ubicacion_str = "Región Principal"
        else:
            ubicacion_str = "Remoto" if attributes.get("remote") else "No indicado"
        seniority_type = attributes.get("seniority", {}).get("data", {}).get("type", "no_seniority")
        # Nivel: seniority_name está disponible en el JSON, lo usaremos.
        nivel_str = attributes.get("seniority", {}).get("data", {}).get("type", "").replace("seniority", "").capitalize()
         # --- 3. CORRECCIÓN DE FECHA DE PUBLICACIÓN Y DESCRIPCIÓN ---
        
        # Fecha de Publicación: Se envía como un timestamp Unix (número grande).
        timestamp_publicacion = attributes.get("published_at")
        
        # Descripción: Contiene etiquetas HTML que deben eliminarse.
        descripcion_html = attributes.get("description", "")
        descripcion_limpia = BeautifulSoup(descripcion_html, 'html.parser').get_text(separator=' ', strip=True)

        # Salario: Mapeo de mínimo y máximo a una sola cadena
        min_salary = attributes.get("min_salary")
        max_salary = attributes.get("max_salary")
        salario_str = f"${min_salary} - ${max_salary}" if min_salary or max_salary else "No informado"

        vacante_dict = {
            # ✅ URL: Se extrae correctamente de 'links'
            "url": links.get("public_url", ""), 

            "titulo": attributes.get("title", "No indicado"), 
            
            # 👈 CORRECCIÓN 1: Usamos la extracción del ID
            "empresa": empresa_en_id.replace('-', ' ').title(), 
            
            # 👈 CORRECCIÓN 2: Usamos la ubicación extraída del ID
            "ubicacion": ubicacion_candidata.capitalize(),
            
            # ✅ TÍTULO Y DESCRIPCIÓN LIMPIA
            "titulo": attributes.get("title", "No indicado"), 
            "descripcion": descripcion_limpia, # 👈 CORRECCIÓN 1: Limpieza de HTML
         
            # 👈 CORRECCIÓN 3: Uso de seniority limpio
            "nivel": nivel_str,
            
            # 👈 CORRECCIÓN 4: Formato de Fecha de Publicación
            "fecha_publicacion": datetime.fromtimestamp(timestamp_publicacion).strftime('%Y-%m-%d') if timestamp_publicacion else "",
            
            # Otros campos... (Se asume que están correctos)
            "modalidad": attributes.get("remote_modality", "Presencial/Híbrido"),
            "salario": f"${attributes.get('min_salary', '0')} - ${attributes.get('max_salary', '0')}" if attributes.get('min_salary') else "No informado",
            "fecha_busqueda": fecha_actual(),
            "prioridad": calc_prioridad(attributes.get("remote")),
        }
        
        vacantes_procesadas.append(vacante_dict)
        
    return vacantes_procesadas

# ⚠️ Función principal (debe recibir el argumento 'keyword')
def buscar_vacantes_getonbrd(keyword: str): 
    """Realiza la solicitud API a GetOnBrd para una única palabra clave."""
    
    vacantes_raw = []
    url = URL_GETONBRD.format(requests.utils.quote(keyword)) # Codificar keyword para la URL
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        #print(json.dumps(data['data'][0], indent=2))
        
        if 'data' in data and isinstance(data['data'], list):
            vacantes_raw.extend(
                _procesar_resultados_getonbrd(data['data'], keyword)
            )
            
    except requests.exceptions.RequestException as e:
        # Lanza una excepción para que sea capturada por el ThreadPoolExecutor
        raise Exception(f"Error HTTP en GetOnBrd para '{keyword}': {e}") 
        
    return vacantes_raw