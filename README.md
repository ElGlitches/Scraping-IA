# 🤖 Asesor de Búsqueda de Empleo con IA

Este proyecto revoluciona tu búsqueda de trabajo combinando **Web Scraping Masivo** con un **Evaluador IA de Élite**. No es solo un buscador; es un sistema que descarga vacantes, descarta la "basura" automáticamente, y te permite analizar a demanda las oportunidades que realmente te interesan.

## 🚀 Cómo Funciona (Workflow Híbrido)

El sistema se divide en dos fases para máxima velocidad y eficiencia:

### 1. 🕵️ El Recolector Veloz (`vacantes_main.py`)
*   **Qué hace**: Navega por **LinkedIn** y **GetOnBrd**.
*   **Filtro "Anti-Basura"**: Usa un algoritmo de *Keyword Scoring* (sin IA costo) para validar si la vacante tiene tus tecnologías clave (Python, AWS, ETL, etc.).
    *   ✅ Si tiene coincidencias -> La guarda en Excel con estado "Pendiente".
    *   🗑️ Si NO tiene ninguna -> La descarta y no ensucia tu base de datos.
*   **Resultado**: Una hoja de Excel limpia, con salarios detectados y ubicaciones normalizadas.

### 2. 🧠 El Asesor a Demanda (`chat_vacante.py`)
*   **Qué hace**: Lee tu Excel y busca las vacantes "Pendientes".
*   **Análisis Profundo**: Tú eliges qué vacante estudiar. La IA (Gemini):
    *   Lee la descripción completa.
    *   Calcula tu **Fit Score** real.
    *   Genera una carta de presentación y tips de entrevista.
*   **Chat Interactivo**: Se abre un chat donde puedes preguntarle: *"¿Qué me van a preguntar en la entrevista?"* o *"Mejora este párrafo de la carta"*.

---

## 🛠️ Requisitos

*   Python 3.9+
*   Cuenta de Google Cloud (API Sheets)
*   API Key de Gemini AI

## 📦 Instalación

1.  **Clonar el repositorio y entrar**:
    ```bash
    git clone <tu-repo>
    cd Buscar_trabajo
    ```
2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    playwright install
    ```
3.  **Configuración**:
    *   `credentials.json`: Tus credenciales de Google Service Account.
    *   `.env`: Tu clave `GEMINI_API_KEY`.
    *   `src/config.py`: Aquí defines tus `PALABRAS_CLAVE` (Skills) para el filtro rápido.

## ▶️ Uso Diario

**Paso 1: Buscar Vacantes**
```bash
python3 vacantes_main.py
```
*(Verás cómo navega y filtra vacantes irrelevantes en segundos)*

**Paso 2: Analizar y Postular**
```bash
python3 chat_vacante.py
```
*(Selecciona una vacante de la lista para activar al Asesor)*

## 📂 Estructura

*   `vacantes_main.py`: Scraper y Filtro Rápido.
*   `chat_vacante.py`: Interfaz de Análisis IA interactivo.
*   `recomendaciones/`: Carpeta donde se guardan los análisis detallados (.md).
*   `src/`: Módulos de lógica (LinkedIn, Sheets, AI).

## 🛡️ Privacidad

Tus datos personales sensibles (CV) se cargan desde `src/config.py` o PDF local y **nunca** se suben al repositorio (protegido por `.gitignore`).
