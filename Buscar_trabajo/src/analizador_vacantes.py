from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type
)
from google import genai
from google.genai.errors import APIError # Para capturar errores 
from dotenv import load_dotenv # Para cargar la clave API desde .env
import os 
import time

# ⚠️ CARGA EXPLÍCITA DEL ARCHIVO .env
load_dotenv() 

# Inicializa el cliente de Gemini. Lee la clave API del entorno.
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) 

# -------------------------------------------------------------
# 🤖 LÓGICA DE REINTENTO Y LLAMADA A LA API
# -------------------------------------------------------------

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60), 
    stop=stop_after_attempt(5), 
    # Reintentar SOLO si ocurre un error de API (Rate Limit, etc.)
    retry=(retry_if_exception_type(APIError)) 
)
def analizar_vacante(desc: str) -> str:
    """
    Analiza una descripción de vacante usando la API de Gemini.
    Incluye lógica de reintento con espera gradual.
    """
    
    # 1. Validación de Entrada
    if not desc or len(desc) < 20:
        return "Descripción demasiado corta para analizar."

    # 1. Ingeniería de Prompt y Definición de Tarea
    prompt = (
        "Eres un analista de datos experto en mercado laboral. Tu tarea es leer "
        "la siguiente vacante y estructurar todos los datos relevantes en el formato JSON proporcionado. "
        "Si un campo no se encuentra, usa 'No Determinado'."
        
        f"\n\nTÍTULO DE LA VACANTE: {titulo}"
        f"\n\nDESCRIPCIÓN COMPLETA: {desc}"
    )
    
    # 2. Definición del Esquema JSON (Schema)
    # ¡IMPORTANTE! Este esquema debe coincidir con TUS ENCABEZADOS de Sheets (A:M)
    schema = {
        "type": "object",
        "properties": {
            "empresa": {"type": "string", "description": "Nombre de la empresa."},
            "ubicacion": {"type": "string", "description": "Ciudad, País o 'Remoto'."},
            "modalidad": {"type": "string", "description": "Ej: 'Remoto', 'Híbrido', 'Presencial'."},
            "nivel": {"type": "string", "description": "Ej: 'Junior', 'Mid', 'Senior', 'Lead'."},
            "jornada": {"type": "string", "description": "Ej: 'Full-time', 'Part-time'."},
            "salario": {"type": "string", "description": "Rango salarial estimado (ej: $2000 - $3000) o 'No informado'."},
            "seniority_score": {"type": "integer", "description": "Puntuación de 1 a 100 de adecuación al perfil de automatización/backend."},
            "top_skills": {"type": "array", "items": {"type": "string"}, "description": "Lista de 3 requisitos técnicos clave."},
        },
        "required": ["empresa", "ubicacion", "nivel", "salario", "top_skills"]
    }

    # 3. Llamada a la API de Gemini (Usando JSON Schema)
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=[prompt],
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema # Pasamos el esquema para una salida estricta
        )
    )
    
    # 4. Devolver resultado
    return response.text

