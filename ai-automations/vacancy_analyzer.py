"""
Script: Vacancy_AI_Analyzer.py
Purpose: GenAI-powered analysis of job descriptions to determine candidate fit.
Author: Iván Durán
"""
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type
)
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv
import os 
import time
from .utils import clean_json_response
from .perfil import get_candidate_prompt

load_dotenv() 

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) 

# Cache logic removed in favor of src.perfil

@retry(
    wait=wait_exponential(multiplier=2, min=10, max=120), 
    stop=stop_after_attempt(8), 
    retry=(retry_if_exception_type(APIError)),
    before_sleep=lambda retry_state: print(f"⏳ API saturada. Esperando para reintentar (Intento {retry_state.attempt_number})...")
)
def analizar_vacante(desc: str, titulo:str) -> str:
    """
    Analiza una descripción de vacante usando la API de Gemini.
    Incluye lógica de reintento con espera gradual.
    """
    print(f"DEBUG: Analizando vacante '{titulo}' (v2)...")
    time.sleep(5) # Rate limit check
    
    import json
    if not desc or len(desc) < 20:
        return json.dumps({
            "error": "Descripción demasiado corta/vacía", 
            "match_percent": 0, 
            "match_reason": "Sin datos",
            "top_skills": [],
            "seniority_score": 0,
            "empresa": "Desconocida",
            "ubicacion": "Desconocida",
            "nivel": "N/A",
            "jornada": "N/A",
            "salario": "No informado"
        })

    perfil_prompt = get_candidate_prompt()

    prompt = (
        "Eres un Asesor de Carrera Senior, experto en reclutamiento IT y conocido por ser BRUTALMENTE HONESTO. "
        "Tu trabajo NO es dar falsas esperanzas, sino proteger el tiempo del candidato validando si REALMENTE tiene posibilidades.\n"
        
        f"\n{perfil_prompt}\n"
        
        f"\nVACANTE A ANALIZAR:\n"
        f"TÍTULO: {titulo}\n"
        f"DESCRIPCIÓN: {desc}\n"
        
        "\nINSTRUCCIONES CRÍTICAS:"
        "\n1. IDENTIFICACIÓN: Extrae el NOMBRE REAL DE LA EMPRESA y el TÍTULO DEL CARGO directo de la descripción si 'TITULO' arriba dice 'Cargo Manual' o similar."
        "\n2. Analiza los REQUISITOS EXCLUYENTES de la vacante. Si el candidato no los cumple (ej: pide 5 años y tiene 2, pide Inglés avanzado y no lo menciona o es básico, pide React y el candidato es puro Python), DESCÁRTALO INMEDIATAMENTE con un puntaje bajo."
        "\n3. Calcula 'match_percent' (0-100) con criterio ESTRICTO:"
        "\n   - 90-100: MATCH PERFECTO. Cumple TODOS los requisitos técnicos y años de experiencia. Es el candidato ideal."
        "\n   - 70-89: MATCH BUENO. Cumple lo principal (Lenguaje + Stack core), le falta quizás 1 herramienta menor o un poco de tiempo, pero es defendible."
        "\n   - 40-69: ARRIESGADO. Le faltan requisitos importantes (ej: otro cloud provider, falta framework clave). Solo si la vacante es flexible."
        "\n   - 0-39: NO TIRES TU TIEMPO. Stack diferente, seniority muy lejano, idioma faltante, o rol equivocado (ej: Fullstack vs Data Engineer)."
        "\n3. Genera 'match_reason' (DIRECTO Y AL GRANO, max 15 palabras). Ejemplos:"
        "\n   - 'Piden 5 años Java, eres Python Jr.'"
        "\n   - 'Falta Inglés conversacional fluido.'"
        "\n   - 'Stack %100 compatible. Aplica YA.'"
        "\n   - 'Es rol DevOps, tú eres Data.'"
        "\n4. Extrae los datos clave en JSON estricto."
    )
    
    schema = {
        "type": "object",
        "properties": {
            "titulo_vacante": {"type": "string", "description": "El título oficial del cargo extraído del texto (ej: 'Ingeniero de Sistemas')."},
            "empresa": {"type": "string", "description": "Nombre de la empresa."},
            "ubicacion": {"type": "string", "description": "Ciudad, País o 'Remoto'."},
            "modalidad": {"type": "string", "description": "Ej: 'Remoto', 'Híbrido', 'Presencial'."},
            "nivel": {"type": "string", "description": "Ej: 'Junior', 'Mid', 'Senior', 'Lead'."},
            "jornada": {"type": "string", "description": "Ej: 'Full-time', 'Part-time'."},
            "salario": {"type": "string", "description": "Rango salarial estimado (ej: $2000 - $3000) o 'No informado'."},
            "seniority_score": {"type": "integer", "description": "Puntuación de 1 a 100 de adecuación al perfil de automatización/backend."},
            "top_skills": {"type": "array", "items": {"type": "string"}, "description": "Lista de 3 requisitos técnicos clave."},
            "match_percent": {"type": "integer", "description": "Porcentaje de coincidencia (0-100) con el perfil del usuario."},
            "match_reason": {"type": "string", "description": "Explicación muy breve del match (ej: 'Falta experiencia en AWS')."},
        },
        "required": ["titulo_vacante", "empresa", "ubicacion", "nivel", "salario", "top_skills", "match_percent", "match_reason"]
    }

    # Eliminado try-except manual para permitir que Tenacity maneje los reintentos
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp", 
        contents=[prompt],
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema
        )
    )
    
    import json
    cleaned = clean_json_response(response.text)
    
    try:
        json.loads(cleaned) # Validar
        print(f"DEBUG: Returning cleaned JSON: {cleaned[:50]}...")
        return cleaned
    except Exception as e:
        print(f"❌ Error parseando JSON de Gemini. Respuesta cruda: {response.text[:200]}...")
        return json.dumps({
            "error": f"JSON Error: {str(e)}", 
            "match_percent": 0, 
            "match_reason": "Error Análisis",
            "top_skills": [],
            "seniority_score": 0,
            "empresa": "Error",
            "ubicacion": "Error",
            "nivel": "Error",
            "jornada": "Error",
            "salario": "Error"
        })

