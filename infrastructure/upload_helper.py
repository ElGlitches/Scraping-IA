def preparar_archivo(path: str):
    """
    Lee un archivo local y retorna un objeto Part de genai para enviar.
    Soporta imágenes, PDFs y texto plano.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encuentra el archivo: {path}")

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg", 
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".csv": "text/csv"
    }
    
    ext = os.path.splitext(path)[1].lower()
    mime_type = mime_types.get(ext, "application/octet-stream")
    
    with open(path, "rb") as f:
        data = f.read()
        
    return genai.types.Part.from_bytes(data=data, mime_type=mime_type)

def enviar_mensaje_multimodal(chat, texto: str, archivo_path: str = None):
    """
    Envía un mensaje al chat, opcionalmente con un archivo adjunto.
    """
    parts = []
    if texto:
        parts.append(genai.types.Part.from_text(text=texto))
        
    if archivo_path:
        try:
            file_part = preparar_archivo(archivo_path)
            parts.append(file_part)
        except Exception as e:
            return f"❌ Error adjuntando archivo: {e}"
            
    try:
        response = chat.send_message(parts)
        return response.text
    except Exception as e:
        return f"❌ Error enviando mensaje: {e}"
