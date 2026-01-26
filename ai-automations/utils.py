from datetime import datetime
from pypdf import PdfReader
from .config import PALABRAS_CLAVE, PALABRAS_EXCLUIDAS

def es_vacante_valida(titulo, descripcion):
    """
    Filtra vacantes basándose en palabras excluidas y palabras clave requeridas.
    """
    if not titulo:
        return False
        
    titulo = titulo.upper()
    descripcion = (descripcion or "").upper()

    # 1. FILTRO DE EXCLUSIÓN (Muerte Súbita)
    # Si tiene ALGUNA palabra prohibida en el TÍTULO, chao.
    for palabra in PALABRAS_EXCLUIDAS:
        if palabra.upper() in titulo:
            return False

    # 2. FILTRO DE INCLUSIÓN
    # Debe tener al menos UNA palabra clave en el TÍTULO o TRES en la DESCRIPCIÓN
    # (Nota: El usuario pidió 3 en descripción en el prompt, pero en el código de ejemplo puso >= 2. Usaré >= 2 para ser consistente con su código)
    tiene_match_titulo = any(p.upper() in titulo for p in PALABRAS_CLAVE)
    
    # Contar cuántas keywords aparecen en la descripción
    matches_descripcion = sum(1 for p in PALABRAS_CLAVE if p.upper() in descripcion)

    if tiene_match_titulo or matches_descripcion >= 2:
        return True
    
    return False


def cargar_texto_pdf(ruta_pdf: str) -> str:
    """
    Lee el texto de un archivo PDF.
    Retorna el texto extraído o una cadena vacía si hay error.
    """
    try:
        reader = PdfReader(ruta_pdf)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() + "\n"
        return texto.strip()
    except Exception as e:
        print(f"⚠️ Error al leer PDF ({ruta_pdf}): {e}")
        return ""

def fecha_actual():
    """Devuelve la fecha actual en formato YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")

def normalizar_texto(texto):
    """Limpia texto de None o espacios extra"""
    if not texto:
        return ""
    return str(texto).strip()

def calc_prioridad(modalidad):
    """Asigna prioridad según modalidad u otras reglas"""
    
    # 💡 CORRECCIÓN: Convierte el valor a cadena antes de usar .lower()
    # Además, si es booleano, nos basaremos en el valor True/False directamente.
    
    if modalidad is True: # Si recibimos el booleano True (es remoto)
        return "Alta"
    if modalidad is False: # Si recibimos el booleano False (no es remoto)
        return "Baja"
        
    # Si es una cadena (comportamiento original, ej: "remoto", "híbrido")
    modalidad_str = str(modalidad or "").lower()
    
    if "remoto" in modalidad_str:
        return "Alta"
    elif "híbrido" in modalidad_str:
        return "Media"
    return "Baja"

def clean_json_response(text: str) -> str:
    """
    Limpia la respuesta de la IA para extraer solo el JSON válido.
    Elimina bloques de código markdown (```json ... ```).
    """
    if not text:
        return ""
    
    # Eliminar envoltorios de markdown
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
        
    return cleaned.strip()