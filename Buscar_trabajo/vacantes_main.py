# --- 1. Importaciones ---
import os
import sys

# Agregamos la carpeta src al path para que Python encuentre los módulos
# Esto asegura que las importaciones de src funcionen correctamente
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importa tus funciones de scraping
from src.getonbrd import buscar_vacantes_getonbrd
# from src.linkedin_jobs import buscar_vacantes_linkedin
# from src.computrabajo import buscar_vacantes_computrabajo
# from src.bne import buscar_vacantes_bne # Asumo el nombre de la función
# from src.laborum import buscar_vacantes_laborum # Asumo el nombre de la función
# from src.trabajando import buscar_vacantes_trabajando # Asumo el nombre de la función

# Importa el resto de tus utilidades
from src.sheets_manager import aplanar_y_normalizar, conectar_sheets, preparar_hoja, actualizar_sheet, registrar_actualizacion 
from src.analizador_vacantes import analizar_vacante 
from concurrent.futures import ThreadPoolExecutor, as_completed
# --- Fin Importaciones ---


# Definición de las funciones de búsqueda y sus nombres
FUNCIONES_BUSQUEDA = [
    # (nombre_del_portal, funcion_de_busqueda)
    ("GetOnBrd", buscar_vacantes_getonbrd),
    # ("LinkedIn", buscar_vacantes_linkedin),
    # ("Computrabajo", buscar_vacantes_computrabajo),
    # ("BNE", buscar_vacantes_bne),
    # ("Laborum", buscar_vacantes_laborum),
    # ("Trabajando", buscar_vacantes_trabajando),
]

# --- 2. Funciones Lógicas ---
def recoleccion_de_vacantes():
    """
    Recolecta vacantes de todas las fuentes definidas en FUNCIONES_BUSQUEDA
    de manera CONCURRENTE (en paralelo) usando hilos.
    """
    resultados_raw = []
    
    # max_workers = 6: Ejecuta hasta 6 búsquedas de red simultáneamente (una por portal)
    with ThreadPoolExecutor(max_workers=len(FUNCIONES_BUSQUEDA)) as executor:
        # 1. Crear un diccionario de "futuros" (tareas en ejecución)
        future_to_portal = {
            executor.submit(func): nombre
            for nombre, func in FUNCIONES_BUSQUEDA
        }
        
        print("-> Iniciando búsquedas en paralelo...")
        
        # 2. Recolectar resultados a medida que terminan
        for future in as_completed(future_to_portal):
            portal_nombre = future_to_portal[future]
            
            try:
                # Obtener el resultado (lista de vacantes)
                vacantes_encontradas = future.result()
                resultados_raw.extend(vacantes_encontradas)
                print(f"✅ Búsqueda exitosa en {portal_nombre}.")
                
            except Exception as e:
                # Capturar errores sin detener el resto del script
                print(f"⚠️ ERROR: Falló la búsqueda en {portal_nombre}. Razón: {e}")
                
    return resultados_raw

def procesar_vacantes(resultados_raw):
    """
    Normaliza el formato de los datos recolectados, ELIMINA DUPLICADOS 
    y realiza el análisis.
    """
    # 1. Normalización y Aplanamiento
    vacantes_normalizadas = aplanar_y_normalizar(resultados_raw)
    
    # 2. DEDUPLICACIÓN: Usar un diccionario para eliminar duplicados por URL
    vacantes_unicas = {}
    for vacante in vacantes_normalizadas:
        url = vacante.get("url")
        # Usamos la URL como clave. Si ya existe, se sobrescribe.
        if url: 
            vacantes_unicas[url] = vacante
    
    # Convierte el diccionario de vuelta a una lista de vacantes
    vacantes_sin_duplicados = list(vacantes_unicas.values())
    
    print(f"✅ Vacantes ÚNICAS y normalizadas: {len(vacantes_sin_duplicados)}") 

    # 3. ANÁLISIS: Ahora iteramos sobre la lista sin duplicados
    print("-> Iniciando Análisis de vacantes...")
    for i, v in enumerate(vacantes_sin_duplicados, 1):
        desc = v.get("descripcion", "")
        titulo = v.get("titulo", "Vacante sin título")
        
        try:
            if not desc:
                v["analisis"] = "Sin descripción disponible."
            else:
                # La función analizar_vacante debe existir en src/analizador_vacantes.py
                v["analisis"] = analizar_vacante(desc)
            
        except Exception as e:
            v["analisis"] = f"Error en análisis: {e}"
            print(f"⚠️ Error al analizar la vacante '{titulo}'.")
            
    # 4. DEVOLVER la lista limpia y analizada
    return vacantes_sin_duplicados

# --- 3. Ejecución principal ---
if __name__ == "__main__":
    F_NAME = "vacantes_main.py"
    print(f"[{F_NAME}]: Iniciando proceso de búsqueda de vacantes...")

    # 1. Recolección de vacantes
    resultados_crudos = recoleccion_de_vacantes()
    print(f"\n✅ {len(resultados_crudos)} vacantes encontradas. Procesando...")
    
    # 2. Normalización y Análisis
    vacantes_finales = procesar_vacantes(resultados_crudos)
    
 # 3. Guardado en Google Sheets 
    try:
        # Asegúrate de importar estas funciones desde src.sheets_manager
        from src.sheets_manager import conectar_sheets, preparar_hoja, actualizar_sheet, registrar_actualizacion
        
        print("\n💾 Iniciando conexión y guardado en Google Sheets...")
        
        # Conectar (obtiene la hoja de trabajo)
        hoja = conectar_sheets()
        
        # Preparar estructura (encabezados, filtros)
        preparar_hoja(hoja)
        
        # Actualizar hoja con las vacantes
        actualizar_sheet(hoja, vacantes_finales)
        
        # Registrar la hora de finalización
        registrar_actualizacion(hoja)
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO al interactuar con Google Sheets: {e}")
        
    print("\nProceso finalizado.")
