import requests
from datetime import datetime
from .utils import normalizar_texto, calc_prioridad, fecha_actual
from .config import URL_GETONBRD, PALABRAS_CLAVE, MAX_VACANTES_POR_PALABRA

SENIORITY_MAP = {
    1: "Trainee/Intern",
    2: "Junior",
    3: "Semi Senior",
    4: "Senior",
    5: "Lead/Expert",
}
TIME_MODALITY_MAP = {
    "full_time": "Full time",
    "part_time": "Part time",
    "freelance": "Freelance",
    "contract": "Contrato",
}
WORKPLACE_MAP = {
    "fully_remote": "Remoto (global)",
    "remote_local": "Remoto (local)",
    "hybrid": "Híbrido",
    "no_remote": "Presencial",
}


def _map_seniority(raw):
    if isinstance(raw, int):
        return SENIORITY_MAP.get(raw, "")
    if isinstance(raw, str):
        try:
            return SENIORITY_MAP.get(int(raw), "") or raw.replace("_", " ").title()
        except ValueError:
            return raw.replace("_", " ").title()
    if isinstance(raw, dict):
        sid = raw.get("id") or (raw.get("data", {}) or {}).get("id")
        try:
            sid = int(sid)
        except Exception:
            pass
        return SENIORITY_MAP.get(sid, "")
    return ""


def _map_time_modality(raw):
    if isinstance(raw, str):
        return TIME_MODALITY_MAP.get(raw, raw.replace("_", " ").title())
    return ""


def _map_workplace(raw):
    if isinstance(raw, str):
        return WORKPLACE_MAP.get(raw, raw.replace("_", " ").title())
    return ""


def buscar_vacantes_getonbrd():
    ofertas = []

    for palabra in PALABRAS_CLAVE:
        try:
            r = requests.get(URL_GETONBRD.format(palabra), timeout=15)
            if r.status_code != 200:
                print(f"⚠️ Error {r.status_code} al buscar '{palabra}' en GetOnBrd.")
                continue

            respuesta = r.json()
            data = respuesta.get("data", [])
            included = respuesta.get("included", [])

            # Crea un mapa id_empresa → nombre_empresa
            empresas = {}
            for inc in included:
                if inc.get("type") == "Company":
                    empresas[inc["id"]] = normalizar_texto(inc.get("attributes", {}).get("name", ""))

        except Exception as e:
            print(f"⚠️ Error al conectar con GetOnBrd para '{palabra}': {e}")
            continue

        for item in data[:MAX_VACANTES_POR_PALABRA]:
            attrs = item.get("attributes", {}) or {}

            titulo = normalizar_texto(attrs.get("title"))
            empresa_id = item.get("relationships", {}).get("company", {}).get("data", {}).get("id")
            empresa = empresas.get(empresa_id, "No indicado")

            pais = normalizar_texto(attrs.get("country_name") or "")
            ciudad = normalizar_texto(attrs.get("city") or "")
            ubicacion = (f"{ciudad}, {pais}".strip(", ") or pais or ciudad or "No indicado")

            workplace = attrs.get("workplace_type") or attrs.get("remote_modality")
            modalidad = _map_workplace(workplace) or normalizar_texto(attrs.get("modality") or "N/A")

            nivel = _map_seniority(attrs.get("seniority"))
            jornada = _map_time_modality(attrs.get("time_modality"))

            permalink = attrs.get("permalink") or f"/jobs/{item.get('id', '')}"
            url = f"https://www.getonbrd.com{permalink}"

            salario_min = attrs.get("min_salary")
            salario_max = attrs.get("max_salary")
            moneda = (attrs.get("currency") or "USD").upper()

            if salario_min and salario_max:
                salario = f"{salario_min} - {salario_max} {moneda}"
            elif salario_min:
                salario = f"Desde {salario_min} {moneda}"
            elif salario_max:
                salario = f"Hasta {salario_max} {moneda}"
            else:
                salario = "No informado"

            pub = attrs.get("published_at")
            if isinstance(pub, str):
                publicada = pub[:10]
            elif isinstance(pub, int):
                publicada = datetime.utcfromtimestamp(pub).strftime("%Y-%m-%d")
            else:
                publicada = ""

            descripcion = normalizar_texto(attrs.get("excerpt") or "")

            ofertas.append({
                "fuente": "GetOnBrd",
                "titulo": titulo,
                "empresa": empresa,
                "ubicacion": ubicacion,
                "modalidad": modalidad,
                "nivel": nivel,
                "jornada": jornada,
                "url": url,
                "salario": salario,
                "descripcion": descripcion,
                "fecha_busqueda": fecha_actual(),
                "fecha_publicacion": publicada,
                "prioridad": calc_prioridad(modalidad or jornada),
            })

    return ofertas
