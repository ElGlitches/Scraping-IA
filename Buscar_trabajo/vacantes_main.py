# vacantes_main.py

# --- 1. Importaciones ---
import os
import sys
import json # NECESARIO para parsear la salida JSON de Gemini
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# Asegura que Python encuentre los módulos en la carpeta 'src'
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importa las funciones de los módulos
from src.getonbrd import buscar_vacantes_getonbrd
# from src.linkedin_jobs import buscar_vacantes_linkedin
# from src.computrabajo import buscar_vacantes_computrabajo

# Importa el resto de tus utilidades
from src.sheets_manager import aplanar_y_normalizar, conectar_sheets, preparar_hoja, actualizar_sheet, registrar_actualizacion
from src.analizador_vacantes import analizar_vacante
from src.config import PALABRAS_CLAVE


# Definición de las funciones de búsqueda activas
PORTALES_ACTIVOS = [
    ("GetOnBrd", buscar_vacantes_getonbrd),
    # ("LinkedIn", buscar_vacantes_linkedin),
    # ("Computrabajo", buscar_vacantes_computrabajo),
]


# --- 2. Funciones Lógicas ---

def recoleccion_de_vacantes() -> List[Dict[str, Any]]:
    """
    Recolecta vacantes usando concurrencia anidada (por portal y por keyword).
    """
    resultados_raw = []

    # 1. Crear todas las tareas (combinaciones de portal + keyword)
    tareas_con_keywords = []
    for portal_nombre, portal_func in PORTALES_ACTIVOS:
        for keyword in PALABRAS_CLAVE:
            # Tarea: (Nombre, Función, Keyword)
            tareas_con_keywords.append((portal_nombre, portal_func, keyword))

    print(f"-> Iniciando {len(tareas_con_keywords)} búsquedas en paralelo...")

    # 2. Ejecución Concurrente
    with ThreadPoolExecutor(max_workers=10) as executor:

        # ⚠️ CORRECCIÓN 1: Mapear la tarea al ejecutor. La clave es el objeto Future, el valor es (portal, keyword)
        future_to_task = {
            executor.submit(portal_func, keyword): (portal_nombre, keyword)
            for portal_nombre, portal_func, keyword in tareas_con_keywords
        }

        # 3. Recolección de resultados a medida que terminan
        for future in as_completed(future_to_task):
            portal_nombre, keyword = future_to_task[future] # ⚠️ CORRECCIÓN 2: Obtener el nombre de la tarea

            try:
                # El resultado aquí es la lista de vacantes devuelta por el scraper
                vacantes_encontradas = future.result()
                if vacantes_encontradas:
                    resultados_raw.extend(vacantes_encontradas)
                    # print(f"✅ Búsqueda exitosa en {portal_nombre} para '{keyword}'.")

            except Exception as e:
                # Capturar errores sin detener el script
                print(f"⚠️ ERROR: Falló la búsqueda en {portal_nombre} para '{keyword}'. Razón: {e}")

    return resultados_raw

def procesar_vacantes(resultados_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normaliza, aplica la deduplicación, y realiza el análisis CONCURRENTE (IA).
    """

    # 1. Normalización y Aplanamiento
    vacantes_normalizadas = aplanar_y_normalizar(resultados_raw)

    vacantes_unicas = {}
    vacantes_sin_url = []

    # 2. DEDUPLICACIÓN y FILTRADO
    for vacante in vacantes_normalizadas:
        url = vacante.get("url")
        if url and url.strip():
            vacantes_unicas[url] = vacante
        else:
            # Retener vacantes sin URL para depuración
            vacantes_sin_url.append(vacante)

    vacantes_finales = list(vacantes_unicas.values()) + vacantes_sin_url

    print(f"✅ Vacantes ÚNICAS y procesadas: {len(vacantes_finales)}")

    # --- 3. ANÁLISIS CONCURRENTE (IA) ---
    print("-> ANÁLISIS OMITIDO para ahorrar tokens. Datos listos para guardar.")

    # Este bloque debe activarse para el análisis de IA:
    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = {
            # ⚠️ PASAMOS DESCRIPCIÓN Y TÍTULO A LA IA
            executor.submit(analizar_vacante, v.get("descripcion", ""), v.get("titulo", "")): v
            for v in vacantes_finales
        }

        for future in as_completed(futures):
            vacante = futures[future]

            try:
                analisis_json_str = future.result()
                analisis_data = json.loads(analisis_json_str) # CONVERTIR JSON DE IA

                # ⚠️ CORRECCIÓN DE CAMPOS: Llenar el diccionario de la vacante con los datos extraídos por la IA
                vacante["empresa"] = analisis_data.get("empresa", vacante["empresa"])
                vacante["ubicacion"] = analisis_data.get("ubicacion", vacante["ubicacion"])
                vacante["modalidad"] = analisis_data.get("modalidad", vacante["modalidad"])
                vacante["nivel"] = analisis_data.get("nivel", vacante["nivel"])
                vacante["salario"] = analisis_data.get("salario", vacante["salario"])

                # Guardar el JSON completo para auditoría o campos extra
                vacante["analisis_json"] = analisis_json_str
    
            except Exception as e:
                vacante["analisis_json"] = f"ERROR API/Análisis: {e.__class__.__name__}"

    return vacantes_finales


# --- 4. Ejecución principal ---
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

        # Pasar la lista final de vacantes
        actualizar_sheet(hoja, vacantes_finales)
        registrar_actualizacion(hoja)

    except Exception as e:
        print(f"❌ ERROR CRÍTICO al interactuar con Google Sheets: {e}")

    print("\nProceso finalizado.")