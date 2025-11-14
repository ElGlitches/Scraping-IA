# --- 1. Importaciones ---
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed # Para concurrencia

# Asegura que Python encuentre los módulos en la carpeta 'src'
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importa las funciones de los módulos
from src.getonbrd import buscar_vacantes_getonbrd
# Agrega aquí tus otras funciones de scraping:
# from src.linkedin_jobs import buscar_vacantes_linkedin 
# from src.computrabajo import buscar_vacantes_computrabajo 

# Importa el resto de tus utilidades
from src.sheets_manager import aplanar_y_normalizar, conectar_sheets, preparar_hoja, actualizar_sheet, registrar_actualizacion 
from src.analizador_vacantes import analizar_vacante 
from src.config import PALABRAS_CLAVE
# --- Fin Importaciones ---


# Definición de las funciones de búsqueda activas
# Esta lista se usa para orquestar la concurrencia a nivel de portal
PORTALES_ACTIVOS = [
    ("GetOnBrd", buscar_vacantes_getonbrd),
    # ("LinkedIn", buscar_vacantes_linkedin),
    # ("Computrabajo", buscar_vacantes_computrabajo),
]


# --- 2. Funciones Lógicas ---

def recoleccion_de_vacantes():
    """
    Recolecta vacantes usando concurrencia anidada (por portal y por keyword) 
    para máxima velocidad.
    """
    resultados_raw = []
    
    # 1. Crear todas las tareas (combinaciones de portal + keyword)
    tareas_con_keywords = []
    for portal_nombre, portal_func in PORTALES_ACTIVOS:
        for keyword in PALABRAS_CLAVE:
            # Tarea: (Nombre, Función, Keyword)
            tareas_con_keywords.append((portal_nombre, portal_func, keyword))

    print(f"-> Iniciando {len(tareas_con_keywords)} búsquedas en paralelo...")
    
    # 2. Ejecución Concurrente con ThreadPoolExecutor
    # 10 workers es un buen número inicial para tareas limitadas por I/O
    with ThreadPoolExecutor(max_workers=10) as executor:
        
        # Mapea las tareas al executor, pasando la keyword como argumento
        future_to_task = {
            executor.submit(portal_func, keyword): (portal_nombre, keyword)
            for portal_nombre, portal_func, keyword in tareas_con_keywords
        }
        
        # 3. Recolección de resultados a medida que terminan
        for future in as_completed(future_to_task):
            portal_nombre, keyword = future_to_task[future]
            
            try:
                vacantes_encontradas = future.result()
                if vacantes_encontradas:
                    resultados_raw.extend(vacantes_encontradas)
                    # print(f"✅ Búsqueda exitosa en {portal_nombre} para '{keyword}'.")
                
            except Exception as e:
                # Capturar errores sin detener el script
                print(f"⚠️ ERROR: Falló la búsqueda en {portal_nombre} para '{keyword}'. Razón: {e}")
                
    return resultados_raw

def procesar_vacantes(resultados_raw):
    """
    Normaliza, elimina duplicados (por URL) y realiza el análisis de las vacantes.
    """
    
    # 1. Normalización y Aplanamiento
    vacantes_normalizadas = aplanar_y_normalizar(resultados_raw)
    vacantes_unicas = {}
    vacantes_sin_url = []
    
    # 2. DEDUPLICACIÓN: Usar un diccionario para eliminar duplicados por URL

    vacantes_unicas = {}
    for vacante in vacantes_normalizadas:
        url = vacante.get("url")
        # Si la URL existe, se sobrescribe con la versión más reciente (o simplemente se mantiene una)
        if url and url.strip(): # ✅ Si la URL existe, aplica deduplicación
            vacantes_unicas[url] = vacante
        else:
            # 💡 Almacenamos las vacantes sin URL para que no se pierdan
            vacantes_sin_url.append(vacante)
    
    vacantes_sin_duplicados = list(vacantes_unicas.values())
    print(f"✅ Vacantes ÚNICAS y normalizadas: {len(vacantes_sin_duplicados)}") 

    # 3. ANÁLISIS
    print("-> Iniciando Análisis de vacantes...")
    for i, v in enumerate(vacantes_sin_duplicados, 1):
        desc = v.get("descripcion", "")
        titulo = v.get("titulo", "Vacante sin título")
        
        try:
            if not desc:
                v["analisis"] = "Sin descripción disponible."
            else:
                v["analisis"] = analizar_vacante(desc)
            
        except Exception as e:
            v["analisis"] = f"Error en análisis: {e}"
            # print(f"⚠️ Error al analizar la vacante '{titulo}'.") # Comentar para no saturar la terminal
            
    return vacantes_sin_duplicados


# --- 3. Ejecución principal ---
if __name__ == "__main__":
    F_NAME = "vacantes_main.py"
    print(f"[{F_NAME}]: Iniciando proceso de búsqueda de vacantes...")

    # 1. Recolección de vacantes (¡En paralelo!)
    resultados_crudos = recoleccion_de_vacantes()
    print(f"\n✅ {len(resultados_crudos)} vacantes encontradas. Procesando...")
    
    # 2. Normalización, Deduplicación y Análisis
    vacantes_finales = procesar_vacantes(resultados_crudos)
    
    # 3. Guardado en Google Sheets 
    try:
        print("\n💾 Iniciando conexión y guardado en Google Sheets...")
        
        hoja = conectar_sheets()
        preparar_hoja(hoja)
        actualizar_sheet(hoja, vacantes_finales)
        registrar_actualizacion(hoja)
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO al interactuar con Google Sheets: {e}")
        
    print("\nProceso finalizado.")