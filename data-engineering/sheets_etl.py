"""
Script: Sheets_ETL_Pipeline.py
Purpose: Automated extraction and load process for Google Sheets vacancy tracking.
Author: Iván Durán
"""
import os
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from gspread_formatting import (
    DataValidationRule, BooleanCondition, set_data_validation_for_cell_range,
    ConditionalFormatRule, BooleanRule, CellFormat, Color, format_cell_ranges, set_frozen, GridRange
)

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")

# --- CONFIGURACIÓN ---
PALABRAS_CLAVE = ["python", "data", "automatización", "etl", "backend", "devops", "cloud"]
URL_API = "https://www.getonbrd.com/api/v0/search/jobs?query={}"
SHEET_NAME = "vacantes"

# --- AUTENTICACIÓN GOOGLE ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
CREDENCIALES = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
cliente = gspread.authorize(CREDENCIALES)

# --- ENCABEZADOS ---
ENCABEZADOS = [
    "Título", "Empresa", "Ubicación", "Modalidad", "URL",
    "Salario", "Estado", "Fecha de Registro", "Fecha Publicación", "Prioridad"
]
ESTADOS = ["Postulando", "Entrevista", "Rechazado", "Contratado", "Sin respuesta"]

# --- CREAR O ABRIR HOJA ---

def abrir_o_crear_hoja(nombre: str):
    try:
        sh = cliente.open(nombre)
        try:
            hoja = sh.worksheet("vacantes")  # Usa tu pestaña actual
        except gspread.exceptions.WorksheetNotFound:
            print("📄 No se encontró 'vacantes'. Creando una nueva…")
            hoja = sh.add_worksheet(title="vacantes", rows=1000, cols=10)
    except gspread.exceptions.SpreadsheetNotFound:
        print("📄 No se encontró la hoja. Creando una nueva…")
        sh = cliente.create(nombre)
        hoja = sh.add_worksheet(title="vacantes", rows=1000, cols=10)
    return hoja

try:
    sh = cliente.open(SHEET_NAME)
    print("Pestañas encontradas:", [ws.title for ws in sh.worksheets()])
    sheet = sh.worksheet("Vacantes")
except gspread.exceptions.WorksheetNotFound:
    print("📄 No existe la pestaña 'Vacantes', creando una nueva…")
    sheet = sh.add_worksheet(title="Vacantes", rows=1000, cols=10)
    sheet.append_row(ENCABEZADOS)



# --- ENCABEZADOS ---
def verificar_encabezados():
    datos = sheet.get_all_values()
    if not datos:
        sheet.append_row(ENCABEZADOS)
        print("🧩 Encabezados creados automáticamente.")
    elif datos[0] != ENCABEZADOS:
        print("ℹ️ La hoja tiene encabezados distintos. Se continúan usando los actuales.")

# --- CONFIGURACIÓN VISUAL Y FORMATO ---
def configurar_ui():
    # Congela la fila 1
    set_frozen(sheet, rows=1)

    # Activa filtros
    try:
        sheet.set_basic_filter()
    except Exception:
        pass

    # Validación de datos (menú desplegable)
    regla = DataValidationRule(
        BooleanCondition("ONE_OF_LIST", ESTADOS),
        showCustomUi=True
    )
    set_data_validation_for_cell_range(sheet, "G2:G10000", regla)

    # Formato condicional por Estado (compatible con versiones recientes)
    estado_rango = GridRange.from_a1_range("G2:G10000", sheet)
    reglas = []

    def regla_color(texto, color):
        return ConditionalFormatRule(
            ranges=[estado_rango],
            booleanRule=BooleanRule(
                condition=BooleanCondition("TEXT_EQ", [texto]),
                format=CellFormat(backgroundColor=color)
            )
        )

    reglas.extend([
        regla_color("Postulando", Color(0.78, 0.87, 1.0)),   # azul
        regla_color("Entrevista", Color(1.0, 0.95, 0.7)),    # amarillo
        regla_color("Rechazado", Color(1.0, 0.8, 0.8)),      # rojo
        regla_color("Contratado", Color(0.8, 0.94, 0.8)),    # verde
        regla_color("Sin respuesta", Color(0.93, 0.93, 0.93))  # gris
    ])

        # Aplicar formato condicional por API (versión compatible y estable)
    try:
        requests_list = []
        colores = {
            "Postulando": (0.78, 0.87, 1.0),
            "Entrevista": (1.0, 0.95, 0.7),
            "Rechazado": (1.0, 0.8, 0.8),
            "Contratado": (0.8, 0.94, 0.8),
            "Sin respuesta": (0.93, 0.93, 0.93)
        }

        for texto, (r, g, b) in colores.items():
            requests_list.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": sheet.id,
                            "startRowIndex": 1,
                            "endRowIndex": 10000,
                            "startColumnIndex": 6,
                            "endColumnIndex": 7
                        }],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [{"userEnteredValue": texto}]
                            },
                            "format": {
                                "backgroundColor": {"red": r, "green": g, "blue": b}
                            }
                        }
                    },
                    "index": 0
                }
            })

        sheet.spreadsheet.batch_update({"requests": requests_list})
        print("🎨 Formato condicional aplicado correctamente.")
    except Exception as e:
        print(f"⚠️ Error aplicando formato condicional: {e}")


    # Formato encabezados (negrita)
    try:
        format_cell_ranges(sheet, [("A1:J1", CellFormat(textFormat={"bold": True}))])
    except Exception:
        pass

