import os
import sys
import glob
import time
import json
from src.asesor import iniciar_chat, generar_pack_postulacion, enviar_mensaje_multimodal
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
    description_to_analyze = vacante.get("Descripción", "")
    analisis_json = analizar_vacante(description_to_analyze, vacante.get("Título", ""))
    
    # Parsear para actualizar sheet
    try:
        data_analisis = json.loads(analisis_json)
        match_pct = data_analisis.get("match_percent", 0)

        # Actualizar datos si son genéricos (Extracción automática)
        if vacante.get("Título") == "Cargo Manual":
             vacante["Título"] = data_analisis.get("titulo_vacante", "Cargo Manual")
        
        if vacante.get("Empresa") == "Empresa Manual":
             vacante["Empresa"] = data_analisis.get("empresa", "Empresa Manual")
        
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
    # Menu Principal Loop
    while True:
        print("\nOpciones:")
        print(" [1-10] Seleccionar vacante de la lista")
        print(" [L]    Analizar desde LINK externo 🌐")
        print(" [T]    Pegar Texto/Descripción directa 📋")
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
            if not url: continue
            print("🕵️ Scrapeando datos en vivo...")
            datos_scraped = extraer_datos_vacante(url)
            if not datos_scraped:
                print("❌ No se pudo extraer información del link.")
                continue
            
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
            break # Exit menu loop to process
            
        elif opcion_raw == "t":
            print("\n📋 MODO TEXTO MANUAL (Extracción Automática)")
            titulo = "Cargo Manual" 
            empresa = "Empresa Manual"
            
            print("\n📝 PEGA LA DESCRIPCIÓN ABAJO:")
            print("   (Cuando termines, escribe 'FIN' en una nueva línea y dale Enter)")
            print("   --------------------------------------------------------------")
            
            lines = []
            while True:
                try:
                    line = input()
                    if line.strip().upper() == "FIN":
                        break
                    lines.append(line)
                except EOFError:
                    break
            
            desc_full = "\n".join(lines).strip()
            if len(desc_full) < 20: 
                print("❌ Descripción muy corta / vacía.")
                continue
    
            modo_link = True # Tratamos como 'link' para permitir guardado
            target_vacante = {
                "Título": titulo,
                "Empresa": empresa,
                "Ubicación": "Manual",
                "URL": "Texto Pegado",
                "Descripción": desc_full,
                "Match %": "Nuevo",
                "_row_idx": None
            }
            break # Exit menu loop to process
    
        else:
            try:
                sel = int(opcion_raw)
                target_vacante = top_n[sel-1]
                break # Exit menu loop to process
            except (ValueError, IndexError):
                print("❌ Opción inválida. Intenta de nuevo.")
                # Loop continues automatically

    # Procesar
    pack_generado = procesar_vacante_seleccionada(target_vacante, sheet)
    
    # Iniciar Chat
    print("\n💬 Iniciando Chat con el Asesor (Modo Elite)...")
    chat_session = iniciar_chat(target_vacante)
    
    # Primera interacción automática para obtener el veredicto
    try:
        # Enviamos un "Hola" o simplemente esperamos, pero como el history tiene el prompt del usuario como último mensaje 'user',
        # el modelo debería responder inmediatamente al prompt del sistema/usuario.
        # PERO: client.chats.create con history NO genera respuesta automática. Hay que enviar un mensaje.
        # OJO: En mi implementación de iniciar_chat puse el prompt como 'user' history. 
        # Para gatillar la respuesta, debo enviar algo o cambiar el history.
        # Mejor estrategia: Enviar el prompt como primer mensaje sendMessage.
        
        # En `iniciar_chat` (versión anterior modificada) lo metí en history. 
        # Si lo dejo en history, tengo que enviar un input vacio o "Analiza".
        pass 
    except:
        pass
        
    print(f"\n🤖 Asesor: Analizando '{target_vacante.get('Título')}' contra tu CV...")
    
    # Truco: Enviamos un token para disparar la respuesta al prompt de contexto si es necesario, 
    # O simplemente imprimimos la respuesta inicial.
    # En la API de Google GenAI, si el último mensaje es User, el modelo espera.
    # Vamos a enviar "Dame el veredicto" para asegurar.
    try:
        resp = chat_session.send_message("Dame el veredicto según las instrucciones.")
        print(f"\n{resp.text}")
    except Exception as e:
        print(f"Error obteniendo respuesta inicial: {e}")
        
        while True:
            user_input = input("\n👤 Tú: ")
            if user_input.lower() in ["salir", "exit", "chau"]:
                print("👋 ¡Éxito en tu postulación!")
                break
            
            archivo_adjunto = None
            mensaje_usuario = user_input
            
            # Detectar comando /adjuntar o /foto
            if user_input.startswith(("/adjuntar", "/foto", "/attach")):
                parts = user_input.split(" ", 1)
                if len(parts) > 1:
                    path_raw = parts[1].strip()
                    # Limpiar comillas si el usuario arrastró el archivo
                    path_raw = path_raw.replace('"', '').replace("'", "")
                    archivo_adjunto = path_raw
                    mensaje_usuario = "He adjuntado un archivo para que lo analices."
                    print(f"📎 Adjuntando: {archivo_adjunto}")
                else:
                    print("⚠️ Uso: /adjuntar <ruta_del_archivo>")
                    continue

            try:
                if archivo_adjunto:
                    resp_text = enviar_mensaje_multimodal(chat_session, mensaje_usuario, archivo_adjunto)
                else:
                    resp = chat_session.send_message(mensaje_usuario)
                    resp_text = resp.text
                    
                print(f"\n🤖 Asesor: {resp_text}")
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
