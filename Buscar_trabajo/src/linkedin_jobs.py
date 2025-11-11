from playwright.sync_api import sync_playwright
from datetime import datetime
from .utils import normalizar_texto, calc_prioridad, fecha_actual
from .config import PALABRAS_CLAVE

def buscar_vacantes_linkedin():
    ofertas = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for palabra in PALABRAS_CLAVE:
            try:
                url = f"https://www.linkedin.com/jobs/search/?keywords={palabra}&location=Chile"
                print(f"🔎 Buscando '{palabra}' en LinkedIn...")
                page.goto(url, timeout=60000)
                page.wait_for_timeout(8000)

                # Esperar que aparezcan los resultados
                for _ in range(3):
                    if page.locator("li.base-card").count() > 0:
                        break
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(3000)

                cards = page.locator("li.base-card").all()
                print(f"💬 LinkedIn '{palabra}': {len(cards)} resultados encontrados.")

                for card in cards[:5]:
                    try:
                        titulo = normalizar_texto(card.locator("h3.base-search-card__title").inner_text())
                        empresa = normalizar_texto(card.locator("h4.base-search-card__subtitle a").inner_text()) if card.locator("h4.base-search-card__subtitle a").count() else ""
                        ubicacion = normalizar_texto(card.locator("span.job-search-card__location").inner_text()) if card.locator("span.job-search-card__location").count() else ""
                        url_oferta = card.locator("a.base-card__full-link").get_attribute("href").split("?")[0]
                        publicada = fecha_actual()
                        modalidad = "N/A"
                        salario = "No informado"
                        prioridad = calc_prioridad(modalidad)

                        if titulo and url_oferta:
                            ofertas.append([
                                titulo, empresa, ubicacion, modalidad, url_oferta,
                                salario, "", fecha_actual(), publicada, prioridad
                            ])
                    except Exception:
                        continue

            except Exception as e:
                print(f"⚠️ Error procesando LinkedIn '{palabra}': {e}")
                continue

        browser.close()

    return ofertas
