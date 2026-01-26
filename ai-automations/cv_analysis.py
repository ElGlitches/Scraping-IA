import os
import pypdf
from typing import List
from google import genai
from dotenv import load_dotenv

import hashlib
import json
from .utils import clean_json_response

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "cv_cache.json")

load_dotenv()

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae texto plano de un archivo PDF."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"No se encontró el archivo: {pdf_path}")
    
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error leyendo PDF: {e}")
        return ""

def analyze_cv_keywords(cv_text: str) -> List[str]:
    """
    Analiza el texto del CV usando Gemini y devuelve una lista de keywords optimizadas para búsqueda.
    """
    if not cv_text or len(cv_text) < 50:
        return []

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = (
        "Eres un experto tech recruiter. Analiza el siguiente CV y extrae una lista de 20 palabras clave ESTRATÉGICAS "
        "para buscar ofertas de trabajo.\n\n"
        "ESTRATEGIA DE BÚSQUEDA Y SENIORITY:\n"
        "1. DETECTA EL SENIORITY: Si el candidato es Senior/Lead, AGREGA 'Senior' o 'Lead' a los títulos de cargo (ej: 'Senior Data Engineer', 'Python Senior').\n"
        "2. FILTRO DE ROLES: Si el candidato es Desarrollador, NO incluyas keywords de QA, Testing o Soporte salvo que lo haga explícito.\n"
        "3. Mezcla Títulos (con Seniority) y Tecnologías avanzadas.\n"
        "4. Si es Junior, busca términos como 'Junior', 'Trainee'. Si es Senior, EVITA estos términos.\n"
        "5. Incluye variaciones en Inglés y Español.\n\n"
        "Devuelve SOLO un array JSON de strings. Ejemplo: [\"Senior Python Developer\", \"Tech Lead\", \"Data Engineer Senior\", \"AWS Architect\"]\n\n"
        f"CV TEXT:\n{cv_text[:10000]}"
    )

    try:
        # Intentar con el modelo potente primero
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[prompt],
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                print("⚠️ Quota excedida en Gemini 2.0. Cambiando a modelo de respaldo (Lite)...")
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=[prompt],
                    config=genai.types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
            else:
                raise e # Si es otro error, re-lanzarlo
        
        import json
        cleaned_json = clean_json_response(response.text)
        keywords = json.loads(cleaned_json)
        
        if isinstance(keywords, list):
            # Limpieza extra: Capitalize y eliminar duplicados
            return list(set([k.strip() for k in keywords if isinstance(k, str)]))
        return []

    except Exception as e:
        print(f"❌ Error analizando CV con IA: {e}")
        return []

def get_file_hash(filepath: str) -> str:
    """Calcula el hash MD5 de un archivo para detectar cambios."""
    if not os.path.exists(filepath):
        return ""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_keyword_cache(current_hash: str) -> List[str]:
    """Carga keywords desde cache si el hash coincide."""
    if not os.path.exists(CACHE_FILE):
        return []
    
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("file_hash") == current_hash:
                return data.get("keywords", [])
    except Exception as e:
        print(f"⚠️ Error leyendo cache: {e}")
    return []

def save_keyword_cache(keywords: List[str], current_hash: str):
    """Guarda las keywords y el hash actual en cache."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "file_hash": current_hash,
                "keywords": keywords,
                "cached_at":  str(os.path.getmtime(CACHE_FILE) if os.path.exists(CACHE_FILE) else "")
            }, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error guardando cache: {e}")

