from playwright.sync_api import sync_playwright
from datetime import datetime
import time
import random
from utils import normalizar_texto, calc_prioridad, fecha_actual

def extraer_datos_vacante(url: str):
    """
    Navega a una URL de vacante (Cualquier portal) y extrae sus datos.
    Usa selectores específicos y fallbacks genéricos (Meta tags, Body text).
    """
    datos = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # User-Agent genérico para evitar bloqueos simples
        context = browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        page = context.new_page()
        
        try:
            print(f"🌍 Navegando a: {url}...")
            page.goto(url, timeout=60000)
            
            # --- TÍTULO ---
            # 1. H1
            h1 = page.locator("h1").first
            if h1.count():
                datos["titulo"] = normalizar_texto(h1.inner_text())
            else:
                # 2. Meta Title / Title Tag
                datos["titulo"] = page.title()
            
            # --- EMPRESA ---
            # 1. Selectores comunes
            empresa_loc = page.locator("a.app-aware-link, div.job-details-jobs-unified-top-card__company-name, [class*='company'], [class*='employer']")
            if empresa_loc.count():
                datos["empresa"] = normalizar_texto(empresa_loc.first.inner_text())
            else:
                # 2. Meta Site Name
                try:
                    site_name = page.locator("meta[property='og:site_name']").get_attribute("content")
                    if site_name: datos["empresa"] = site_name
                except:
                    pass
            
            if "empresa" not in datos:
                datos["empresa"] = "Empresa Desconocida"

            # --- DESCRIPCIÓN ---
            selector_desc = "div.show-more-less-html__markup, div.description__text, section.core-section-container, div#job-details, div[class*='description'], article"
            desc = ""
            
            if page.locator(selector_desc).count() > 0:
                desc = page.locator(selector_desc).first.inner_text()
            
            # FALLBACK: Si no encontramos la caja de descripción, tomamos todo el texto visible.
            # La IA es buena filtrando menús y footers.
            if not desc or len(desc) < 100:
                print("⚠️ Usando modo 'Texto Completo' (Fallback genérico)...")
                desc = page.locator("body").inner_text()
                
            datos["descripcion"] = normalizar_texto(desc)
            
            # --- SALARIO ---
            # Buscar '$' en el texto
            salario = "No informado"
            if "$" in desc:
                # Intento muy naive de extraer la línea con $.
                # Mejor dejamos que la IA lo extraiga luego si es necesario, 
                # pero para el sheet intentamos algo simple.
                pass 
            datos["salario"] = salario
            
            datos["url"] = url
            datos["ubicacion"] = "Remoto/Desconocido"
            
            return datos
            
        except Exception as e:
            print(f"❌ Error scraping URL: {e}")
            return None
        finally:
            browser.close()

