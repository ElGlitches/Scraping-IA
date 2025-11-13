# --- 1. Importaciones ---
import os
import sys

# Agregamos la carpeta src al path para que Python encuentre los módulos
# Esto asegura que las importaciones de src funcionen correctamente
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importa tus funciones de scraping
from src.getonbrd import buscar_vacantes_getonbrd
from src.linkedin_jobs import buscar_vacantes_linkedin
from src.computrabajo import buscar_vacantes_computrabajo
from src.bne import buscar_vacantes_bne # Asumo el nombre de la función
from src.laborum import buscar_vacantes_laborum # Asumo el nombre de la función
from src.trabajando import buscar_vacantes_trabajando # Asumo el nombre de la función

# Importa el resto de tus utilidades
from src.sheets_manager import aplanar_y_normalizar # Asumo que esta es la función de normalización
from src.analizador_vacantes import analizar_vacante # Asumo que esta es la función de análisis
from concurrent.futures import ThreadPoolExecutor, as_completed
# --- Fin Importaciones ---


# Definición de las funciones de búsqueda y sus nombres
FUNCIONES_BUSQUEDA = [
    # (nombre_del_portal, funcion_de_busqueda)
    ("GetOnBrd", buscar_vacantes_getonbrd),
    ("LinkedIn", buscar_vacantes_linkedin),
    ("Computrabajo", buscar_vacantes_computrabajo),
    ("BNE", buscar_vacantes_bne),
    ("Laborum", buscar_vacantes_laborum),
    ("Trabajando", buscar_vacantes_trabajando),
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
    Normaliza el formato de los datos recolectados y realiza el análisis (placeholder).
    """
    
    # Normalización (Aplanar y Normalizar)
    vacantes_normalizadas = aplanar_y_normalizar(resultados_raw)
    print(f"✅ Vacantes normalizadas: {len(vacantes_normalizadas)}")

    # Análisis (Placeholder para la lógica de análisis)
    # Reemplazo el placeholder que tenías en tu script original por una estructura más limpia
    print("-> Iniciando Análisis de vacantes...")
    for i, v in enumerate(vacantes_normalizadas, 1):
        desc = v.get("descripcion", "")
        titulo = v.get("titulo", "Vacante sin título")
        
        try:
            if not desc:
                v["analisis"] = "Sin descripción disponible."
            else:
                # La función analizar_vacante debe existir en src/analizador_vacantes.py
                v["analisis"] = analizar_vacante(desc)
            
            # Puedes añadir aquí tu lógica de impresión de avance
            # print(f"Analizada {i}/{len(vacantes_normalizadas)}") 
            
        except Exception as e:
            v["analisis"] = f"Error en análisis: {e}"
            print(f"⚠️ Error al analizar la vacante '{titulo}'.")
            
    return vacantes_normalizadas


# --- 3. Ejecución principal ---
if __name__ == "__main__":
    F_NAME = "vacantes_main.py"
    print(f"[{F_NAME}]: Iniciando proceso de búsqueda de vacantes...")

    # 1. Recolección de vacantes
    resultados_crudos = recoleccion_de_vacantes()
    print(f"\n✅ {len(resultados_crudos)} vacantes encontradas. Procesando...")
    
    # 2. Normalización y Análisis
    vacantes_finales = procesar_vacantes(resultados_crudos)
    
    # Aquí iría el paso final:
    # 3. Guardado en hojas de cálculo (si tienes la función de sheets_manager para guardar)
    # sheets_manager.guardar_datos(vacantes_finales)
    
    print("\nProceso finalizado.")