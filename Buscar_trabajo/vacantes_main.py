from src.getonbrd import buscar_vacantes_getonbrd
# from src.linkedin_jobs import buscar_vacantes_linkedin
# from src.trabajando import buscar_vacantes_trabajando
# from src.computrabajo import buscar_vacantes_computrabajo
from src.sheets_manager import conectar_sheets, preparar_hoja, actualizar_sheet, registrar_actualizacion
# from src.analizador_vacantes import analizar_vacante


# ----------------------------
# 🧩 Funciones auxiliares
# ----------------------------
def fila_lista_a_dict(fila):
    """Convierte filas tipo lista (legacy) a diccionario estándar."""
    try:
        return {
            "fuente": "Desconocida",
            "titulo": fila[0] if len(fila) > 0 else "",
            "empresa": fila[1] if len(fila) > 1 else "",
            "ubicacion": fila[2] if len(fila) > 2 else "",
            "modalidad": fila[3] if len(fila) > 3 else "",
            "url": fila[4] if len(fila) > 4 else "",
            "salario": fila[5] if len(fila) > 5 else "",
            "descripcion": "",
            "fecha_busqueda": fila[7] if len(fila) > 7 else "",
            "fecha_publicacion": fila[8] if len(fila) > 8 else "",
            "prioridad": fila[9] if len(fila) > 9 else "",
        }
    except Exception:
        return None


def aplanar_y_normalizar(resultados):
    """Aplana listas anidadas y convierte entradas legacy (listas) a dicts."""
    planos = []
    pila = list(resultados)
    while pila:
        item = pila.pop(0)
        if isinstance(item, list) and item and isinstance(item[0], (list, dict)):
            pila = item + pila
            continue
        if isinstance(item, dict):
            planos.append(item)
        elif isinstance(item, list):
            d = fila_lista_a_dict(item)
            if d and d.get("url"):
                planos.append(d)
            else:
                print(f"⚠️ Entrada descartada (lista inválida): {item}")
        else:
            print(f"⚠️ Entrada descartada (tipo no soportado): {type(item)}")
    return planos


# ----------------------------
# 🚀 Ejecución principal
# ----------------------------
if __name__ == "__main__":
    print("🚀 Iniciando búsqueda de vacantes...")

    # 1️⃣ Recolección de vacantes
    resultados = []
    resultados += buscar_vacantes_getonbrd() or []
    # resultados += buscar_vacantes_linkedin() or []
    # resultados += buscar_vacantes_trabajando() or []
    # resultados += buscar_vacantes_computrabajo() or []

    print(f"📊 {len(resultados)} vacantes encontradas. Normalizando datos...")

    # 2️⃣ Normalización de datos (aplanar listas, convertir formatos)
    vacantes = aplanar_y_normalizar(resultados)
    print(f"🧩 Vacantes normalizadas: {len(vacantes)}")

    # 3️⃣ Análisis (placeholder por ahora)
    for i, v in enumerate(vacantes, 1):
        try:
            desc = v.get("descripcion", "") if isinstance(v, dict) else ""
            titulo = v.get("titulo", "Vacante sin título")
            if not desc:
                v["analisis"] = "Sin descripción disponible."
            else:
                # analisis = analizar_vacante(desc)
                analisis = "Análisis simulado (placeholder)"
                v["analisis"] = analisis
            if i % 10 == 0 or i == len(vacantes):
                print(f"🔍 Analizadas {i}/{len(vacantes)}")
        except Exception as e:
            if isinstance(v, dict):
                v["analisis"] = f"Error al analizar: {e}"
            print(f"⚠️ Error analizando vacante {i}: {e}")

    # 4️⃣ Eliminación de duplicados por URL
    urls_vistas = set()
    vacantes_unicas = []
    for v in vacantes:
        url = v.get("url")
        if url and url not in urls_vistas:
            urls_vistas.add(url)
            vacantes_unicas.append(v)
    print(f"🧼 Eliminadas duplicadas: {len(vacantes) - len(vacantes_unicas)} duplicadas filtradas.")
    print(f"📦 Vacantes únicas para registrar: {len(vacantes_unicas)}")

    # 5️⃣ Carga en Google Sheets
    sheet = conectar_sheets()
    preparar_hoja(sheet)
    actualizar_sheet(sheet, vacantes_unicas)
    registrar_actualizacion(sheet)

    print("✔️ Proceso finalizado con análisis incluidos.")
