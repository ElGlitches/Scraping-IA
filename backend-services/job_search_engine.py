"""
Script: Job_Search_Engine_Enterprise.py
Purpose: Orchestrates multi-platform job scraping and AI-driven vacancy analysis.
Author: Iván Durán
"""
import os
import sys
import json
import traceback
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import questionary

# --- ENTERPRISE PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "infrastructure"))
sys.path.append(os.path.join(BASE_DIR, "data-engineering"))
sys.path.append(os.path.join(BASE_DIR, "ai-automations"))
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Infrastructure Imports
import ui
from config import PALABRAS_CLAVE, RUTA_CV
from utils import es_vacante_valida

# Data Engineering Imports
from sheets_manager import aplanar_y_normalizar, conectar_sheets, preparar_hoja, actualizar_sheet, registrar_actualizacion, obtener_urls_existentes

# AI Automation Imports
from vacancy_analyzer import analizar_vacante
from advisor import generar_pack_postulacion
from cv_analysis import extract_text_from_pdf, analyze_cv_keywords, get_file_hash, load_keyword_cache, save_keyword_cache

# Scraper Imports (Local Lib)
from getonbrd import buscar_vacantes_getonbrd
from linkedin_jobs import buscar_vacantes_linkedin


PORTALES_ACTIVOS = [
    ("GetOnBrd", buscar_vacantes_getonbrd),
    ("LinkedIn", buscar_vacantes_linkedin),
    # ("Computrabajo", buscar_vacantes_computrabajo),
]


def recoleccion_de_vacantes(keywords_custom: List[str] = None) -> List[Dict[str, Any]]:
    """
    Recolecta vacantes usando concurrencia anidada (por portal y por keyword).
    Si keywords_custom es None, usa las de config.
    """
    resultados_raw = []
    
    keywords_to_use = keywords_custom if keywords_custom else PALABRAS_CLAVE
    
    # Deduplicar y limpiar
    keywords_to_use = list(set([k.strip() for k in keywords_to_use if k and k.strip()]))

    tareas_con_keywords = []
    for portal_nombre, portal_func in PORTALES_ACTIVOS:
        for keyword in keywords_to_use:
            tareas_con_keywords.append((portal_nombre, portal_func, keyword))

    ui.console.print(f"🔍 SEARCHING IN {len(PORTALES_ACTIVOS)} PORTALS FOR {len(keywords_to_use)} KEYWORDS...")
    # ui.console.print(f"   [dim]Keywords: {', '.join(keywords_to_use)}[/dim]")

    with ui.status_context("SEARCHING WEB FOR VACANCIES") as status:
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_task = {
                executor.submit(portal_func, keyword): (portal_nombre, keyword)
                for portal_nombre, portal_func, keyword in tareas_con_keywords
            }

            for future in as_completed(future_to_task):
                portal_nombre, keyword = future_to_task[future]
                try:
                    vacantes_encontradas = future.result()
                    if vacantes_encontradas:
                        resultados_raw.extend(vacantes_encontradas)
                except Exception as e:
                    ui.console.print(f"❌ ERROR IN {portal_nombre} ('{keyword}'): {e}")

    return resultados_raw