# --- FUNCIONES AUXILIARES ---
def normalizar_texto(valor, por_defecto=""):
    if valor is None:
        return por_defecto
    try:
        return str(valor).strip()
    except Exception:
        return por_defecto

def formatear_salario(attrs):
    sal = attrs.get("salary")
    if isinstance(sal, dict):
        minimo = sal.get("min")
        maximo = sal.get("max")
        curr = sal.get("currency", "")
        periodo = sal.get("payment_period", "")
        partes = []
        if minimo is not None and maximo is not None:
            partes.append(f"{minimo}-{maximo}")
        elif minimo is not None:
            partes.append(f"{minimo}+")
        if curr:
            partes.append(curr)
        if periodo:
            partes.append(periodo)
        return " ".join(str(p) for p in partes) if partes else "No informado"
    return "No informado"

def calc_prioridad(modalidad: str) -> str:
    m = (modalidad or "").lower()
    if any(x in m for x in ["remote", "remoto"]):
        return "Alta"
    if any(x in m for x in ["hybrid", "híbrido", "hibrido"]):
        return "Media"
    return "Baja"

def fecha_publicacion(attrs) -> str:
    iso = attrs.get("published_at")
    if not iso:
        return ""
    try:
        return iso[:10]
    except Exception:
        return ""

# --- BUSCAR VACANTES ---
def buscar_vacantes():
    ofertas = []
    for palabra in PALABRAS_CLAVE:
        try:
            r = requests.get(URL_API.format(palabra), timeout=20)
            if r.status_code != 200:
                continue
            data = r.json().get("data", [])
        except Exception as e:
            print(f"⚠️ Error buscando '{palabra}': {e}")
            continue
        
        print(f"💬 {palabra}: {len(data)} resultados obtenidos.")
        
        for item in data[:5]:
            attrs = item.get("attributes", {})

            titulo = normalizar_texto(attrs.get("title"))
            empresa = normalizar_texto(attrs.get("company", {}).get("name"))
            ubicacion = normalizar_texto(attrs.get("country_name"))
            modalidad = normalizar_texto(attrs.get("modality")) if isinstance(attrs.get("modality"), str) else "N/A"
            
            # Manejo robusto del permalink
            permalink = attrs.get("permalink")
            if not permalink:
                job_id = item.get("id", "")
                permalink = f"/jobs/{job_id}" if job_id else ""
            
            url = f"https://www.getonbrd.com{permalink}" if permalink else ""

            # si aún no hay URL, omite
            if not url:
                continue

            salario = formatear_salario(attrs)
            fecha_registro = datetime.now().strftime("%Y-%m-%d")
            publicada = fecha_publicacion(attrs)
            prioridad = calc_prioridad(modalidad)

            ofertas.append([
                titulo, empresa, ubicacion, modalidad, url,
                salario, "", fecha_registro, publicada, prioridad
            ])
    
    print(f"🧾 Total de ofertas obtenidas: {len(ofertas)}")
    return ofertas


# --- ACTUALIZAR HOJA ---
def actualizar_sheet(ofertas):
    valores = sheet.get_all_values()

    # Si la hoja está vacía o no tiene los encabezados correctos, la reinicia
    if not valores or valores[0] != ENCABEZADOS:
        print("📄 Hoja vacía o con encabezados incorrectos. Reiniciando contenido...")
        sheet.clear()
        sheet.append_row(ENCABEZADOS)
        existentes = set()
    else:
        existentes = set()
        for fila in valores[1:]:
            if len(fila) >= 5:  # aseguramos que tenga URL
                existentes.add(fila[4])

    nuevas = [o for o in ofertas if o[4] not in existentes]

    if nuevas:
        sheet.append_rows(nuevas)
        print(f"✅ {len(nuevas)} nuevas vacantes agregadas.")
    else:
        print("🔄 No hay nuevas vacantes para agregar.")


# --- MAIN ---
if __name__ == "__main__":
    print("Buscando vacantes...")
    verificar_encabezados()
    configurar_ui()
    resultados = buscar_vacantes()
    actualizar_sheet(resultados)
    print("✔️ Listo.")
