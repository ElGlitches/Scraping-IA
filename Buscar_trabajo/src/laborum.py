import requests
from datetime import datetime
from .utils import normalizar_texto, calc_prioridad, fecha_actual
from .config import PALABRAS_CLAVE

API_URL = "https://www.laborum.cl/api/joboffers/search"

def buscar_vacantes_laborum():
    ofertas = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for palabra in PALABRAS_CLAVE:
        try:
            params = {
                "query": palabra,
                "page": 1,
                "size": 20,
                "area": "tecnologia-sistemas-y-telecomunicaciones"
            }
            response = requests.get(API_URL, headers=headers, params=params, timeout=15)
            if response.status_code != 200:
                print(f"⚠️ Laborum: error {response.status_code} para '{palabra}'")
                continue

            data = response.json()
            jobs = data.get("data", {}).get("jobOffers", [])
            print(f"💬 Laborum '{palabra}': {len(jobs)} resultados encontrados.")

            for job in jobs[:5]:
                titulo = normalizar_texto(job.get("title", ""))
                empresa = normalizar_texto(job.get("company", {}).get("name", ""))
                url_oferta = f"https://www.laborum.cl/empleo-{job.get('id', '')}.html"
                publicada = job.get("publishedDate", "")
                fecha_registro = fecha_actual()

                modalidad = job.get("modality", "N/A")
                salario = job.get("salary", "No informado")
                prioridad = calc_prioridad(modalidad)

                if not titulo or not url_oferta:
                    continue

                ofertas.append([
                    titulo, empresa, "Chile", modalidad, url_oferta,
                    salario, "", fecha_registro, publicada, prioridad
                ])
        except Exception as e:
            print(f"⚠️ Error Laborum '{palabra}': {e}")
            continue

    return ofertas
