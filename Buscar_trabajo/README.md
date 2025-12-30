# 🤖 Asesor de Búsqueda de Empleo con IA

Este proyecto revoluciona tu búsqueda de trabajo combinando **Web Scraping Masivo** con un **Evaluador IA de Élite**. No es solo un buscador; es un sistema que descarga vacantes, descarta la "basura" automáticamente, y te permite analizar a demanda las oportunidades que realmente te interesan.

## 🚀 Características Principales

### 1. 🕵️ El Recolector Veloz (`vacantes_main.py`)
*   **Multi-Plataforma**: Barre **LinkedIn** y **GetOnBrd** automáticamente.
*   **Filtro "Anti-Basura"**: Descarta vacantes que no coinciden con tus Keywords (Python, SQL, etc.) antes de que toquen tu Excel.
*   **Resultado**: Una base de datos limpia de oportunidades pendientes.

### 2. 🧠 El Asesor a Demanda (`chat_vacante.py`)
Tu centro de comando interactivo.

*   **📊 Análisis de Lista**: Lee tu Excel y te muestra las vacantes pendientes. Eliges una, y la IA la analiza a fondo (Fit Score, Carta, Tips).
*   **🌐 Escáner Universal de Links**: ¿Viste una oferta en **Indeed, Glassdoor, Trabajando.cl** o la web de una empresa?
    *   Copia el link.
    *   Pégalo en el Asesor (Opción `[L]`).
    *   ¡La IA leerá la página en vivo y te dará la estrategia ganadora!
*   **📡 Tracking de Postulaciones**:
    *   Al terminar de analizar, dile al Asesor si te postulaste (`[P]`) o la descartaste (`[D]`).
    *   El sistema actualizará tu Excel automáticamente ("Postulado" / "Rechazado").

---

## 🛠️ Requisitos

*   Python 3.9+
*   Cuenta de Google Cloud (API Sheets)
*   API Key de Gemini AI
*   Browser para scraping (Playwright)

## 📦 Instalación

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/ElGlitches/Scraping-IA.git
    cd Scraping-IA
    ```

2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    playwright install
    ```

3.  **Configuración**:
    *   Renombra `src/perfil.py.example` a `src/perfil.py` y pon tu Info.
    *   Crea `.env` con `GEMINI_API_KEY=tu_clave`.
    *   Pon `credentials.json` (Google Service Account) en la raíz.

## ▶️ Uso Diario

**Paso 1: Buscar Vacantes (Automático)**
```bash
python3 vacantes_main.py
```
*(Llena tu Excel con vacantes nuevas)*

**Paso 2: Analizar y Postular (Interactivo)**
```bash
python3 chat_vacante.py
```
*(Analiza vacantes de la lista O pega links externos)*

## 📂 Estructura

*   `vacantes_main.py`: Scraper y Filtro Rápido.
*   `chat_vacante.py`: Interfaz de Usuario (Terminal).
*   `recomendaciones/`: Estrategias generadas (.md).
*   `src/`: Lógica interna (Scrapers, AI, Sheets).

## 🛡️ Privacidad

Tus datos personales sensibles (CV) y credenciales están protegidos por `.gitignore` y nunca se suben al repositorio.