def procesar_vacantes(resultados_raw: List[Dict[str, Any]], urls_existentes: set = set()) -> List[Dict[str, Any]]:
    """
    Normaliza, aplica la deduplicación, y realiza el análisis CONCURRENTE (IA).
    """
    
    
    with ui.status_context("PROCESSING AND NORMALIZING DATA"):
        vacantes_normalizadas = aplanar_y_normalizar(resultados_raw)

        vacantes_unicas = {}
        vacantes_sin_url = []
        vacantes_descartadas = 0

        # from src.utils import es_vacante_valida (Moved to top) 

        for vacante in vacantes_normalizadas:
            # 0. FILTRO PREVIO (Exclusión/Inclusión)
            if not es_vacante_valida(vacante.get("titulo"), vacante.get("descripcion")):
                vacantes_descartadas += 1
                continue

            url = vacante.get("url")
            if url and url.strip():
                vacantes_unicas[url] = vacante
            else:
                vacantes_sin_url.append(vacante)
            
    ui.console.print(f"🧹 [dim]Vacantes descartadas por filtro de palabras: {vacantes_descartadas}[/dim]")

    vacantes_finales = list(vacantes_unicas.values()) + vacantes_sin_url

    ui.console.print(f"📊 Vacantes ÚNICAS encontradas: [bold]{len(vacantes_finales)}[/bold]")

    vacantes_a_analizar = []
    for v in vacantes_finales:
        if v.get("url") not in urls_existentes:
            vacantes_a_analizar.append(v)
        else:
            pass
            
    nuevas_count = len(vacantes_a_analizar)
    repetidas_count = len(vacantes_finales) - nuevas_count
    
    ui.console.print(f"♻️  [dim]Ya existían en base de datos: {repetidas_count}[/dim]")
    
    if not vacantes_a_analizar:
        ui.console.print("⚠️ NO NEW VACANCIES TO ANALYZE.")
        return []
    
    ui.console.print(f"🆕 [bold green]Nuevas vacantes a analizar: {nuevas_count}[/bold green]")

    # --- NUEVA LÓGICA: FILTRADO RÁPIDO (SIN IA) ---
    ui.console.print("\n⚡ FILTERING BY RELEVANCE...")
    
    # Palabras clave extra para validar relevancia
    KEYWORDS_RELEVANTES = set([item.lower() for item in PALABRAS_CLAVE])
    
    vacantes_filtradas = []

    # Barra de progreso simple para el filtrado
    with ui.status_context("EVALUATING RELEVANCE"):
        for vacante in vacantes_a_analizar:
            texto_completo = (vacante.get("titulo", "") + " " + vacante.get("descripcion", "")).lower()
            
            # Scoring simple
            score = 0
            matches = []
            for kw in KEYWORDS_RELEVANTES:
                if kw in texto_completo:
                    score += 1
                    matches.append(kw)
            
            # Umbral: Al menos 1 palabra clave fuerte
            if score > 0:
                vacante["match_percent"] = "Pendiente" 
                vacante["match_reason"] = f"Keywords: {', '.join(matches[:3])}"
                vacante["seniority_estimado"] = "N/A"
                vacante["top_skills"] = ", ".join(matches)
                vacantes_filtradas.append(vacante)
            else:
                 # ui.console.print(f"[dim]🗑️ Descartando: {vacante.get('titulo')}[/dim]")
                 pass
    
    vacantes_a_analizar = vacantes_filtradas
    ui.console.print(f"✅ Vacantes relevantes tras filtro: [bold]{len(vacantes_a_analizar)}[/bold]")

    # --- FASE 2: GENERACIÓN DE PACK DE POSTULACIÓN (Asesor) ---
    if ui.confirmar_accion(f"GENERATE APPLICATION PACKS FOR {len(vacantes_a_analizar)} VACANCIES?"):
        ui.console.print("\n🧠 GENERATING STRATEGIES...")
        
        dir_recomendaciones = os.path.join(os.path.dirname(__file__), "recomendaciones")
        os.makedirs(dir_recomendaciones, exist_ok=True)

        count_generados = 0
        with ui.status_context("WRITING LETTERS AND ANALYZING"):
            for v in vacantes_a_analizar:
                # Aquí asumimos que si pasó el filtro de keywords es un candidato potencial,
                # pero idealmente tendríamos un score numérico real. 
                # Simulemos un score alto para procesar o usar lógica previa.
                # En el código original se usaba match_pct >= 70. 
                # Como 'match_percent' es "Pendiente", este bloque original podría fallar si comparamos strings.
                # Vamos a forzar el intento si pasó el filtro de keywords.
                
                empresa = v.get("empresa", "Empresa").replace("/", "-").strip()
                titulo = v.get("titulo", "Rol").replace("/", "-").strip()
                filename = f"{empresa}_{titulo}.md"
                filepath = os.path.join(dir_recomendaciones, filename)

                if not os.path.exists(filepath):
                    try:
                        pack_content = generar_pack_postulacion(v)
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(pack_content)
                        count_generados += 1
                    except Exception as e:
                        ui.console.print(f"⚠️ ERROR GENERATING PACK FOR {titulo}: {e}")
        
        ui.console.print(f"✨ Se generaron [bold]{count_generados}[/bold] nuevos packs de postulación.")

    return vacantes_a_analizar


