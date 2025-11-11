# Scraper directo de Trabajando.cl con Playwright
# Obtiene resultados reales desde el frontend React (sin depender de buscadores)

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from .utils import normalizar_texto, calc_prioridad, fecha_actual
from .config import PALABRAS_CLAVE

BASE_URL = "https://www.trabajando.cl/jobs?keywords={}"

def buscar_vacantes_trabajando():
    ofertas = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for palabra in PALABRAS_CLAVE:
            try:
                url = BASE_URL.format(palabra)
                page.goto(url, timeout=60000)
                page.wait_for_timeout(4000)  # esperar carga dinámica
                html = page.content()

                soup = BeautifulSoup(html, "html.parser")
                cards = soup.select("div.offer")  # estructura actual
                print(f"💬 Trabajando.cl '{palabra}': {len(cards)} resultados encontrados.")

                for card in cards[:5]:
                    titulo_tag = card.select_one("h2 a")
                    empresa_tag = card.select_one(".offer__company")
                    fecha_tag = card.select_one(".offer__date")
                    link_tag = card.select_one("h2 a")

                    titulo = normalizar_texto(titulo_tag.text if titulo_tag else "")
                    empresa = normalizar_texto(empresa_tag.text if empresa_tag else "")
                    url_oferta = link_tag["href"] if link_tag else ""
                    publicada = normalizar_texto(fecha_tag.text if fecha_tag else "")
                    fecha_registro = fecha_actual()

                    modalidad = "N/A"
                    salario = "No informado"
                    prioridad = calc_prioridad(modalidad)

                    if url_oferta.startswith("/"):
                        url_oferta = "https://www.trabajando.cl" + url_oferta

                    if titulo and url_oferta:
                        ofertas.append([
                            titulo, empresa, "Chile", modalidad, url_oferta,
                            salario, "", fecha_registro, publicada, prioridad
                        ])
            except Exception as e:
                print(f"⚠️ Error Trabajando.cl '{palabra}': {e}")
                continue

        browser.close()

    return ofertas
