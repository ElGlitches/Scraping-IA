# Scraper de Computrabajo Chile
# Obtiene Título, Empresa, Modalidad, Salario y Fecha de publicación correctamente mapeados

import requests
from bs4 import BeautifulSoup
from .utils import normalizar_texto, calc_prioridad, fecha_actual
from .config import PALABRAS_CLAVE

BASE_URL = "https://www.computrabajo.cl/trabajo-de-{}"

def buscar_vacantes_computrabajo():
    ofertas = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for palabra in PALABRAS_CLAVE:
        try:
            url = BASE_URL.format(palabra)
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"⚠️ Computrabajo: error {response.status_code} para '{palabra}'")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select("article.box_offer")  # estructura general
            print(f"💬 Computrabajo '{palabra}': {len(cards)} resultados encontrados.")

            for card in cards[:5]:
                titulo_tag = card.select_one("a.js-o-link")
                empresa_tag = card.select_one("a.dIB")
                modalidad_tag = card.select_one(".tag_base")
                salario_tag = card.select_one(".tag_salary")
                fecha_tag = card.select_one(".fs13")

                titulo = normalizar_texto(titulo_tag.text if titulo_tag else "")
                empresa = normalizar_texto(empresa_tag.text if empresa_tag else "")
                modalidad = normalizar_texto(modalidad_tag.text if modalidad_tag else "N/A")
                salario = normalizar_texto(salario_tag.text if salario_tag else "No informado")
                publicada = normalizar_texto(fecha_tag.text if fecha_tag else "")
                url_oferta = titulo_tag["href"] if titulo_tag else ""
                fecha_registro = fecha_actual()

                prioridad = calc_prioridad(modalidad)

                if not titulo or not url_oferta:
                    continue

                if url_oferta.startswith("/"):
                    url_oferta = "https://www.computrabajo.cl" + url_oferta

                ofertas.append([
                    titulo, empresa, "Chile", modalidad, url_oferta,
                    salario, "", fecha_registro, publicada, prioridad
                ])
        except Exception as e:
            print(f"⚠️ Error Computrabajo '{palabra}': {e}")
            continue

    return ofertas
