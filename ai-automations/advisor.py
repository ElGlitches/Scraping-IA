import os
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .utils import clean_json_response
from .perfil import get_candidate_prompt
from .upload_helper import enviar_mensaje_multimodal

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))




@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(3),
    retry=(retry_if_exception_type(APIError))
)
def generar_pack_postulacion(vacante: dict) -> str:
    """
    Genera un pack de postulación (Carta, Entrevista, Tips) para una vacante
    usando el CV del usuario.
    Retorna un string con formato Markdown.
    """
    titulo = vacante.get("titulo", "Puesto IT")
    empresa = vacante.get("empresa", "Empresa Confidencial")
    desc = vacante.get("descripcion", "")
    url = vacante.get("url", "No especificada")
    url = vacante.get("url", "No especificada")
    
    perfil_prompt = get_candidate_prompt()

    prompt = (
        f"Actúa como mi Headhunter Personal de Élite. No quiero consejos genéricos de chatbot. Quiero estrategia pura para ganar este puesto.\n\n"
        f"--- DATOS DE LA VACANTE ---\n"
        f"Empresa: {empresa}\n"
        f"Rol: {titulo}\n"
        f"Link: {url}\n"
        f"Descripción: {desc}\n\n"
        f"{perfil_prompt}\n"
        f"--- MENTALIDAD ---\n"
        f"Analiza esto como si tuvieras 'insider info'. Busca qué es lo que REALMENTE le duele a esta empresa (escalabilidad, deuda técnica, falta de liderazgo) basándote en la descripción.\n\n"
        f"--- ENTREGABLES ---\n"
        f"Genera un documento Markdown estratégico:\n\n"
        f"# [{titulo} en {empresa}]({url})\n\n"
        f"## 1. Diagnóstico Estratégico (The Hook)\n"
        f"- 🎯 **¿Qué les duele?**: Identifica el problema real (no lo obvio).\n"
        f"- 🔑 **Mi Llave Maestra**: ¿Qué experiencia exacta de mi CV resuelve ese dolor? (Cita proyectos míos específicos).\n"
        f"- ⚠️ **Red Flag / Gap**: ¿Qué excusa usarán para descartarme y cómo la desarmamos antes de la entrevista?\n\n"
        f"## 2. Cold Email de Alto Impacto (Para el Hiring Manager)\n"
        f"- Asunto: Corto, relevante y no clickbait.\n"
        f"- Cuerpo: 3 párrafos cortos. Párrafo 1: Contexto (vi tu búsqueda). Párrafo 2: Prueba social/Técnica (hice X, Y, Z). Párrafo 3: Call to Action (CTA) suave.\n"
        f"- Tono: Profesional pero conversacional, senior.\n\n"
        f"## 3. Preparación de Entrevista (Modo Hardcore)\n"
        f"- ❓ **Pregunta Trampa**: Esa pregunta difícil que seguro harán.\n"
        f"- ⭐ **Respuesta Ganadora**: Cómo responderla usando la técnica STAR con mis datos.\n"
        f"- 🗣️ **Pregunta 'Reverse Uno'**: Una pregunta tan buena que yo deba hacerles a ellos para que digan 'wow'.\n\n"
        f"## 4. Estrategia Salarial y Dudas\n"
        f"- Basado en el seniority pedido y skills, ¿tengo apalancamiento para negociar fuerte? (Sí/No y por qué).\n"
        f"- Sección interactiva: Pregúntame si hay algo ambiguo (ej: tech stack no claro) para que averigüemos antes de enviar.\n"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[prompt]
        )
        return response.text
    except Exception as e:
        return f"Error generando pack de postulación: {str(e)}"

def iniciar_chat(vacante: dict):
    """
    Inicia una sesión de chat interactiva con el Asesor usando el PROMPT PERSISTENTE v2.
    """
    try:
        titulo = vacante.get("Título", "Vacante")
        empresa = vacante.get("Empresa", "Confidencial")
        url = vacante.get("URL", "No especificada")
        descripcion = vacante.get("Descripción", "")
        
        perfil_candidato = get_candidate_prompt()

        # Construcción del Prompt MAESTRO solicitado por el usuario
        system_instruction = (
            f"Actúa como mi Asesor de Carrera IT Senior (Headhunter nivel Elite).\n"
            f"He adjuntado mi CV en formato PDF (cuyo contenido textual verás abajo). Úsalo como base de verdad absoluta para este análisis.\n\n"
            
            f"La vacante a analizar se encuentra en este enlace:\n"
            f"🔗 {url}\n\n"
            f"(Nota: Para asegurar que tengas todo el contexto, aquí está la DESCRIPCIÓN EXTRAÍDA del link):\n"
            f"'{titulo} en {empresa}'\n"
            f"{descripcion[:8000]}...\n\n" # Truncamos descripción si es gigante para no explotar tokens
            
            f"--- CONTENIDO DEL CV ADJUNTO ---\n"
            f"{perfil_candidato}\n"
            f"--------------------------------\n\n"

            f"INSTRUCCIONES DE ANÁLISIS (HONESTIDAD BRUTAL):\n\n"
            f"1. 🔍 FACT CHECK: Cruza los requisitos de la vacante (del link/texto) con mi CV. No asumas NADA. Si no está en el PDF, no lo tengo.\n\n"
            
            f"2. ⚖️ VEREDICTO (Primero):\n"
            f"   - 🟢 APLICA YA (>80% match).\n"
            f"   - 🟡 RIESGOSO (50-80%).\n"
            f"   - 🔴 NO APLIQUES (<50% match).\n\n"
            
            f"3. ⚠️ GAPS & ATS:\n"
            f"   - Dime qué 3 keywords de la vacante NO están en mi CV (Habilidades que el filtro ATS no encontrará).\n"
            f"   - Dime qué 'Killer Question' me harán en la primera entrevista que podría descartarme por lo que ves en mi CV.\n\n"
            
            f"4. 🧪 VALIDACIÓN TÉCNICA:\n"
            f"   - Générame una pregunta técnica muy difícil basada en el stack de la vacante para probar si realmente tengo el nivel Senior/Mid que piden.\n\n"
            
            f"Comienza con el VEREDICTO."
        )

        chat = client.chats.create(
            model="gemini-2.0-flash-exp",
            history=[
                genai.types.Content(
                    role="user",
                    parts=[genai.types.Part.from_text(text=system_instruction)]
                )
            ]
        )
        return chat
    except Exception as e:
        print(f"Error iniciando chat: {e}")
        return None
