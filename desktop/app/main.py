# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Main Entry Point
Ponto de entrada principal da aplicacao
"""

import sys
import asyncio
import signal
import argparse
from pathlib import Path
from typing import Optional

# Adiciona diretorio pai ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_config, save_config, config_manager, APP_NAME, APP_VERSION
from app.utils.logger import setup_logging, get_logger
from app.services.camera_discovery import CameraDiscoveryService
from app.services.process_manager import ProcessManager, ProcessState
from app.services.disk_manager import DiskManager, AlertLevel
from app.services.auto_start import AutoStartManager, AutoStartMethod
from app.ui.main_window import MainWindow
from app.ui.system_tray import SystemTrayIcon, TrayStatus

logger = get_logger("main")


class DesktopManager:
    """
    Gerenciador principal do Desktop Manager.
    Coordena todos os servicos e a interface.
    """

    def __init__(
        self,
        minimized: bool = False,
        no_tray: bool = False,
        debug: bool = False
    ):
        """
        Inicializa o Desktop Manager.

        Args:
            minimized: Se deve iniciar minimizado (apenas tray)
            no_tray: Se deve desabilitar system tray
            debug: Modo de debug
        """
        self.minimized = minimized
        self.no_tray = no_tray
        self.debug = debug

        # Carrega configuracao
        self.config = get_config()

        # Configura logging
        log_level = "DEBUG" if debug else self.config.logging.level
        setup_logging(log_level=log_level)

        # Servicos
        self.camera_discovery: Optional[CameraDiscoveryService] = None
        self.process_manager: Optional[ProcessManager] = None
        self.disk_manager: Optional[DiskManager] = None
        self.auto_start: Optional[AutoStartManager] = None

        # UI
        self.main_window: Optional[MainWindow] = None
        self.system_tray: Optional[SystemTrayIcon] = None

        # Estado
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def initialize(self) -> bool:
        """
        Inicializa todos os componentes.

        Returns:
            True se inicializou com sucesso
        """
        logger.info(f"Inicializando {APP_NAME} v{APP_VERSION}...")

        try:
            # Camera Discovery Service
            self.camera_discovery = CameraDiscoveryService(
                onvif_enabled=self.config.discovery.onvif_enabled,
                ssdp_enabled=self.config.discovery.ssdp_enabled,
                scan_timeout=self.config.discovery.scan_timeout
            )

            # Process Manager
            self.process_manager = ProcessManager(
                host=self.config.server.host,
                port=self.config.server.port,
                auto_restart=self.config.server.auto_restart,
                restart_delay=self.config.server.restart_delay,
                health_check_interval=self.config.server.health_check_interval
            )

            # Callback para mudancas de estado do backend
            self.process_manager.add_state_callback(self._on_backend_state_change)

            # Disk Manager
            self.disk_manager = DiskManager(
                recordings_dir=self.config.storage.recordings_dir,
                max_storage_gb=self.config.storage.max_storage_gb,
                min_free_space_gb=self.config.storage.min_free_space_gb,
                check_interval=self.config.storage.check_interval,
                warning_threshold=self.config.storage.warning_threshold_percent,
                critical_threshold=self.config.storage.critical_threshold_percent
            )

            # Callback para alertas de disco
            self.disk_manager.add_alert_callback(self._on_disk_alert)

            # Auto Start Manager
            self.auto_start = AutoStartManager()

            # System Tray
            if not self.no_tray and self.config.ui.system_tray_enabled:
                self.system_tray = SystemTrayIcon(
                    on_open=self._on_tray_open,
                    on_settings=self._on_tray_settings,
                    on_quit=self._on_tray_quit
                )

                # Registra callbacks do tray
                self.system_tray.register_callback("start_backend", self._on_start_backend)
                self.system_tray.register_callback("stop_backend", self._on_stop_backend)
                self.system_tray.register_callback("discover", self._on_discover_cameras)

            # Main Window (CLI)
            self.main_window = MainWindow()
            self._register_cli_callbacks()

            logger.info("Componentes inicializados com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar componentes: {e}")
            return False

    def _register_cli_callbacks(self) -> None:
        """Registra callbacks para comandos CLI."""
        if not self.main_window:
            return

        self.main_window.register_callback("status", self._cmd_status)
        self.main_window.register_callback("cameras", self._cmd_cameras)
        self.main_window.register_callback("discover", self._cmd_discover)
        self.main_window.register_callback("start", self._cmd_start)
        self.main_window.register_callback("stop", self._cmd_stop)
        self.main_window.register_callback("restart", self._cmd_restart)
        self.main_window.register_callback("disk", self._cmd_disk)
        self.main_window.register_callback("cleanup", self._cmd_cleanup)
        self.main_window.register_callback("config", self._cmd_config)
        self.main_window.register_callback("autostart", self._cmd_autostart)

    async def start(self) -> None:
        """Inicia a aplicacao."""
        self._running = True
        self._loop = asyncio.get_event_loop()

        logger.info("Iniciando Desktop Manager...")

        # Inicia system tray
        if self.system_tray:
            if self.system_tray.start():
                logger.info("System tray iniciado")
            else:
                logger.warning("Falha ao iniciar system tray")

        # Inicia monitoramento de disco
        await self.disk_manager.start_monitoring()

        # Inicia descoberta periodica de cameras
        await self.camera_discovery.start_periodic_scan(
            interval=self.config.discovery.scan_interval
        )

        # Primeira descoberta de cameras
        logger.info("Executando descoberta inicial de cameras...")
        await self.camera_discovery.scan_once()

        # Atualiza status do tray
        self._update_tray_status()

        # Interface interativa ou minimizado
        if self.minimized:
            logger.info("Iniciado em modo minimizado")
            # Mantem rodando em background
            try:
                while self._running:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
        else:
            # Executa interface CLI
            await self.main_window.run_interactive()

    async def stop(self) -> None:
        """Para a aplicacao."""
        logger.info("Encerrando Desktop Manager...")
        self._running = False

        # Para servicos
        if self.camera_discovery:
            await self.camera_discovery.stop_periodic_scan()

        if self.disk_manager:
            await self.disk_manager.stop_monitoring()

        if self.process_manager and self.process_manager.is_running:
            await self.process_manager.stop()

        # Para UI
        if self.system_tray:
            self.system_tray.stop()

        if self.main_window:
            self.main_window.stop()

        logger.info("Desktop Manager encerrado")

    def _update_tray_status(self) -> None:
        """Atualiza status do system tray."""
        if not self.system_tray:
            return

        backend_running = self.process_manager.is_running if self.process_manager else False
        camera_count = len(self.camera_discovery.cameras) if self.camera_discovery else 0

        self.system_tray.update_status(
            backend_running=backend_running,
            camera_count=camera_count
        )

    def _on_backend_state_change(self, state: ProcessState) -> None:
        """Callback para mudanca de estado do backend."""
        logger.info(f"Estado do backend: {state.value}")

        if self.system_tray:
            self.system_tray.update_from_process_state(state)

            # Notificacao
            if state == ProcessState.CRASHED:
                self.system_tray.show_notification(
                    "Backend",
                    "O backend parou inesperadamente"
                )
            elif state == ProcessState.RUNNING:
                self.system_tray.show_notification(
                    "Backend",
                    "Backend iniciado com sucesso"
                )

    def _on_disk_alert(self, level: AlertLevel, usage) -> None:
        """Callback para alertas de disco."""
        if level == AlertLevel.WARNING:
            logger.warning(f"Espaco em disco baixo: {usage.percent_used:.1f}% usado")
            if self.system_tray:
                self.system_tray.show_notification(
                    "Espaco em disco",
                    f"Atencao: {usage.percent_used:.1f}% do disco em uso"
                )
        elif level == AlertLevel.CRITICAL:
            logger.error(f"Espaco em disco critico: {usage.percent_used:.1f}% usado")
            if self.system_tray:
                self.system_tray.show_notification(
                    "Espaco em disco",
                    f"CRITICO: {usage.percent_used:.1f}% do disco em uso!"
                )

    # Callbacks do System Tray
    def _on_tray_open(self) -> None:
        """Abre a interface principal."""
        logger.debug("Tray: Abrir interface")
        # Em modo GUI, abriria a janela
        # Em modo CLI, nao faz nada

    def _on_tray_settings(self) -> None:
        """Abre configuracoes."""
        logger.debug("Tray: Configuracoes")

    def _on_tray_quit(self) -> None:
        """Encerra a aplicacao."""
        logger.debug("Tray: Sair")
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _on_start_backend(self) -> None:
        """Inicia o backend via tray."""
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self.process_manager.start(),
                self._loop
            )

    def _on_stop_backend(self) -> None:
        """Para o backend via tray."""
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self.process_manager.stop(),
                self._loop
            )

    def _on_discover_cameras(self) -> None:
        """Descobre cameras via tray."""
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self.camera_discovery.scan_once(),
                self._loop
            )

    # Comandos CLI
    async def _cmd_status(self) -> None:
        """Comando: status"""
        backend_status = self.process_manager.get_status_dict()
        disk_status = self.disk_manager.get_status()
        cameras = self.camera_discovery.cameras

        self.main_window.show_status(backend_status, disk_status, cameras)

    async def _cmd_cameras(self) -> None:
        """Comando: cameras"""
        cameras = self.camera_discovery.cameras
        self.main_window.show_cameras(cameras)
        self.main_window.show_message(f"Total: {len(cameras)} cameras", "info")

    async def _cmd_discover(self) -> None:
        """Comando: discover"""
        self.main_window.show_message("Iniciando descoberta de cameras...", "info")

        async def scan():
            return await self.camera_discovery.scan_once()

        cameras = await self.main_window.cli.show_progress(
            "Procurando cameras na rede",
            scan
        )

        self.main_window.show_cameras(cameras)
        self.main_window.show_message(f"Descoberta concluida: {len(cameras)} cameras", "success")
        self._update_tray_status()

    async def _cmd_start(self) -> None:
        """Comando: start"""
        if self.process_manager.is_running:
            self.main_window.show_message("Backend ja esta em execucao", "warning")
            return

        self.main_window.show_message("Iniciando backend...", "info")

        if await self.process_manager.start():
            self.main_window.show_message("Backend iniciado com sucesso", "success")
        else:
            self.main_window.show_message(
                f"Falha ao iniciar: {self.process_manager.info.last_error}",
                "error"
            )

        self._update_tray_status()

    async def _cmd_stop(self) -> None:
        """Comando: stop"""
        if not self.process_manager.is_running:
            self.main_window.show_message("Backend nao esta em execucao", "warning")
            return

        self.main_window.show_message("Parando backend...", "info")

        if await self.process_manager.stop():
            self.main_window.show_message("Backend parado", "success")
        else:
            self.main_window.show_message("Falha ao parar backend", "error")

        self._update_tray_status()

    async def _cmd_restart(self) -> None:
        """Comando: restart"""
        self.main_window.show_message("Reiniciando backend...", "info")

        if await self.process_manager.restart():
            self.main_window.show_message("Backend reiniciado", "success")
        else:
            self.main_window.show_message("Falha ao reiniciar", "error")

        self._update_tray_status()

    async def _cmd_disk(self) -> None:
        """Comando: disk"""
        status = self.disk_manager.get_status()
        report = await self.disk_manager.get_storage_report()

        self.main_window.cli.print(f"\n[bold]Armazenamento:[/bold]")
        self.main_window.cli.print(f"  Disco total: {status['disk']['total_gb']:.1f} GB")
        self.main_window.cli.print(f"  Disco usado: {status['disk']['used_gb']:.1f} GB ({status['disk']['percent_used']:.1f}%)")
        self.main_window.cli.print(f"  Disco livre: {status['disk']['free_gb']:.1f} GB")
        self.main_window.cli.print(f"\n[bold]Gravacoes:[/bold]")
        self.main_window.cli.print(f"  Total: {report['total_files']} arquivos")
        self.main_window.cli.print(f"  Tamanho: {report['total_size_gb']:.1f} GB")
        self.main_window.cli.print(f"  Media por arquivo: {report['average_file_size_mb']:.1f} MB")

        if report['oldest_file']['path']:
            self.main_window.cli.print(f"  Mais antigo: {report['oldest_file']['age_days']:.1f} dias")

    async def _cmd_cleanup(self) -> None:
        """Comando: cleanup"""
        if not self.main_window.cli.confirm("Executar limpeza de gravacoes antigas?"):
            return

        self.main_window.show_message("Executando limpeza...", "info")
        deleted = await self.disk_manager.cleanup(force=True)
        self.main_window.show_message(f"Limpeza concluida: {deleted} arquivos removidos", "success")

    async def _cmd_config(self) -> None:
        """Comando: config"""
        import json
        config_dict = self.config.to_dict()
        self.main_window.cli.print("\n[bold]Configuracao atual:[/bold]")
        self.main_window.cli.print(json.dumps(config_dict, indent=2))

    async def _cmd_autostart(self) -> None:
        """Comando: autostart"""
        status = self.auto_start.get_status()

        self.main_window.cli.print("\n[bold]Auto-Start:[/bold]")
        self.main_window.cli.print(f"  Executando como admin: {status['is_admin']}")

        for method, info in status['methods'].items():
            state = "[green]Ativo[/green]" if info['enabled'] else "[red]Inativo[/red]"
            available = "Disponivel" if info['available'] else "Indisponivel"
            self.main_window.cli.print(f"  {method}: {state} ({available})")

        # Opcao para alterar
        if self.main_window.cli.confirm("\nDeseja alterar configuracao de auto-start?"):
            if self.auto_start.is_enabled():
                if self.main_window.cli.confirm("Desabilitar auto-start?"):
                    self.auto_start.disable()
                    self.main_window.show_message("Auto-start desabilitado", "success")
            else:
                if self.main_window.cli.confirm("Habilitar auto-start?"):
                    if self.auto_start.enable(start_minimized=True):
                        self.main_window.show_message("Auto-start habilitado", "success")
                    else:
                        self.main_window.show_message("Falha ao habilitar auto-start", "error")


def parse_args():
    """Parse argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} Desktop Manager v{APP_VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--minimized", "-m",
        action="store_true",
        help="Inicia minimizado (apenas system tray)"
    )

    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Desabilita icone na bandeja do sistema"
    )

    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Modo de debug (mais logs)"
    )

    parser.add_argument(
        "--service",
        action="store_true",
        help="Modo de servico (sem interface)"
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"{APP_NAME} v{APP_VERSION}"
    )

    return parser.parse_args()


async def main_async(args) -> int:
    """
    Funcao principal assincrona.

    Args:
        args: Argumentos parseados

    Returns:
        Codigo de saida
    """
    # Cria e inicializa o manager
    manager = DesktopManager(
        minimized=args.minimized or args.service,
        no_tray=args.no_tray or args.service,
        debug=args.debug
    )

    if not await manager.initialize():
        logger.error("Falha ao inicializar Desktop Manager")
        return 1

    # Configura handler de sinais
    def signal_handler():
        logger.info("Sinal de interrupcao recebido")
        asyncio.create_task(manager.stop())

    if sys.platform != "win32":
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

    try:
        await manager.start()
        return 0

    except KeyboardInterrupt:
        logger.info("Interrupcao do usuario")
        await manager.stop()
        return 0

    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        await manager.stop()
        return 1


def main() -> int:
    """
    Ponto de entrada principal.

    Returns:
        Codigo de saida
    """
    args = parse_args()

    try:
        # Windows: usa WindowsSelectorEventLoopPolicy
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        return asyncio.run(main_async(args))

    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Erro fatal: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
