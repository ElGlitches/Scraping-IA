import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    DataValidationRule, BooleanCondition, set_data_validation_for_cell_range,
    format_cell_ranges, CellFormat, set_frozen
)
# Asumo que config está en el mismo nivel o es una ruta válida.
from .config import SCOPES, SHEET_NAME 
import time

# 🧱 Nuevos encabezados ampliados
ENCABEZADOS = [
    "Título", "Empresa", "Ubicación", "Modalidad", "Nivel", "Jornada", "URL",
    "Salario", "Estado", "Fecha de Registro", "Fecha Publicación", "Prioridad", "Descripción"
]

ESTADOS = ["Postulando", "Entrevista", "Rechazado", "Contratado", "Sin respuesta", "Descartado"]

# --- FUNCIONES AUXILIARES ---

def _aplicar_formato_y_validaciones(sheet):
    """Aplica el formato, filtro, congelación y validación de datos a la hoja."""
    
    # Congelar filas de encabezado
    set_frozen(sheet, rows=2)
    sheet.set_basic_filter()
    
    # 🔗 Regla de validación de datos para la columna 'Estado'
    regla = DataValidationRule(BooleanCondition("ONE_OF_LIST", ESTADOS), showCustomUi=True)
    # Rango de validación: Columna I (Estado) desde la fila 3 hasta la 10000
    set_data_validation_for_cell_range(sheet, "I3:I10000", regla)
    
    # 🎨 Formato: Encabezados en negrita
    # Rango de A2:M2 (fila de encabezados)
    format_cell_ranges(sheet, [("A2:M2", CellFormat(textFormat={"bold": True}))])
    print("🎨 Formato y validaciones aplicadas.")

def aplanar_y_normalizar(resultados_crudos):
    """
    Convierte la lista de resultados de las búsquedas en una única lista de diccionarios normalizados.
    """
    vacantes_normalizadas = []
    
    # Lógica de aplanamiento
    for lista_vacantes in resultados_crudos:
        if isinstance(lista_vacantes, list):
            vacantes_normalizadas.extend(lista_vacantes)
        elif isinstance(lista_vacantes, dict):
            vacantes_normalizadas.append(lista_vacantes)

    # Lógica de normalización
    vacantes_limpias = []
    for vacante in vacantes_normalizadas:
        if 'descripcion' not in vacante:
             vacante['descripcion'] = ''
        # Aquí puedes añadir más normalizaciones, si las tienes.
        vacantes_limpias.append(vacante)

    return vacantes_limpias

# 🔗 Conexión con Google Sheets
def conectar_sheets():
    """Establece la conexión, abre/crea el archivo y la hoja de vacantes."""
    
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    cliente = gspread.authorize(creds)

    # 🔄 Lógica de reintento simplificada
    sh = None
    for _ in range(3):
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
                time.sleep(3) # Reducido el tiempo de espera
            else:
                raise # Otros errores se elevan inmediatamente
    else:
        raise RuntimeError("❌ No se pudo conectar con Google Sheets después de varios intentos.")

    # 📄 Crea o accede a la hoja "Vacantes"
    hojas = [ws.title for ws in sh.worksheets()]
    if "Vacantes" in hojas:
        return sh.worksheet("Vacantes")
    else:
        print("📄 Creando hoja 'Vacantes' dentro del archivo...")
        # Usa el tamaño de los encabezados para definir las columnas
        return sh.add_worksheet("Vacantes", rows=200, cols=len(ENCABEZADOS))


# 🧩 Preparar estructura base
def preparar_hoja(sheet):
    """
    Asegura que la hoja tenga los encabezados correctos y el formato base.
    """
    datos = sheet.get_all_values()
    
    # Condición de verificación más robusta para encabezados
    # Si la hoja está vacía (len(datos) < 2) O si el encabezado no coincide
    if len(datos) < 2 or datos[1][:len(ENCABEZADOS)] != ENCABEZADOS:
        sheet.clear()
        print("🗑️ Hoja limpiada. Insertando nuevos encabezados y formato.")
        sheet.update("A1", [[f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]])
        sheet.append_row(ENCABEZADOS)
        
        # Aplicamos formato inmediatamente después de insertar encabezados
        _aplicar_formato_y_validaciones(sheet)
    else:
        # Solo actualiza el registro de A1 si la estructura es correcta
        sheet.update("A1", [[f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]])
        _aplicar_formato_y_validaciones(sheet) # Asegurar que el formato esté aplicado


# 🧾 Actualizar hoja con nuevas vacantes
def actualizar_sheet(sheet, ofertas: list[dict]):
    """
    Añade nuevas vacantes a la hoja, asumiendo que 'ofertas' es una lista de diccionarios
    estandarizados (ya normalizados y deducidos en el paso anterior).
    """
    
    # 1. Obtener URLs existentes para deduplicación
    try:
        # Columna G (indice 6) es donde está la URL
        urls_columna = sheet.col_values(7, value_render_option='UNFORMATTED_VALUE')[2:] 
        existentes = set(urls_columna)
    except Exception:
        # En caso de error de lectura, asumimos que no hay duplicados (más seguro)
        existentes = set()
    
    nuevas_filas = []

    # 2. Generar filas a partir de los diccionarios
    for o in ofertas:
        url = o.get("url")

        # Se espera que 'o' sea un dict. Si la URL es inválida o ya existe, saltar.
        if not url or url in existentes:
            continue

        # 3. Mapeo de diccionario a lista (asegura el orden de ENCABEZADOS)
        nuevas_filas.append([
            o.get("titulo", ""),
            o.get("empresa", ""),
            o.get("ubicacion", ""),
            o.get("modalidad", ""),
            o.get("nivel", ""),
            o.get("jornada", ""),
            o.get("url", ""),
            o.get("salario", ""),
            "",  # Estado editable (vacío por defecto)
            o.get("fecha_busqueda", ""),
            o.get("fecha_publicacion", ""),
            o.get("prioridad", ""),
            o.get("descripcion", "")
        ])

    if nuevas_filas:
        sheet.append_rows(nuevas_filas)
        print(f"✅ {len(nuevas_filas)} nuevas vacantes agregadas.")
    else:
        print("🔄 No hay nuevas vacantes para agregar.")


# 🕒 Registrar fecha de última actualización
def registrar_actualizacion(sheet):
    """Actualiza la celda A1 con la fecha y hora actuales."""
    valor = f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    sheet.update("A1", [[valor]])
    print("🕒 Fecha de actualización registrada.")