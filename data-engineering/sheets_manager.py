import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    DataValidationRule, BooleanCondition, set_data_validation_for_cell_range,
    format_cell_ranges, CellFormat, set_frozen
)
from .config import SCOPES, SHEET_NAME 
import time

# 💡 COLUMNAS OPTIMIZADAS (Sin Descripción, Razón Match, Prioridad, Match %)
ENCABEZADOS = [
    "Título", "Empresa", "Ubicación", "Modalidad", "Nivel", "Jornada", "URL",
    "Salario", "Estado", "Fecha de Registro", "Fecha Publicación"
]

ESTADOS = ["Postulando", "Entrevista", "Rechazado", "Contratado", "Sin respuesta", "Descartado"]

def obtener_urls_existentes(sheet):
    """
    Obtiene un set con todas las URLs que ya están registradas en la hoja.
    Útil para filtrar antes de procesar.
    """
    try:
        data = sheet.get_all_values()
        # La URL sigue estando en índice 6 (columna G)
        urls = [row[6] for row in data[1:] if len(row) > 6 and row[6]]
        return set(urls)
    except Exception as e:
        print(f"Advertencia: No se pudieron cargar URLs existentes: {e}")
        return set()

def _aplicar_formato_y_validaciones(sheet):
    """Aplica el formato, filtro, congelación y validación de datos a la hoja."""
    
    set_frozen(sheet, rows=2)
    sheet.set_basic_filter()
    
    regla = DataValidationRule(BooleanCondition("ONE_OF_LIST", ESTADOS), showCustomUi=True)
    set_data_validation_for_cell_range(sheet, "I3:I10000", regla)
    
    # Ajuste de rango de negritas (A2:K2) - Ajustado a 11 columnas
    format_cell_ranges(sheet, [("A2:K2", CellFormat(textFormat={"bold": True}))])
    print("Formato y validaciones aplicadas.")

def aplanar_y_normalizar(resultados_crudos):
    """
    Convierte la lista de resultados de las búsquedas en una única lista de diccionarios normalizados.
    """
    vacantes_normalizadas = []
    
    if resultados_crudos:
        print(f"DEBUG APLANAR: El primer resultado crudo es de tipo: {type(resultados_crudos[0])}")
    
    for item in resultados_crudos: 
        if item is None:
            continue
        
        if isinstance(item, list):
            vacantes_normalizadas.extend(item)
        elif isinstance(item, dict):
            vacantes_normalizadas.append(item)
        else:
            print(f"DEBUG APLANAR: Tipo de dato inesperado encontrado: {type(item)}")
            
    vacantes_limpias = []
    for vacante in vacantes_normalizadas:
        vacante['url'] = vacante.get('url', '') 
        vacante['descripcion'] = vacante.get('descripcion', '') 
        
        vacantes_limpias.append(vacante)

    print(f"DEBUG APLANAR: Vacantes normalizadas listas para deducción: {len(vacantes_limpias)}")
    
    return vacantes_limpias

def conectar_sheets():
    """Establece la conexión, abre/crea el archivo y la hoja de vacantes."""
    
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    cliente = gspread.authorize(creds)

    sh = None
    for _ in range(3):
        try:
            try:
                sh = cliente.open(SHEET_NAME)
            except gspread.exceptions.SpreadsheetNotFound:
                print(f"No se encontró '{SHEET_NAME}', creando nuevo archivo en Drive...")
                sh = cliente.create(SHEET_NAME)
            break
        except Exception as e:
            if "503" in str(e):
                print("Google Sheets no disponible, reintentando...")
                time.sleep(3)
            else:
                raise
    else:
        raise RuntimeError("No se pudo conectar con Google Sheets después de varios intentos.")

    hojas = [ws.title for ws in sh.worksheets()]
    if "Vacantes" in hojas:
        return sh.worksheet("Vacantes")
    else:
        print("Creando hoja 'Vacantes' dentro del archivo...")
        return sh.add_worksheet("Vacantes", rows=200, cols=len(ENCABEZADOS))


