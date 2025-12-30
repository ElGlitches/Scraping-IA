import os
import sys
import glob
import time
import json
from src.asesor import iniciar_chat, generar_pack_postulacion
from src.sheets_manager import conectar_sheets, actualizar_estado, actualizar_sheet
from src.linkedin_jobs import extraer_datos_vacante
from src.analizador_vacantes import analizar_vacante

def obtener_vacantes_pendientes(sheet):
    """Obtiene vacantes con Match % = 'Pendiente' o vacío."""
    # Usamos get_all_values para evitar error de "duplicate headers" si hay columnas vacías
    todas_las_filas = sheet.get_all_values()
    
    # La fila 1 es metadata ("Última actualización..."), la fila 2 son los HEADERS
    if len(todas_las_filas) < 3:
        return []
        
    headers = todas_las_filas[1]
    data = []
    
    # Mapeo manual (Datos desde fila 3 en adelante)
    for i, row in enumerate(todas_las_filas[2:]):
        item = {}
        for j, h in enumerate(headers):
            if h and j < len(row): # Solo columnas con nombre
                item[h] = row[j]
        
        # Agregar índice real (i + 3 porque row 1 metadata, row 2 headers, i0 based)
        item["_row_idx"] = i + 3
        data.append(item)
    
    pendientes = []
    
    for row in data:
        start_date = row.get("Fecha de Registro", "")
        # Filtrado simple: Si no tiene Match % calculado o dice Pendiente
        match_val = str(row.get("Match %", "")).strip()
        
        # Lógica: Si es Pendiente, vacio, o 0.
        if match_val in ["Pendiente", "", "0"]:
            pendientes.append(row)
            
    # Ordenar las últimas primero
    return pendientes[::-1]

def procesar_vacante_seleccionada(vacante, sheet):
    """
    1. Analiza la vacante con IA
    2. Genera Pack
    3. Actualiza Sheet
    4. Retorna contexto para chat
    """
    print(f"\n🧠 Analizando a fondo: {vacante.get('Título')} @ {vacante.get('Empresa')}...")
    
    # 1. Análisis Técnico
    analisis_json = analizar_vacante(vacante.get("URL", ""), vacante.get("Título", ""))
    
    # Parsear para actualizar sheet
    try:
        data_analisis = json.loads(analisis_json)
        match_pct = data_analisis.get("match_percent", 0)
        
        # 2. Generar Pack (Carta, Tips)
        print("📝 Redactando estrategia de postulación...")
        pack_content = generar_pack_postulacion({
            "titulo": vacante.get("Título"),
            "empresa": vacante.get("Empresa"),
            "descripcion": "Revisar link para detalle", # El asesor ya tiene el contexto del análisis
            "url": vacante.get("URL"),
            "analisis_previo": analisis_json
        })
        
        # Guardar en archivo
        dir_reco = os.path.join(os.path.dirname(__file__), "recomendaciones")
        os.makedirs(dir_reco, exist_ok=True)
        filename = f"{vacante.get('Empresa')}_{vacante.get('Título')}.md".replace("/", "-").strip()
        filepath = os.path.join(dir_reco, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(pack_content)
            
        print(f"✅ Pack guardado en: recomendaciones/{filename}")
        
        # 3. Actualizar Sheet (Opcional, si queremos guardar el resultado)
        # Nota: Escribir en una celda específica requiere coordenadas.
        # Por simplicidad ahora, solo mostramos el resultado.
        print(f"🎯 Match IA calculado: {match_pct}%")
        
        return pack_content
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")
        return None

def main():
    print("\n👔 ASESOR DE VACANTES 'A DEMANDA' 👔")
    print("---------------------------------------")
    print("Conectando con tu base de vacantes...")
    
    try:
        sheet = conectar_sheets()
        vacantes = obtener_vacantes_pendientes(sheet)
    except Exception as e:
        print(f"❌ Error leyendo Excel: {e}")
        return

    print(f"\nSe encontraron {len(vacantes)} vacantes pendientes.")
    
    # Menu Principal
    print("\nOpciones:")
    print(" [1-10] Seleccionar vacante de la lista")
    print(" [L]    Analizar desde LINK externo 🌐")
    print(" [0]    Salir")

    # Mostrar menú (Top 10)
    top_n = vacantes[:10]
    for i, v in enumerate(top_n):
        print(f" [{i+1}] {v.get('Título')} - {v.get('Empresa')} (📍 {v.get('Ubicación')})")

    opcion_raw = input("\nElige opción: ").strip().lower()
    
    target_vacante = None
    modo_link = False

    if opcion_raw == "0":
        return
    elif opcion_raw == "l":
        modo_link = True
        url = input("Pegue el LINK de la vacante: ").strip()
        if not url: return
        print("🕵️ Scrapeando datos en vivo...")
        datos_scraped = extraer_datos_vacante(url)
        if not datos_scraped:
            print("❌ No se pudo extraer información del link.")
            return
        
        # Adaptar al formato de sheet
        target_vacante = {
            "Título": datos_scraped.get("titulo"),
            "Empresa": datos_scraped.get("empresa"),
            "Ubicación": datos_scraped.get("ubicacion"),
            "URL": datos_scraped.get("url"),
            "Descripción": datos_scraped.get("descripcion"),
            "Match %": "Nuevo",
            "_row_idx": None # No está en sheet aún
        }
    else:
        try:
            sel = int(opcion_raw)
            target_vacante = top_n[sel-1]
        except (ValueError, IndexError):
            print("Opción inválida.")
            return

    # Procesar
    contexto = procesar_vacante_seleccionada(target_vacante, sheet)
    
    if contexto:
        # Iniciar Chat
        print("\n💬 Iniciando Chat con el Asesor...")
        chat_session = iniciar_chat(contexto)
        
        print(f"\n🤖 Asesor: He estudiado la vacante {target_vacante.get('Título')}. ¿Preparamos la entrevista o revisamos la carta?")
        
        while True:
            user_input = input("\n👤 Tú: ")
            if user_input.lower() in ["salir", "exit", "chau"]:
                print("👋 ¡Éxito en tu postulación!")
                break
            
            try:
                resp = chat_session.send_message(user_input)
                print(f"\n🤖 Asesor: {resp.text}")
            except Exception as e:
                print(f"Error: {e}")

        # --- SEGUIMIENTO (LINK vs EXISTENTE) ---
        if modo_link:
             guardar = input("\n¿Quieres GUARDAR esta vacante en tu Excel? [S/N]: ").lower()
             if guardar == "s":
                 # Convertir keys para sheet manager
                 vacante_fmt = {k.lower(): v for k,v in target_vacante.items() if k != "_row_idx"}
                 vacante_fmt["fecha_busqueda"] = "Manual"
                 actualizar_sheet(sheet, [vacante_fmt])
                 print("✅ Vacante guardada. (Aparecerá en la lista la próxima vez)")
        
        # Solo ofrecemos tracking si tiene una fila asociada
        if target_vacante.get("_row_idx"):
            print("\n📊 SEGUIMIENTO:")
            print("¿Qué harás con esta vacante?")
            opcion = input("[P]ostulado ✅  | [D]escartar ❌  | [M]antener Pendiente ⏳ : ").lower()
            
            nuevo_estado = ""
            if opcion.startswith("p"):
                nuevo_estado = "Postulado"
            elif opcion.startswith("d"):
                nuevo_estado = "Rechazado"
                
            if nuevo_estado:
                actualizar_estado(target_vacante["_row_idx"], nuevo_estado)
            else:
                print("👌 Manteniendo en Pendiente.")

if __name__ == "__main__":
    main()
