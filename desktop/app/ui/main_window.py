# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Main Window
Interface principal (CLI inicialmente, preparada para GUI)
"""

import asyncio
import sys
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False
    click = None

from ..utils.logger import get_logger, LoggerMixin
from ..services.process_manager import ProcessState
from ..services.camera_discovery import DiscoveredCamera, CameraProtocol
from ..services.disk_manager import DiskUsage, AlertLevel

logger = get_logger("main_window")


class CLIInterface(LoggerMixin):
    """
    Interface de linha de comando usando Rich.
    Fornece uma interface rica e interativa no terminal.
    """

    def __init__(self):
        """Inicializa a interface CLI."""
        self.console = Console() if RICH_AVAILABLE else None
        self._running = False

    def print(self, message: str, style: str = None) -> None:
        """
        Imprime mensagem no console.

        Args:
            message: Mensagem a imprimir
            style: Estilo Rich (bold, red, green, etc)
        """
        if self.console:
            self.console.print(message, style=style)
        else:
            print(message)

    def print_header(self) -> None:
        """Imprime cabecalho da aplicacao."""
        header = """
   _____ _          _____                  ____   _____
  / ____| |        / ____|                / __ \\ / ____|
 | (___ | | ___   | |     __ _ _ __ ___  | |  | | (___
  \\___ \\| |/ / |  | |    / _` | '_ ` _ \\ | |  | |\\___ \\
  ____) |   <| |__| |___| (_| | | | | | || |__| |____) |
 |_____/|_|\\_\\____|______\\__,_|_| |_| |_| \\____/|_____/

        Desktop Manager v1.0.0
"""
        if self.console:
            self.console.print(Panel(
                header,
                title="[bold cyan]SkyCamOS[/bold cyan]",
                border_style="cyan"
            ))
        else:
            print(header)

    def print_status(
        self,
        backend_status: Dict[str, Any],
        disk_status: Dict[str, Any],
        cameras: List[DiscoveredCamera]
    ) -> None:
        """
        Imprime status geral do sistema.

        Args:
            backend_status: Status do backend
            disk_status: Status do disco
            cameras: Lista de cameras
        """
        if not self.console:
            self._print_status_plain(backend_status, disk_status, cameras)
            return

        # Cria layout
        layout = Layout()
        layout.split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )

        # Painel de Backend
        backend_table = Table(show_header=False, box=box.SIMPLE)
        backend_table.add_column("Item", style="cyan")
        backend_table.add_column("Valor")

        state = backend_status.get('state', 'unknown')
        state_color = {
            'running': 'green',
            'stopped': 'red',
            'starting': 'yellow',
            'crashed': 'red bold'
        }.get(state, 'white')

        backend_table.add_row("Status", f"[{state_color}]{state.upper()}[/{state_color}]")
        backend_table.add_row("PID", str(backend_status.get('pid', 'N/A')))
        backend_table.add_row("Porta", str(backend_status.get('port', 'N/A')))
        backend_table.add_row("CPU", f"{backend_status.get('cpu_percent', 0):.1f}%")
        backend_table.add_row("Memoria", f"{backend_status.get('memory_mb', 0):.1f} MB")
        backend_table.add_row("Reinicializacoes", str(backend_status.get('restart_count', 0)))

        # Painel de Disco
        disk_table = Table(show_header=False, box=box.SIMPLE)
        disk_table.add_column("Item", style="cyan")
        disk_table.add_column("Valor")

        disk_info = disk_status.get('disk', {})
        alert = disk_info.get('alert_level', 'ok')
        alert_color = {
            'ok': 'green',
            'warning': 'yellow',
            'critical': 'red',
            'full': 'red bold'
        }.get(alert, 'white')

        disk_table.add_row("Status", f"[{alert_color}]{alert.upper()}[/{alert_color}]")
        disk_table.add_row("Total", f"{disk_info.get('total_gb', 0):.1f} GB")
        disk_table.add_row("Usado", f"{disk_info.get('used_gb', 0):.1f} GB")
        disk_table.add_row("Livre", f"{disk_info.get('free_gb', 0):.1f} GB")
        disk_table.add_row("Uso", f"{disk_info.get('percent_used', 0):.1f}%")

        recordings = disk_status.get('recordings', {})
        disk_table.add_row("Gravacoes", f"{recordings.get('size_gb', 0):.1f} GB")
        disk_table.add_row("Arquivos", str(recordings.get('file_count', 0)))

        # Exibe paineis
        self.console.print(Panel(backend_table, title="[bold]Backend[/bold]", border_style="blue"))
        self.console.print(Panel(disk_table, title="[bold]Armazenamento[/bold]", border_style="blue"))

        # Tabela de cameras
        self.print_cameras_table(cameras)

    def _print_status_plain(
        self,
        backend_status: Dict[str, Any],
        disk_status: Dict[str, Any],
        cameras: List[DiscoveredCamera]
    ) -> None:
        """Imprime status em formato texto simples."""
        print("\n=== Backend Status ===")
        print(f"  Estado: {backend_status.get('state', 'unknown')}")
        print(f"  PID: {backend_status.get('pid', 'N/A')}")
        print(f"  Porta: {backend_status.get('port', 'N/A')}")

        print("\n=== Disco ===")
        disk = disk_status.get('disk', {})
        print(f"  Livre: {disk.get('free_gb', 0):.1f} GB")
        print(f"  Uso: {disk.get('percent_used', 0):.1f}%")

        print("\n=== Cameras ===")
        print(f"  Total: {len(cameras)}")
        for cam in cameras:
            print(f"  - {cam.ip_address}: {cam.manufacturer} {cam.model}")

    def print_cameras_table(self, cameras: List[DiscoveredCamera]) -> None:
        """
        Imprime tabela de cameras.

        Args:
            cameras: Lista de cameras descobertas
        """
        if not self.console:
            for cam in cameras:
                print(f"  {cam.ip_address}:{cam.port} - {cam.manufacturer} {cam.model}")
            return

        table = Table(
            title="Cameras Descobertas",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED
        )

        table.add_column("IP", style="cyan")
        table.add_column("Porta")
        table.add_column("Protocolo")
        table.add_column("Fabricante", style="green")
        table.add_column("Modelo")
        table.add_column("Status")
        table.add_column("Ultima vez visto")

        for cam in cameras:
            status = "[green]Online[/green]" if cam.is_online else "[red]Offline[/red]"
            last_seen = cam.last_seen.strftime("%H:%M:%S") if cam.last_seen else "N/A"

            table.add_row(
                cam.ip_address,
                str(cam.port),
                cam.protocol.value.upper(),
                cam.manufacturer,
                cam.model,
                status,
                last_seen
            )

        if not cameras:
            table.add_row(
                "[dim]Nenhuma camera encontrada[/dim]",
                "", "", "", "", "", ""
            )

        self.console.print(table)

    def print_menu(self) -> None:
        """Imprime menu de opcoes."""
        menu = """
[bold cyan]Comandos disponiveis:[/bold cyan]

  [green]status[/green]     - Exibe status do sistema
  [green]cameras[/green]    - Lista cameras descobertas
  [green]discover[/green]   - Inicia descoberta de cameras
  [green]start[/green]      - Inicia o backend
  [green]stop[/green]       - Para o backend
  [green]restart[/green]    - Reinicia o backend
  [green]disk[/green]       - Status do disco
  [green]cleanup[/green]    - Limpa gravacoes antigas
  [green]config[/green]     - Exibe configuracao
  [green]autostart[/green]  - Configura inicio automatico
  [green]help[/green]       - Exibe esta ajuda
  [green]quit[/green]       - Sai da aplicacao

"""
        if self.console:
            self.console.print(Panel(menu, title="[bold]Menu[/bold]", border_style="cyan"))
        else:
            print(menu)

    async def show_progress(self, description: str, task_func: Callable) -> Any:
        """
        Exibe progresso durante uma tarefa.

        Args:
            description: Descricao da tarefa
            task_func: Funcao async a executar

        Returns:
            Resultado da funcao
        """
        if not self.console:
            print(f"{description}...")
            return await task_func()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(description, total=None)
            result = await task_func()
            progress.update(task, completed=True)
            return result

    def print_success(self, message: str) -> None:
        """Imprime mensagem de sucesso."""
        if self.console:
            self.console.print(f"[green][OK][/green] {message}")
        else:
            print(f"[OK] {message}")

    def print_error(self, message: str) -> None:
        """Imprime mensagem de erro."""
        if self.console:
            self.console.print(f"[red][ERRO][/red] {message}")
        else:
            print(f"[ERRO] {message}")

    def print_warning(self, message: str) -> None:
        """Imprime mensagem de aviso."""
        if self.console:
            self.console.print(f"[yellow][AVISO][/yellow] {message}")
        else:
            print(f"[AVISO] {message}")

    def print_info(self, message: str) -> None:
        """Imprime mensagem informativa."""
        if self.console:
            self.console.print(f"[cyan][INFO][/cyan] {message}")
        else:
            print(f"[INFO] {message}")

    def get_input(self, prompt: str = "> ") -> str:
        """
        Obtem entrada do usuario.

        Args:
            prompt: Prompt a exibir

        Returns:
            Texto digitado
        """
        try:
            if self.console:
                return self.console.input(f"[bold cyan]{prompt}[/bold cyan]")
            return input(prompt)
        except EOFError:
            return "quit"
        except KeyboardInterrupt:
            return "quit"

    def confirm(self, message: str) -> bool:
        """
        Solicita confirmacao do usuario.

        Args:
            message: Mensagem a exibir

        Returns:
            True se confirmou
        """
        response = self.get_input(f"{message} [s/N]: ")
        return response.lower() in ('s', 'sim', 'y', 'yes')

    def clear(self) -> None:
        """Limpa a tela."""
        if self.console:
            self.console.clear()
        else:
            import os
            os.system('cls' if sys.platform == 'win32' else 'clear')


class MainWindow(LoggerMixin):
    """
    Janela principal da aplicacao.
    Atualmente implementa interface CLI, preparada para futura GUI.
    """

    def __init__(self):
        """Inicializa a janela principal."""
        self.cli = CLIInterface()
        self._running = False
        self._callbacks: Dict[str, Callable] = {}

    def register_callback(self, command: str, callback: Callable) -> None:
        """
        Registra callback para um comando.

        Args:
            command: Nome do comando
            callback: Funcao a executar
        """
        self._callbacks[command] = callback

    async def run_interactive(self) -> None:
        """Executa interface interativa."""
        self._running = True
        self.cli.clear()
        self.cli.print_header()
        self.cli.print_menu()

        while self._running:
            try:
                command = self.cli.get_input().strip().lower()

                if not command:
                    continue

                await self._handle_command(command)

            except KeyboardInterrupt:
                self.cli.print_info("Use 'quit' para sair")
            except Exception as e:
                self.cli.print_error(f"Erro: {e}")
                self.logger.error(f"Erro no comando: {e}")

    async def _handle_command(self, command: str) -> None:
        """
        Processa um comando.

        Args:
            command: Comando digitado
        """
        # Comandos internos
        if command in ('quit', 'exit', 'q'):
            self._running = False
            self.cli.print_info("Encerrando...")
            return

        if command in ('help', 'h', '?'):
            self.cli.print_menu()
            return

        if command == 'clear':
            self.cli.clear()
            return

        # Comandos com callbacks
        if command in self._callbacks:
            callback = self._callbacks[command]
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                callback()
        else:
            self.cli.print_warning(f"Comando desconhecido: {command}")
            self.cli.print_info("Digite 'help' para ver comandos disponiveis")

    def show_status(
        self,
        backend_status: Dict[str, Any],
        disk_status: Dict[str, Any],
        cameras: List[DiscoveredCamera]
    ) -> None:
        """
        Exibe status do sistema.

        Args:
            backend_status: Status do backend
            disk_status: Status do disco
            cameras: Lista de cameras
        """
        self.cli.print_status(backend_status, disk_status, cameras)

    def show_cameras(self, cameras: List[DiscoveredCamera]) -> None:
        """
        Exibe lista de cameras.

        Args:
            cameras: Lista de cameras
        """
        self.cli.print_cameras_table(cameras)

    def show_message(self, message: str, level: str = "info") -> None:
        """
        Exibe mensagem.

        Args:
            message: Mensagem
            level: Nivel (info, success, warning, error)
        """
        method = getattr(self.cli, f"print_{level}", self.cli.print_info)
        method(message)

    def stop(self) -> None:
        """Para a interface."""
        self._running = False


def create_cli_app():
    """
    Cria aplicacao CLI usando Click.

    Returns:
        Grupo de comandos Click
    """
    if not CLICK_AVAILABLE:
        return None

    @click.group()
    @click.version_option(version="1.0.0")
    def cli():
        """SkyCamOS Desktop Manager - Interface de linha de comando."""
        pass

    @cli.command()
    def status():
        """Exibe status do sistema."""
        click.echo("Status do sistema...")

    @cli.command()
    def cameras():
        """Lista cameras descobertas."""
        click.echo("Listando cameras...")

    @cli.command()
    def discover():
        """Inicia descoberta de cameras."""
        click.echo("Descobrindo cameras...")

    @cli.command()
    def start():
        """Inicia o backend."""
        click.echo("Iniciando backend...")

    @cli.command()
    def stop():
        """Para o backend."""
        click.echo("Parando backend...")

    @cli.command()
    def disk():
        """Exibe status do disco."""
        click.echo("Status do disco...")

    @cli.command()
    @click.option('--enable/--disable', default=None, help='Habilita ou desabilita')
    def autostart(enable):
        """Configura inicio automatico."""
        if enable is None:
            click.echo("Status do autostart...")
        elif enable:
            click.echo("Habilitando autostart...")
        else:
            click.echo("Desabilitando autostart...")

    return cli
