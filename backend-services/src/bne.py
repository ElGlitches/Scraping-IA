from playwright.sync_api import sync_playwright
from datetime import datetime
from .utils import normalizar_texto, calc_prioridad, fecha_actual
from .config import PALABRAS_CLAVE

def buscar_vacantes_bne():
    ofertas = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for palabra in PALABRAS_CLAVE:
            try:
                url = f"https://www.bne.cl/ofertas?mostrar=empleo&textoLibre={palabra}"
                print(f"🔎 Buscando '{palabra}' en BNE...")
                page.goto(url, timeout=60000)
                # Reemplazado wait_for_timeout(8000) por espera inteligente
                try:
                    page.wait_for_selector("app-oferta-card", timeout=15000)
                except:
                    print(f"⚠️ No se detectaron ofertas inmediatamente para '{palabra}'.")
                
                
                # Forzar scroll para activar carga dinámica
                for _ in range(4):
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(2000)
                
                # Extraer elementos directamente del DOM renderizado
                cards = page.locator("app-oferta-card").all()
                print(f"💬 BNE '{palabra}': {len(cards)} resultados encontrados.")

                for card in cards[:5]:
                    try:
                        titulo = normalizar_texto(card.locator("a").inner_text())
                        url_oferta = "https://www.bne.cl" + card.locator("a").get_attribute("href")
                        empresa = normalizar_texto(card.locator("p strong").inner_text()) if card.locator("p strong").count() else ""
                        ubicacion = normalizar_texto(card.locator("p span").inner_text()) if card.locator("p span").count() else ""
                        publicada = normalizar_texto(card.locator("small").inner_text()) if card.locator("small").count() else ""
                        fecha_registro = fecha_actual()
                        modalidad = "N/A"
                        salario = "No informado"
                        prioridad = calc_prioridad(modalidad)

                        if titulo and url_oferta:
                            ofertas.append([
                                titulo, empresa, ubicacion, modalidad, url_oferta,
                                salario, "", fecha_registro, publicada, prioridad
                            ])
                    except Exception:
                        continue

            except Exception as e:
                print(f"⚠️ Error procesando BNE '{palabra}': {e}")
                continue

        browser.close()

    return ofertas
