import questionary
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.align import Align
from rich.style import Style
from rich.layout import Layout
from typing import List, Dict, Any

# Global console instance with Retro Theme forces
# System 1.0 style: White text on Black background (standard terminal) 
# or strictly monochrome.
console = Console(highlight=False)

# Estilos Retro
STYLE_WINDOW_BORDER = "white"
STYLE_TITLE = "bold black on white"
STYLE_TEXT_NORMAL = "white"
STYLE_HIGHLIGHT = "reverse bold" # Invertido para selección

def mostrar_banner():
    """Muestra el banner estilo Macintosh System 1.0"""
    
    # Arte ASCII estilo Happy Mac simplificado
    happy_mac = """
      .---.
     /     \\
    |  o o  |
    |   ^   |
    |  '-'  |
     '-----' 
    """
    
    texto_sistema = Text("WELCOME TO MACINTOSH", justify="center", style="bold white")
    subtexto = Text("SYSTEM 1.0 - JOB SEARCH APP", justify="center", style="dim white")
    
    # Contenido del "About Box"
    contenido = Group(
        Align.center(Text(happy_mac, style="bold white")),
        texto_sistema,
        subtexto
    )
    
    panel = Panel(
        contenido,
        box=box.ROUNDED,  # Bordes redondeados simulando ventanas Mac
        border_style=STYLE_WINDOW_BORDER,
        title="[bold black on white] ABOUT [/bold black on white]",
        title_align="center",
        padding=(1, 4),
        width=50
    )
    
    console.print(Align.center(panel))
    console.print("\n")

def menu_principal() -> str:
    """Muestra el menú principal y retorna la opción seleccionada."""
    
    # Usamos questionary pero simulando un menú de texto plano limpio
    opcion = questionary.select(
        "SELECT AN OPTION:",
        choices=[
            "FILE -> SEARCH VACANCIES",
            "VIEW -> SHOW DATABASE",
            "SHUTDOWN"
        ],
        style=questionary.Style([
            ('qmark', 'fg:white'),       
            ('question', 'bold fg:white'), 
            ('answer', 'fg:white'),      
            ('pointer', 'fg:white bold'),     # Puntero blanco
            ('highlighted', 'bg:white fg:black'), # Selección invertida (Clásico Mac)
            ('selected', 'fg:white'),         
            ('separator', 'fg:white'),        
            ('instruction', 'fg:gray'),                
            ('text', 'fg:white'),                       
            ('disabled', 'fg:gray italic')   
        ]),
        use_indicator=True,
        pointer=">"
    ).ask()
    
    # Mapeo de vuelta a los valores esperados por el main
    if "SEARCH VACANCIES" in opcion:
        return "Buscar Vacantes"
    elif "SHOW DATABASE" in opcion:
        return "Ver Vacantes"
    elif "SHUTDOWN" in opcion:
        return "Salir"
    return "Salir"

def mostrar_ventana(titulo: str, contenido: Any, estilo_borde: str="white"):
    """Helper para dibujar 'ventanas' consistentes."""
    panel = Panel(
        contenido,
        box=box.ROUNDED, # Bordes redondeados
        border_style=estilo_borde,
        title=f"[bold black on white] {titulo.upper()} [/bold black on white]",
        title_align="center",
        padding=(1, 2)
    )
    console.print(panel)

def mostrar_tabla_resultados(vacantes: List[Dict[str, Any]], titulo: str = "Resultados"):
    """Muestra una tabla con las vacantes encontradas estilo hoja de cálculo antigua."""
    if not vacantes:
        ventana_info = Panel(
            Text("0 ITEMS FOUND", justify="center"),
            title="[bold black on white] INFO [/bold black on white]",
            border_style="white",
            box=box.ROUNDED
        )
        console.print(ventana_info)
        return

    table = Table(
        box=box.SIMPLE, # Bordes simples, sin doble línea
        show_header=True, 
        header_style="bold black on white", # Cabecera invertida
        border_style="white",
        width=100
    )
    
    table.add_column("ID", justify="right", style="white")
    table.add_column("ROLE", style="bold white")
    table.add_column("COMPANY", style="white")
    table.add_column("MATCH", justify="center", style="white")

    for idx, v in enumerate(vacantes, 1):
        match_val = v.get("match_percent", "N/A")
        match_str = f"{match_val}%" if isinstance(match_val, (int, float)) else str(match_val)
        
        # En blanco y negro no usamos colores semánticos, usamos símbolos o texto
        # Si es alto match, podríamos ponerle un asterisco o negrita
        match_display = match_str
        if isinstance(match_val, (int, float)) and match_val >= 80:
             match_display = f"★ {match_str}" 
        
        table.add_row(
            str(idx),
            v.get("titulo", "NO DATA").upper(),
            v.get("empresa", "NO DATA").upper(),
            match_display
        )

    mostrar_ventana(titulo, table)

def confirmar_accion(texto: str) -> bool:
    """Solicita confirmación al usuario estilo diálogo de sistema."""
    return questionary.confirm(
        texto.upper(),
        style=questionary.Style([
            ('qmark', 'fg:white'),
            ('question', 'bold fg:white'), 
            ('answer', 'fg:white'),
            ('instruction', 'fg:gray')
        ])
    ).ask()

def status_context(texto: str):
    """Retorna un contexto de status con spinner 'watch' o similar."""
    # El spinner 'dots' es lo más cercano a algo simple. 'line' o 'pipe' también sirven.
    # Ojalá rich tuviera el 'beachball', pero usaremos 'line' para ser retro.
    return console.status(f"[white]{texto.upper()}...[/white]", spinner="line")
