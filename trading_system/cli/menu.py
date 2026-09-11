import os
import sys
import time
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich import box

# Set API Base URL (adjust if running in Docker with different port mapping)
API_BASE = "http://localhost:8000/api"

console = Console()

def get_state():
    try:
        resp = requests.get(f"{API_BASE}/state", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None

def trigger_manual_trade(signal_type: str):
    try:
        resp = requests.post(f"{API_BASE}/trade/manual?signal_type={signal_type}")
        console.print(f"[bold green]{resp.json().get('message')}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

def force_exit():
    try:
        resp = requests.post(f"{API_BASE}/trade/exit")
        console.print(f"[bold yellow]{resp.json().get('message')}[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

def toggle_sim(enabled: bool):
    try:
        resp = requests.post(f"{API_BASE}/simulation/toggle?enabled={str(enabled).lower()}")
        mode_str = "SIMULATION (Dry Run)" if enabled else "LIVE (Real Money)"
        color = "cyan" if enabled else "bold red"
        console.print(f"\n[bold {color}]>>> ENGINE MODE CHANGED: {mode_str} <<<[/bold {color}]\n")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

def trigger_manual_trade(signal_type: str):
    try:
        console.print(f"\n[bold yellow]Triggering {signal_type}...[/bold yellow]")
        requests.post(f"{API_BASE}/trade/manual?signal_type={signal_type}")
        console.print("[bold green]Signal sent to engine.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

def recover_levels():
    try:
        with console.status("[bold yellow]Fetching historical ORB levels...[/bold yellow]"):
            resp = requests.post(f"{API_BASE}/recovery/orb")
            if resp.status_code == 200:
                console.print(f"[bold green]{resp.json().get('message')}[/bold green]")
            else:
                console.print(f"[bold red]Recovery Failed: {resp.json().get('detail')}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

def kill_bot():
    try:
        requests.post(f"{API_BASE}/kill")
        console.print("[bold red]Kill Switch Sent. Shutting down CLI...[/bold red]")
        sys.exit(0)
    except Exception:
        sys.exit(0)

def generate_dashboard(state):
    if not state:
        return Panel("[bold red]ERROR: Could not connect to Trading Engine[/bold red]", title="F&O Automation Status", border_style="red")

    position = state.get("position", {})
    risk = state.get("risk", {})
    levels = state.get("orb_levels", {})
    
    # Header Table
    header = Table(show_header=False, box=box.SIMPLE)
    header.add_row("Bot State:", f"[bold cyan]{state.get('engine_state', 'UNKNOWN')}[/bold cyan]")
    
    # Simulation Badge
    sim_mode = risk.get("is_simulation", True) # Default to true for safety
    header.add_row("Mode:", "[bold magenta]SIMULATION (DRY RUN)[/bold magenta]" if sim_mode else "[bold red]LIVE TRADING[/bold red]")

    # Levels Table
    lvls_table = Table(title="ORB Levels (9:15-9:45)", box=box.ROUNDED)
    lvls_table.add_column("Level Type", style="dim")
    lvls_table.add_column("Price", justify="right")
    lvls_table.add_row("Resistance (High)", f"[green]{levels.get('opening_high', 0.0)}[/green]")
    lvls_table.add_row("Support (Low)", f"[red]{levels.get('opening_low', 0.0)}[/red]")

    # Position Table
    pos_table = Table(title="Current Position", box=box.HEAVY)
    pos_table.add_column("Symbol")
    pos_table.add_column("Type")
    pos_table.add_column("Entry", justify="right")
    pos_table.add_column("LTP", justify="right")
    pos_table.add_column("P&L", justify="right")
    
    symbol = position.get("tradingsymbol", "NONE")
    pnl = position.get("unrealized_pnl", 0.0)
    pnl_style = "green" if pnl >= 0 else "red"
    
    pos_table.add_row(
        symbol,
        position.get("option_type", "-"),
        f"{position.get('entry_price', 0.0):.2f}",
        f"{position.get('last_price', 0.0):.2f}",
        f"[{pnl_style}]{pnl:.2f}[/{pnl_style}]"
    )

    layout = Table.grid()
    layout.add_row(header)
    layout.add_row(lvls_table)
    layout.add_row(pos_table)
    
    return Panel(layout, title=" Trading Engine Control Panel ", border_style="blue", padding=(1, 2))

def main():
    console.clear()
    console.print("[bold yellow]Initalizing F&O Control Menu...[/bold yellow]")
    
    while True:
        state = get_state()
        console.clear()
        console.print(generate_dashboard(state))
        
        console.print("\n[bold]Manual Controls:[/bold]")
        console.print("  [1] Refresh Status")
        console.print("  [2] Force BUY CE (Manual Trigger)")
        console.print("  [3] Force BUY PE (Manual Trigger)")
        console.print("  [4] Manual Exit (Square Off)")
        console.print("  [5] Enable Simulation Mode (Dry Run)")
        console.print("  [6] Disable Simulation Mode (LIVE)")
        console.print("  [7] Recover Today's ORB Levels")
        console.print("  [0] KILL SWITCH (Halt & Exit)")
        console.print("  [q] Quit CLI (Engine keeps running)")
        
        choice = console.input("\nSelect an option: ").strip().lower()
        
        if choice == "1":
            continue
        elif choice == "2":
            trigger_manual_trade("BUY_CE")
            time.sleep(1)
        elif choice == "3":
            trigger_manual_trade("BUY_PE")
            time.sleep(1)
        elif choice == "4":
            if console.input("Confirm Exit Position? (y/n): ").lower() == 'y':
                force_exit()
                time.sleep(1)
        elif choice == "5":
            toggle_sim(True)
            time.sleep(1)
        elif choice == "6":
            if console.input("WARNING: This enables LIVE orders. Confirm? (y/n): ").lower() == 'y':
                toggle_sim(False)
                time.sleep(1)
        elif choice == "7":
            recover_levels()
            time.sleep(2)
        elif choice == "0":
            if console.input("[BOLD RED]ACTIVATE KILL SWITCH? (y/n): [/BOLD RED]").lower() == 'y':
                kill_bot()
        elif choice == "q":
            console.print("Exiting CLI...")
            break
        else:
            console.print("[red]Invalid choice[/red]")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