def buscar_vacantes_linkedin(keyword: str):
    ofertas = []
    
    if not keyword:
        return []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # --- FASE 1: Búsqueda y Recolección de URLs ---
            url_busqueda = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location=Chile"
            print(f"🔎 Buscando '{keyword}' en LinkedIn...")
            
            page.goto(url_busqueda, timeout=60000)
            
            selector_tarjeta = "li.base-card, div.job-search-card, div.base-card"
            
            try:
                page.wait_for_selector(selector_tarjeta, timeout=15000)
            except:
                print(f"⚠️ No se encontraron resultados inmediatos en LinkedIn para '{keyword}'.")

            # Breve scroll para cargar
            for _ in range(3):
                if page.locator(selector_tarjeta).count() > 0:
                    break
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(2000)

            cards = page.locator(selector_tarjeta).all()
            print(f"💬 LinkedIn '{keyword}': {len(cards)} resultados encontrados. Procesando Top 5...")

            pre_ofertas = []
            
            # Solo procesamos las 5 primeras para no ser bloqueados
            for card in cards[:5]: 
                try:
                    titulo = normalizar_texto(card.locator("h3.base-search-card__title").inner_text())
                    
                    # 🛡️ Detección de ofuscación (Asteriscos)
                    if not titulo or "****" in titulo:
                        # Intentar recuperar desde aria-label del enlace
                        try:
                            aria_label = card.locator("a.base-card__full-link").get_attribute("aria-label")
                            if aria_label:
                                titulo = normalizar_texto(aria_label)
                        except:
                            pass

                    # Si sigue ofuscado, saltar esta oferta basura
                    if "****" in titulo:
                        print(f"⚠️ Saltando oferta ofuscada/bloqueada: {titulo[:15]}...")
                        continue

                    empresa_loc = card.locator("h4.base-search-card__subtitle a")
                    empresa = normalizar_texto(empresa_loc.inner_text()) if empresa_loc.count() else ""
                    
                    ub_loc = card.locator("span.job-search-card__location")
                    if ub_loc.count():
                        # Limpieza agresiva de ubicación duplicada (Ej: "Santiago, Santiago...")
                        raw_loc = ub_loc.inner_text()
                        ubicacion = normalizar_texto(raw_loc.split(",")[0])
                    else:
                        ubicacion = ""
                    
                    link_loc = card.locator("a.base-card__full-link")
                    url_oferta = link_loc.get_attribute("href").split("?")[0] if link_loc.count() else ""
                    
                    if titulo and url_oferta:
                        pre_ofertas.append({
                            "titulo": titulo,
                            "empresa": empresa,
                            "ubicacion": ubicacion,
                            "url": url_oferta
                        })
                except Exception:
                    continue
            
            # --- FASE 2: Extracción Profunda (Visitar cada link) ---
            for item in pre_ofertas:
                try:
                    print(f"   -> Navegando a: {item['titulo'][:30]}...")
                    page.goto(item['url'], timeout=60000)
                    
                    # Esperar a que cargue la descripción
                    # Selectores comunes de descripción en LinkedIn Guest View
                    selector_desc = "div.show-more-less-html__markup, div.description__text, section.core-section-container"
                    try:
                        page.wait_for_selector(selector_desc, timeout=10000)
                    except:
                        pass # Si falla, intentaremos extraer lo que haya
                    
                    # Extraer descripción
                    descripcion = ""
                    if page.locator(selector_desc).count() > 0:
                        descripcion = page.locator(selector_desc).first.inner_text()
                    
                    # Limpieza básica
                    descripcion = normalizar_texto(descripcion)
                    
                    # Intentar extraer Salario (Sidebar o Texto)
                    salario = "No informado"
                    try:
                        # Estrategia 1: Buscar texto "Sueldo base" (común en Chile)
                        bloque_sueldo = page.locator("div", has_text="Sueldo base").filter(has_text="$").last
                        if bloque_sueldo.count() > 0:
                            # Tomar el texto, limpiar y buscar línea con números
                            texto_raw = bloque_sueldo.inner_text()
                            lines = texto_raw.split('\n')
                            for line in lines:
                                if "$" in line and any(c.isdigit() for c in line):
                                    salario = line.strip()
                                    break
                        
                        # Estrategia 2: Selectores de LinkedIn (insight de salario)
                        if salario == "No informado":
                            selectores_salario = [
                                "div.salary-insight__compensation-text",
                                "span.salary-main-rail-card__salary-text",
                                "div.compensation__salary-range"
                            ]
                            for sel in selectores_salario:
                                if page.locator(sel).count() > 0:
                                    salario = page.locator(sel).first.inner_text().strip()
                                    break
                    except Exception:
                        pass
                    
                    # Datos por defecto
                    publicada = fecha_actual()
                    modalidad = item.get("ubicacion", "N/A") # A veces la ubicación dice "Remoto"
                    prioridad = calc_prioridad(modalidad)

                    ofertas.append({
                        "titulo": item["titulo"],
                        "empresa": item["empresa"],
                        "ubicacion": item["ubicacion"],
                        "modalidad": modalidad,
                        "url": item["url"],
                        "salario": salario,
                        "descripcion": descripcion, 
                        "fecha_busqueda": fecha_actual(),
                        "fecha_publicacion": publicada,
                        "prioridad": prioridad
                    })
                    
                    # Pausa anti-bot para no ser agresivos
                    time.sleep(random.uniform(2.0, 4.0))

                except Exception as e:
                    print(f"⚠️ Error extrayendo detalle de '{item['titulo']}': {e}")
                    continue

        except Exception as e:
            print(f"⚠️ Error general en LinkedIn '{keyword}': {e}")
        
        finally:
            browser.close()

    return ofertas
