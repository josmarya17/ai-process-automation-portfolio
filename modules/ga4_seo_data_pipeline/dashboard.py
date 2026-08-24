import os
import sys
import json
import time
import pandas as pd
import config
from data_extractor import ClientManager
from report_generator import SheetsManager
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich import box
import subprocess
import threading

console = Console()
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "STATE.json")

def initialize_state(client_name=""):
    state = {
        "client": client_name,
        "status": "INITIALIZING",
        "progress": 0,
        "message": "Esperando inicio...",
        "metrics": {},
        "analysis": "",
        "done": False,
        "error": None
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)
    return state

def read_state():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    layout["main"].split_row(
        Layout(name="side", ratio=1),
        Layout(name="body", ratio=2)
    )
    return layout

class Header:
    def __rich__(self):
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row("[bold magenta]ANTIGRAVITY COMMAND CENTER[/bold magenta] [white]|[/white] [bold cyan]WAC SEO AUTOMATION[/bold cyan]")
        return Panel(grid, style="white on blue")

def get_active_clients():
    try:
        client_mgr = ClientManager(account_key='wac')
        creds = client_mgr.get_creds()
        sheets_mgr = SheetsManager(creds)
        df = sheets_mgr.read_config_sheet(config.SHEET_ID_PROPIEDADES, config.TAB_NAME_PROPIEDADES)
        if config.COL_ACTIVO in df.columns:
            df = df[df[config.COL_ACTIVO].astype(str).str.strip().upper() == 'TRUE']
        return df
    except Exception as e:
        console.print(f"[red]Error cargando clientes: {e}[/red]")
        return pd.DataFrame()

def run_main_process(client_name):
    # Lanzar main.py en segundo plano pasando el modo full
    subprocess.run(
        [sys.executable, "main.py", "--mode", "full", "--client", client_name],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

def main_dashboard():
    while True:
        console.clear()
        console.print(Panel("[bold yellow]Cargando Clientes Activos desde Google Sheets...[/bold yellow]", expand=False))
        df = get_active_clients()
        
        if df.empty:
            console.print("[red]❌ No se encontraron clientes activos.[/red]")
            time.sleep(3)
            break
            
        clients = df[config.COL_CLIENTE].tolist()
        
        table = Table(title="[bold cyan]Selección de Cliente[/bold cyan]", box=box.ROUNDED)
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Nombre del Cliente", style="white")
        
        for i, client in enumerate(clients, 1):
            table.add_row(str(i), client)
        
        console.print(table)
        console.print("\n[bold yellow]0.[/bold yellow] SALIR")
        
        choice = console.input("\n[green]Selecciona un ID: [/green]")
        
        if choice == '0':
            break
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(clients):
                selected_client = clients[idx]
                state = initialize_state(selected_client)
                
                # Iniciar proceso en hilo separado
                proc_thread = threading.Thread(target=run_main_process, args=(selected_client,), daemon=True)
                proc_thread.start()
                
                # Interfaz Live
                layout = make_layout()
                layout["header"].update(Header())
                
                with Live(layout, refresh_per_second=2, screen=True):
                    while True:
                        current_state = read_state()
                        if not current_state: break
                        
                        # Panel Izquierdo: Métricas y Datos
                        side_table = Table(title="[bold green]Métricas Técnicas[/bold green]", expand=True)
                        side_table.add_column("Dato", style="cyan")
                        side_table.add_column("Valor", style="white")
                        
                        metrics = current_state.get("metrics", {})
                        for key, val in metrics.items():
                            side_table.add_row(key, str(val))
                        
                        layout["side"].update(Panel(side_table, title="[bold cyan]Contexto GSC/GA4[/bold cyan]"))
                        
                        # Cuerpo Central: Análisis e Informe
                        analysis_text = current_state.get("analysis", "")
                        msg = current_state.get("message", "")
                        
                        if not analysis_text:
                            if "Esperando que Antigravity" in msg:
                                analysis_text = f"🤖 [bold magenta]ANTIGRAVITY ESTÁ TRABAJANDO...[/bold magenta]\n\n[cyan]Redactando informe senior e insertando en Google Doc automáticamente.[/cyan]\n\n[dim]Espera unos segundos, verás el informe aparecer aquí pronto.[/dim]"
                            else:
                                analysis_text = f"🤖 [yellow]{msg if msg else 'Iniciando...'}[/yellow]\n\n[dim]Extrayendo datos de Google Search Console y Generando reportes Looker PDF...[/dim]"
                        
                        layout["body"].update(Panel(analysis_text, title=f"[bold green]Centro de Análisis Senior: {selected_client}[/bold green]"))
                        
                        # Footer: Progreso
                        prog = current_state.get("progress", 0)
                        layout["footer"].update(Panel(f"[bold cyan]Progreso:[/bold cyan] {prog}% - {msg}", style="white on black"))
                        
                        if current_state.get("done"):
                            time.sleep(1)
                            # Mostramos el análisis final antes de salir si existe
                            if current_state.get("analysis"):
                                layout["body"].update(Panel(current_state["analysis"], title=f"[bold green]✨ Informe Publicado exitosamente[/bold green]"))
                                time.sleep(4)
                            break
                        
                        if current_state.get("error"):
                            layout["body"].update(Panel(f"[red]Error detectado:[/red] {current_state['error']}", title="[bold red]Error en el Proceso[/bold red]"))
                            time.sleep(5)
                            break
                        
                        time.sleep(0.5)
                
                console.print("\n[bold green]✨ CICLO COMPLETADO EXITOSAMENTE[/bold green]")
                if os.path.exists(STATE_FILE): 
                    try: os.remove(STATE_FILE)
                    except: pass
                input("\nPresiona Enter para continuar...")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            time.sleep(2)

if __name__ == "__main__":
    main_dashboard()
