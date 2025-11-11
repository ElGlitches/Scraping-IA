import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    DataValidationRule, BooleanCondition, set_data_validation_for_cell_range,
    format_cell_ranges, CellFormat, set_frozen
)
from .config import SCOPES, SHEET_NAME

# 🧱 Nuevos encabezados ampliados
ENCABEZADOS = [
    "Título", "Empresa", "Ubicación", "Modalidad", "Nivel", "Jornada", "URL",
    "Salario", "Estado", "Fecha de Registro", "Fecha Publicación", "Prioridad", "Descripción"
]

ESTADOS = ["Postulando", "Entrevista", "Rechazado", "Contratado", "Sin respuesta", "Descartado"]


# 🔗 Conexión con Google Sheets
def conectar_sheets():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    cliente = gspread.authorize(creds)

    import time
    for intento in range(3):
        try:
            try:
                sh = cliente.open(SHEET_NAME)
            except gspread.exceptions.SpreadsheetNotFound:
                print(f"📄 No se encontró '{SHEET_NAME}', creando nuevo archivo en Drive...")
                sh = cliente.create(SHEET_NAME)
            break
        except Exception as e:
            if "503" in str(e):
                print("⚠️ Google Sheets no disponible, reintentando...")
                time.sleep(5)
            else:
                raise
    else:
        raise RuntimeError("❌ No se pudo conectar con Google Sheets después de varios intentos.")

    # Crea o accede a la hoja "Vacantes"
    hojas = [ws.title for ws in sh.worksheets()]
    if "Vacantes" in hojas:
        return sh.worksheet("Vacantes")
    else:
        print("📄 Creando hoja 'Vacantes' dentro del archivo...")
        return sh.add_worksheet("Vacantes", rows=200, cols=len(ENCABEZADOS))


# 🧩 Preparar estructura base
def preparar_hoja(sheet):
    datos = sheet.get_all_values()

    if len(datos) < 2 or datos[1][:len(ENCABEZADOS)] != ENCABEZADOS:
        sheet.clear()
        sheet.update("A1", [[f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]])
        sheet.append_row(ENCABEZADOS)
    else:
        sheet.update("A1", [[f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]])

    set_frozen(sheet, rows=2)
    sheet.set_basic_filter()
    regla = DataValidationRule(BooleanCondition("ONE_OF_LIST", ESTADOS), showCustomUi=True)
    set_data_validation_for_cell_range(sheet, "I3:I10000", regla)
    format_cell_ranges(sheet, [("A2:M2", CellFormat(textFormat={"bold": True}))])


# 🧾 Actualizar hoja con nuevas vacantes
def actualizar_sheet(sheet, ofertas):
    valores = sheet.get_all_values()
    existentes = {fila[6] for fila in valores[1:] if len(fila) >= 7}  # URLs existentes
    nuevas_filas = []

    for o in ofertas:
        try:
            if isinstance(o, dict):
                url = o.get("url", "")
                if not url or url in existentes:
                    continue

                nuevas_filas.append([
                    o.get("titulo", ""),
                    o.get("empresa", ""),
                    o.get("ubicacion", ""),
                    o.get("modalidad", ""),
                    o.get("nivel", ""),
                    o.get("jornada", ""),
                    o.get("url", ""),
                    o.get("salario", ""),
                    "",  # Estado editable
                    o.get("fecha_busqueda", ""),
                    o.get("fecha_publicacion", ""),
                    o.get("prioridad", ""),
                    o.get("descripcion", "")
                ])

            elif isinstance(o, list) and len(o) >= 10:
                url = o[4]
                if not url or url in existentes:
                    continue
                nuevas_filas.append(o[:len(ENCABEZADOS)])
        except Exception as e:
            print(f"⚠️ Error procesando fila: {e}")

    if nuevas_filas:
        sheet.append_rows(nuevas_filas)
        print(f"✅ {len(nuevas_filas)} nuevas vacantes agregadas.")
    else:
        print("🔄 No hay nuevas vacantes para agregar.")


# 🕒 Registrar fecha de última actualización
def registrar_actualizacion(sheet):
    valor = f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    sheet.update("A1", [[valor]])
    print("🕒 Fecha de actualización registrada.")
