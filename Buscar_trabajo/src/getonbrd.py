# --- Importaciones ---
import requests
import json
from .config import URL_GETONBRD, MAX_VACANTES_POR_PALABRA
from .utils import fecha_actual, calc_prioridad
# --- Fin Importaciones ---

def _procesar_resultados_getonbrd(json_data: list, keyword: str):
    """Analiza la respuesta JSON de GetOnBrd y extrae las vacantes."""
    vacantes_procesadas = []
    
    # Asumo que la data principal está en 'data' y es una lista de resultados
    for item in json_data[:MAX_VACANTES_POR_PALABRA]: 
        
        vacante_dict = {
            "titulo": item.get("title", ""),
            "empresa": item.get("organization", {}).get("name", ""),
            "ubicacion": item.get("location_name", "No indicado"),
            "modalidad": item.get("remote_allowed", False), # Ejemplo de booleano
            "nivel": item.get("seniority_name", ""),
            "jornada": item.get("salary_range", "No informado"),
            "url": item.get("url", ""),
            "salario": item.get("salary_range", "No informado"),
            "fecha_busqueda": fecha_actual(), 
            "fecha_publicacion": item.get("published_at", ""),
            "prioridad": calc_prioridad(item.get("remote_allowed")), # Usar la lógica de config
            "descripcion": item.get("description", ""),
            "keyword_buscada": keyword 
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
        print(json.dumps(data['data'][0], indent=2))
        
        if 'data' in data and isinstance(data['data'], list):
            vacantes_raw.extend(
                _procesar_resultados_getonbrd(data['data'], keyword)
            )
            
    except requests.exceptions.RequestException as e:
        # Lanza una excepción para que sea capturada por el ThreadPoolExecutor
        raise Exception(f"Error HTTP en GetOnBrd para '{keyword}': {e}") 
        
    return vacantes_raw