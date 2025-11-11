# src/analizador_vacantes.py
from openai import OpenAI
from dotenv import load_dotenv
import os

# Cargar variables del archivo .env
load_dotenv()

# Inicializar el cliente con la API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "❌ No se encontró la clave OPENAI_API_KEY. "
        "Asegúrate de tener un archivo .env con la línea: OPENAI_API_KEY=tu_clave_aqui"
    )

client = OpenAI(api_key=api_key)


def generar_prompt_analisis(vacante_texto):
    """
    Genera un prompt detallado para analizar si una vacante encaja con el perfil profesional de Iván Durán.
    """

    prompt = f"""
Actúa como un asesor laboral y reclutador experto en perfiles tecnológicos.
Tu función es analizar la siguiente vacante y determinar qué tan bien encaja con el perfil profesional del candidato.

### Perfil del candidato:
- Nombre: Iván Durán Luengo
- Rol actual: Desarrollador Experto en Banco de Chile
- Experiencia total: 4 años en desarrollo backend, automatización de procesos e integración de sistemas.
- Áreas de experiencia: Backend, ETL, integración, automatización, infraestructura cloud y manejo de datos en entornos financieros regulados.
- Tecnologías: Python, SQL, IBM DataStage, Control-M, AWS, GCP, Ansible, Bash, Docker, APIs REST, Node.js, React, PostgreSQL, Git.
- Metodologías: Scrum, CI/CD, Jira, Confluence, Bamboo.
- Formación: Analista Programador (Duoc UC).
- Certificaciones: Google Cloud Computing Foundations (en curso), DevOps Engineer Path, Python con Django, JavaScript con Node.js.
- Logros: Automatización de procesos bancarios reduciendo tiempos de ejecución en un 40%, estabilización de flujos ETL críticos y mejora de tiempos de respuesta ante incidencias.
- Intereses: Roles relacionados con desarrollo backend, automatización, cloud o datos.
- Preferencias: Evitar COBOL o funciones centradas en soporte puro.

### Vacante a analizar:
{vacante_texto}

### Instrucciones:
Analiza la vacante y entrega tu respuesta estructurada en el siguiente formato:

📄 **Resumen de la vacante:**  
[Describe brevemente el cargo, empresa y funciones principales.]

🧩 **Compatibilidad con el perfil:** [porcentaje]%  
[Explica por qué asignas ese porcentaje considerando nivel técnico, experiencia, entorno y proyección.]

✅ **Puntos a favor:**  
- [Coincidencia 1]  
- [Coincidencia 2]  
- [Coincidencia 3]  

⚠️ **Puntos a mejorar o brechas:**  
- [Diferencia 1]  
- [Diferencia 2]  

💡 **Recomendación final:**  
Indica si recomendarías postular o no, justificando la decisión en base a encaje técnico, experiencia, cultura de la empresa y oportunidades de crecimiento profesional.
"""
    return prompt


def analizar_vacante(vacante_texto):
    """
    Envía el prompt al modelo y devuelve el análisis de compatibilidad.
    """
    prompt = generar_prompt_analisis(vacante_texto)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error al analizar la vacante: {e}"