def preparar_hoja(sheet):
    """
    Asegura que la hoja tenga los encabezados correctos y el formato base.
    Si los encabezados cambiaron, intenta MIGRAR los datos existentes.
    """
    try:
        datos = sheet.get_all_values()
    except Exception:
        datos = []
    
    # Caso 1: Hoja vacía o corrupta
    if len(datos) < 2:
        sheet.clear()
        print("Hoja vacía. Iniciando de cero.")
        sheet.update("A1", [[f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]])
        sheet.append_row(ENCABEZADOS)
        _aplicar_formato_y_validaciones(sheet)
        return

    # Caso 2: Verificar encabezados (Fila 2, índice 1)
    filas_actuales_headers = datos[1]
    headers_actuales = filas_actuales_headers[:len(ENCABEZADOS)]
    
    if headers_actuales == ENCABEZADOS:
        # Todo correcto
        sheet.update("A1", [[f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]])
        _aplicar_formato_y_validaciones(sheet)
        return

    # Caso 3: MIGRACIÓN DE COLUMNAS
    print(f"⚠️ Detectado cambio de estructura. Migrando datos... (Old: {len(headers_actuales)} cols, New: {len(ENCABEZADOS)} cols)")
    
    # Mapa de columnas antiguas: "NombreColumna" -> Indice
    mapa_old = {nombre: idx for idx, nombre in enumerate(filas_actuales_headers)}
    
    filas_migradas = []
    
    # Datos comienzan en fila 3 (índice 2)
    for fila_old in datos[2:]:
        nueva_fila = []
        for col_nueva in ENCABEZADOS:
            # Buscar si existe en la vieja
            idx_old = mapa_old.get(col_nueva)
            
            valor = ""
            if idx_old is not None and idx_old < len(fila_old):
                valor = fila_old[idx_old]
            
            nueva_fila.append(valor)
        filas_migradas.append(nueva_fila)
    
    # Reescribir hoja
    sheet.clear()
    sheet.update("A1", [[f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]])
    sheet.append_row(ENCABEZADOS)
    
    if filas_migradas:
        sheet.append_rows(filas_migradas)
        print(f"✅ Migración completada. {len(filas_migradas)} filas preservadas.")
    
    _aplicar_formato_y_validaciones(sheet)


def actualizar_sheet(sheet, ofertas: list[dict]):
    """
    Añade nuevas vacantes a la hoja.
    """
    
    existentes = obtener_urls_existentes(sheet)

    nuevas_filas = []

    for o in ofertas:
        url = o.get("url")

        if url and url in existentes:
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
            "",
            o.get("fecha_busqueda", ""),
            o.get("fecha_publicacion", "")
        ])

    if nuevas_filas:
        sheet.append_rows(nuevas_filas)
        print(f"{len(nuevas_filas)} nuevas vacantes agregadas.")
    else:
        print("No hay nuevas vacantes para agregar.")



def registrar_actualizacion(sheet):
    """Actualiza la celda A1 con la fecha actual."""
    try:
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sheet.update("A1", [[f"Última actualización: {fecha}"]])
        print("Fecha de actualización registrada.")
    except Exception as e:
        print(f"Error al registrar actualización: {e}")

def actualizar_estado(row_idx, nuevo_estado):
    """
    Actualiza el estado de una vacante en la hoja.
    row_idx: Índice de la fila (1-based).
    nuevo_estado: String (ej: "Postulado", "Descartado")
    """
    try:
        sheet = conectar_sheets()
        # La columna Estado es la I (9na columna)
        COL_ESTADO = 9 
        sheet.update_cell(row_idx, COL_ESTADO, nuevo_estado)
        print(f"✅ Estado actualizado en fila {row_idx}: {nuevo_estado}")
        return True
    except Exception as e:
        print(f"❌ Error actualizando estado: {e}")
        return False