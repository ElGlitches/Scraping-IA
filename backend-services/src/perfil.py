from .utils import cargar_texto_pdf
from .config import RUTA_CV

_CACHE_PERFIL = None

def cargar_perfil() -> str:
    """
    Carga el texto del CV desde el archivo PDF definido en config.
    Usa un cache simple para no releer el archivo si ya está en memoria.
    """
    global _CACHE_PERFIL
    if _CACHE_PERFIL:
        return _CACHE_PERFIL
    
    try:
        texto = cargar_texto_pdf(RUTA_CV)
        if not texto:
            print(f"⚠️  Advertencia: El CV en {RUTA_CV} parece estar vacío o no se pudo leer.")
            return "Información de candidato no disponible."
        
        _CACHE_PERFIL = texto
        return texto
    except Exception as e:
        print(f"❌ Error crítico leyendo CV ({RUTA_CV}): {e}")
        return "Error leyendo CV."

def get_candidate_prompt() -> str:
    """
    Devuelve un bloque de texto formateado con la información del candidato,
    listo para insertar en un prompt de LLM.
    """
    cv_text = cargar_perfil()
    return (
        f"--- PERFIL DEL CANDIDATO (CV) ---\n"
        f"{cv_text}\n"
        f"---------------------------------\n"
    )