def main():
    ui.mostrar_banner()

    while True:
        opcion = ui.menu_principal()

        if "Salir" in opcion:
            ui.console.print("GOODBYE! 👋")
            break

        elif "Buscar Vacantes" in opcion:
            # Lógica de búsqueda
            try:
                ui.console.print("\n[dim]Conectando a Google Sheets para obtener historial...[/dim]")
                hoja = conectar_sheets()
                preparar_hoja(hoja)
                urls_existentes = obtener_urls_existentes(hoja)
            except Exception as e:
                ui.console.print(f"ERROR CONNECTING TO SHEETS: {e}")
                urls_existentes = set()
                hoja = None

            resultados_crudos = []
            keywords_dinamicas = []

            # 1. Intentar obtener keywords del CV (con Cache Inteligente)
            # 1. Intentar obtener keywords del CV (con Cache Inteligente)
            if os.path.exists(RUTA_CV):
                ui.console.print(f"\n[dim]📄 Verificando CV en: {RUTA_CV}[/dim]")
                
                current_cv_hash = get_file_hash(RUTA_CV)
                cached_keywords = load_keyword_cache(current_cv_hash)
                
                if cached_keywords:
                    ui.console.print(f"⚡ [green]Usando keywords en cache (CV sin cambios):[/green] {', '.join(cached_keywords)}")
                    keywords_dinamicas = cached_keywords
                else:
                    ui.console.print(f"📄 [bold]Se detectó un CV nuevo o modificado.[/bold]")
                    if ui.confirmar_accion("¿Analizar CV con IA para generar keywords?"):
                        try:
                            # 1. Extracción Inicial
                            with ui.status_context("ANALYZING CV WITH AI"):
                                cv_text = extract_text_from_pdf(RUTA_CV)
                                keywords_dinamicas = analyze_cv_keywords(cv_text)
                            
                            if keywords_dinamicas:
                                # 2. Loop de Validación (Solo se ejecuta una vez por versión de CV)
                                while True:
                                    ui.console.print("\n📋 [bold]KEYWORDS SUGERIDAS:[/bold]")
                                    ui.console.print(f"[dim]{', '.join(keywords_dinamicas)}[/dim]")
                                    
                                    opcion_k = questionary.select(
                                        "¿Qué deseas hacer?",
                                        choices=[
                                            "✅ Confirmar y Guardar (Cache)",
                                            "✏️  Editar Manualmente",
                                            "🔄 Regenerar desde 0 con IA"
                                        ],
                                        style=questionary.Style([
                                            ('qmark', 'fg:white'),       
                                            ('question', 'bold fg:white'), 
                                            ('answer', 'fg:white'),      
                                            ('pointer', 'fg:white bold'),
                                            ('highlighted', 'bg:white fg:black'),
                                        ])
                                    ).ask()

                                    if "Confirmar" in opcion_k:
                                        # Guardar y salir
                                        save_keyword_cache(keywords_dinamicas, current_cv_hash)
                                        ui.console.print("✅ Keywords guardadas en cache para futuras búsquedas.")
                                        break
                                    
                                    elif "Editar" in opcion_k:
                                        nueva_str = questionary.text("Ingresa keywords (sep. por coma):", default=", ".join(keywords_dinamicas)).ask()
                                        if nueva_str:
                                            keywords_dinamicas = [k.strip() for k in nueva_str.split(",") if k.strip()]
                                    
                                    elif "Regenerar" in opcion_k:
                                        with ui.status_context("RE-ANALYZING..."):
                                            keywords_dinamicas = analyze_cv_keywords(cv_text)

                            else:
                                ui.console.print("⚠️ No se pudieron extraer keywords del CV.")
                        except Exception as e:
                            ui.console.print(f"❌ Error analizando CV: {e}")
                    else:
                        ui.console.print("⚠️ Análisis de CV omitido por el usuario.")

            # 2. Búsqueda
            resultados_crudos = recoleccion_de_vacantes(keywords_custom=keywords_dinamicas)
            
            if not resultados_crudos:
                ui.console.print("NO VACANCIES FOUND.")
                continue

            vacantes_finales = procesar_vacantes(resultados_crudos, urls_existentes)

            # Mostrar resumen antes de guardar
            ui.mostrar_tabla_resultados(vacantes_finales, titulo="Resumen de Vacantes Encontradas")

            if vacantes_finales and hoja:
                if ui.confirmar_accion("SAVE RESULTS TO GOOGLE SHEETS?"):
                    try:
                        with ui.status_context("SAVING TO CLOUD"):
                            actualizar_sheet(hoja, vacantes_finales)
                            registrar_actualizacion(hoja)
                        ui.console.print("✅ SAVE SUCCESSFUL!")
                    except Exception as e:
                        ui.console.print(f"CRITICAL ERROR SAVING: {e}")
                else:
                    ui.console.print("SAVE CANCELLED BY USER.")
            elif not vacantes_finales:
                ui.console.print("[dim]Nada nuevo que guardar.[/dim]")
            
            ui.console.print("\n------------------------------------------------\n")
            
        elif "Ver Vacantes" in opcion:
            ui.console.print("🚧 UNDER CONSTRUCTION. PLEASE CHECK GOOGLE SHEETS.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupción detectada. Saliendo...")
        sys.exit(0)
    except Exception as e:
        print(f"Error inesperado: {e}")
        traceback.print_exc()