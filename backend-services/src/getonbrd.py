import requests
import json
from .config import URL_GETONBRD, MAX_VACANTES_POR_PALABRA
from .utils import fecha_actual, calc_prioridad
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

LIMITE_ANTIGUEDAD_DIAS = 60

def _procesar_resultados_getonbrd(json_data: list, keyword: str):
    """
    Analiza la respuesta JSON de GetOnBrd, aplica el filtro de antigüedad, 
    y extrae las vacantes con el mapeo corregido.
    """
    vacantes_procesadas = []
    
    fecha_limite = datetime.now() - timedelta(days=LIMITE_ANTIGUEDAD_DIAS)
    
    for item in json_data[:MAX_VACANTES_POR_PALABRA]: 
  
        attributes = item.get("attributes", {})
        links = item.get("links", {})
        timestamp_publicacion = attributes.get("published_at")

        if timestamp_publicacion:
            fecha_publicacion = datetime.fromtimestamp(timestamp_publicacion)
            
            if fecha_publicacion < fecha_limite:
                continue
        
        company_data = attributes.get("company", {}).get("data", {})
        if company_data:
             empresa_candidata = company_data.get("attributes", {}).get("name", "No indicado")
        else:
             parts = item_id.split('-')
             empresa_candidata = parts[-3] if len(parts) >= 3 else "No indicado"

        cities_data = attributes.get("location_cities", {}).get("data", [])
        regions_data = attributes.get("location_regions", {}).get("data", [])
        
        ubicacion_str = "No indicado"
        if cities_data:
            nombres_ciudades = [c.get("attributes", {}).get("name") for c in cities_data]
            nombres_ciudades = [n for n in nombres_ciudades if n] 
            ubicacion_str = ", ".join(nombres_ciudades) if nombres_ciudades else "No indicado"
        elif regions_data:
            nombres_regiones = [r.get("attributes", {}).get("name") for r in regions_data]
            nombres_regiones = [n for n in nombres_regiones if n] 
            ubicacion_str = ", ".join(nombres_regiones) if nombres_regiones else "No indicado"
        else:
            ubicacion_str = "Remoto" if attributes.get("remote") else "No indicado"

        seniority_data = attributes.get("seniority", {}).get("data", {})
        if seniority_data:
            nivel_str = seniority_data.get("attributes", {}).get("name", "No indicado")
        else:
            nivel_str = "No indicado"
        
        timestamp_publicacion = attributes.get("published_at")
        
        descripcion_html = attributes.get("description", "")
        descripcion_limpia = BeautifulSoup(descripcion_html, 'html.parser').get_text(separator=' ', strip=True)

        min_salary = attributes.get("min_salary")
        max_salary = attributes.get("max_salary")
        salario_str = f"${min_salary} - ${max_salary}" if min_salary or max_salary else "No informado"

        vacante_dict = {
            "titulo": attributes.get("title", "No indicado"), 
            "url": links.get("public_url", ""), 
            "descripcion": descripcion_limpia,
            
            "fecha_publicacion": fecha_publicacion.strftime("%Y-%m-%d"),
            
            "empresa": empresa_candidata,
            "ubicacion": ubicacion_str,
            "modalidad": "Remoto" if attributes.get("remote") else "Presencial",
            "nivel": nivel_str,
            "jornada": attributes.get("modality", {}).get("data", {}).get("attributes", {}).get("name", "No indicado"),
            "salario": salario_str,
            
            "fecha_busqueda": fecha_actual(),
            "prioridad": calc_prioridad(attributes.get("remote")),
            "keyword_buscada": keyword
        }
        
        vacantes_procesadas.append(vacante_dict)
        
    return vacantes_procesadas

def buscar_vacantes_getonbrd(keyword: str): 
    """Realiza la solicitud API a GetOnBrd para una única palabra clave."""
    
    vacantes_raw = []
    url = URL_GETONBRD.format(requests.utils.quote(keyword))
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and isinstance(data['data'], list):
            vacantes_raw.extend(
                _procesar_resultados_getonbrd(data['data'], keyword)
            )
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error HTTP en GetOnBrd para '{keyword}': {e}") 
        
    return vacantes_raw