# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - System Tray
Icone na bandeja do sistema com menu de contexto
"""

import sys
import asyncio
import threading
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path
from enum import Enum

try:
    import pystray
    from pystray import MenuItem as Item, Menu
    PYSTRAY_AVAILABLE = True
except ImportError:
    pystray = None
    PYSTRAY_AVAILABLE = False

try:
    from PIL import Image, ImageDraw
    PILLOW_AVAILABLE = True
except ImportError:
    Image = None
    ImageDraw = None
    PILLOW_AVAILABLE = False

from ..utils.logger import get_logger, LoggerMixin
from ..services.process_manager import ProcessState

logger = get_logger("system_tray")


class TrayStatus(Enum):
    """Status do icone na bandeja."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    OFFLINE = "offline"


class SystemTrayIcon(LoggerMixin):
    """
    Icone na bandeja do sistema (System Tray).
    Fornece acesso rapido as funcionalidades do Desktop Manager.
    """

    # Cores para os diferentes status
    COLORS = {
        TrayStatus.OK: (0, 200, 0),        # Verde
        TrayStatus.WARNING: (255, 165, 0),  # Laranja
        TrayStatus.ERROR: (255, 0, 0),      # Vermelho
        TrayStatus.OFFLINE: (128, 128, 128) # Cinza
    }

    def __init__(
        self,
        on_open: Optional[Callable[[], None]] = None,
        on_settings: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None
    ):
        """
        Inicializa o icone na bandeja.

        Args:
            on_open: Callback para abrir interface
            on_settings: Callback para abrir configuracoes
            on_quit: Callback para sair
        """
        self.on_open = on_open
        self.on_settings = on_settings
        self.on_quit = on_quit

        self._icon: Optional[Any] = None
        self._status = TrayStatus.OFFLINE
        self._tooltip = "SkyCamOS Desktop Manager"
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, Callable] = {}
        self._backend_running = False
        self._camera_count = 0

        # Verifica disponibilidade
        if not PYSTRAY_AVAILABLE:
            self.logger.warning("pystray nao disponivel, system tray desabilitado")
        if not PILLOW_AVAILABLE:
            self.logger.warning("Pillow nao disponivel, usando icone padrao")

    @property
    def is_available(self) -> bool:
        """Verifica se system tray esta disponivel."""
        return PYSTRAY_AVAILABLE

    @property
    def status(self) -> TrayStatus:
        """Retorna status atual."""
        return self._status

    @status.setter
    def status(self, value: TrayStatus) -> None:
        """Define status e atualiza icone."""
        if value != self._status:
            self._status = value
            self._update_icon()

    def _create_icon_image(self, status: TrayStatus = None, size: int = 64) -> Optional[Any]:
        """
        Cria imagem do icone.

        Args:
            status: Status para determinar a cor
            size: Tamanho do icone em pixels

        Returns:
            Imagem PIL ou None
        """
        if not PILLOW_AVAILABLE:
            return None

        status = status or self._status
        color = self.COLORS.get(status, self.COLORS[TrayStatus.OFFLINE])

        # Cria imagem
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Desenha circulo de fundo
        margin = size // 8
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=color
        )

        # Desenha icone de camera estilizado
        cam_color = (255, 255, 255)
        cam_margin = size // 4

        # Corpo da camera (retangulo)
        body_left = cam_margin
        body_top = size // 3
        body_right = size - cam_margin - size // 6
        body_bottom = size - cam_margin

        draw.rectangle(
            [body_left, body_top, body_right, body_bottom],
            fill=cam_color
        )

        # Lente da camera (circulo pequeno)
        lens_center_x = (body_left + body_right) // 2
        lens_center_y = (body_top + body_bottom) // 2
        lens_radius = (body_bottom - body_top) // 4

        draw.ellipse(
            [
                lens_center_x - lens_radius,
                lens_center_y - lens_radius,
                lens_center_x + lens_radius,
                lens_center_y + lens_radius
            ],
            fill=color
        )

        # Visor/Flash da camera (triangulo)
        flash_left = body_right
        flash_right = size - cam_margin
        flash_top = body_top
        flash_bottom = body_top + (body_bottom - body_top) // 2

        draw.polygon(
            [
                (flash_left, flash_top),
                (flash_right, (flash_top + flash_bottom) // 2),
                (flash_left, flash_bottom)
            ],
            fill=cam_color
        )

        return image

    def _load_icon_from_file(self, path: Path) -> Optional[Any]:
        """
        Carrega icone de um arquivo.

        Args:
            path: Caminho para o arquivo de icone

        Returns:
            Imagem PIL ou None
        """
        if not PILLOW_AVAILABLE or not path.exists():
            return None

        try:
            return Image.open(path)
        except Exception as e:
            self.logger.debug(f"Erro ao carregar icone: {e}")
            return None

    def _create_menu(self) -> Any:
        """
        Cria menu de contexto.

        Returns:
            Menu pystray
        """
        if not PYSTRAY_AVAILABLE:
            return None

        # Itens do menu
        items = [
            Item(
                "SkyCamOS Desktop Manager",
                None,
                enabled=False
            ),
            Menu.SEPARATOR,
            Item(
                self._get_status_text(),
                None,
                enabled=False
            ),
            Menu.SEPARATOR,
            Item(
                "Abrir Interface",
                self._on_menu_open,
                default=True
            ),
            Item(
                "Descobrir Cameras",
                self._on_menu_discover
            ),
            Menu.SEPARATOR,
            Item(
                "Backend",
                Menu(
                    Item(
                        "Iniciar" if not self._backend_running else "Reiniciar",
                        self._on_menu_start_backend
                    ),
                    Item(
                        "Parar",
                        self._on_menu_stop_backend,
                        enabled=self._backend_running
                    ),
                    Item(
                        "Status",
                        self._on_menu_backend_status
                    )
                )
            ),
            Item(
                "Configuracoes",
                self._on_menu_settings
            ),
            Menu.SEPARATOR,
            Item(
                "Sair",
                self._on_menu_quit
            )
        ]

        return Menu(*items)

    def _get_status_text(self) -> str:
        """Retorna texto de status para o menu."""
        status_map = {
            TrayStatus.OK: f"Online - {self._camera_count} cameras",
            TrayStatus.WARNING: "Aviso - Verificar sistema",
            TrayStatus.ERROR: "Erro - Backend offline",
            TrayStatus.OFFLINE: "Offline"
        }
        return status_map.get(self._status, "Status desconhecido")

    def _update_icon(self) -> None:
        """Atualiza icone e tooltip."""
        if not self._icon:
            return

        try:
            # Atualiza imagem
            new_image = self._create_icon_image()
            if new_image:
                self._icon.icon = new_image

            # Atualiza tooltip
            self._icon.title = self._tooltip

            # Atualiza menu
            self._icon.menu = self._create_menu()

        except Exception as e:
            self.logger.debug(f"Erro ao atualizar icone: {e}")

    def _on_menu_open(self, icon=None, item=None) -> None:
        """Handler para abrir interface."""
        self.logger.debug("Menu: Abrir Interface")
        if self.on_open:
            self.on_open()
        if "open" in self._callbacks:
            self._callbacks["open"]()

    def _on_menu_discover(self, icon=None, item=None) -> None:
        """Handler para descobrir cameras."""
        self.logger.debug("Menu: Descobrir Cameras")
        if "discover" in self._callbacks:
            self._callbacks["discover"]()

    def _on_menu_start_backend(self, icon=None, item=None) -> None:
        """Handler para iniciar backend."""
        self.logger.debug("Menu: Iniciar Backend")
        if "start_backend" in self._callbacks:
            self._callbacks["start_backend"]()

    def _on_menu_stop_backend(self, icon=None, item=None) -> None:
        """Handler para parar backend."""
        self.logger.debug("Menu: Parar Backend")
        if "stop_backend" in self._callbacks:
            self._callbacks["stop_backend"]()

    def _on_menu_backend_status(self, icon=None, item=None) -> None:
        """Handler para status do backend."""
        self.logger.debug("Menu: Status Backend")
        if "backend_status" in self._callbacks:
            self._callbacks["backend_status"]()

    def _on_menu_settings(self, icon=None, item=None) -> None:
        """Handler para configuracoes."""
        self.logger.debug("Menu: Configuracoes")
        if self.on_settings:
            self.on_settings()
        if "settings" in self._callbacks:
            self._callbacks["settings"]()

    def _on_menu_quit(self, icon=None, item=None) -> None:
        """Handler para sair."""
        self.logger.debug("Menu: Sair")
        self.stop()
        if self.on_quit:
            self.on_quit()
        if "quit" in self._callbacks:
            self._callbacks["quit"]()

    def register_callback(self, event: str, callback: Callable) -> None:
        """
        Registra callback para evento do menu.

        Args:
            event: Nome do evento (open, discover, settings, quit, etc)
            callback: Funcao a chamar
        """
        self._callbacks[event] = callback

    def start(self) -> bool:
        """
        Inicia o icone na bandeja.

        Returns:
            True se iniciou com sucesso
        """
        if not PYSTRAY_AVAILABLE:
            self.logger.warning("System tray nao disponivel")
            return False

        if self._running:
            self.logger.warning("System tray ja esta em execucao")
            return True

        try:
            # Cria icone
            image = self._create_icon_image()
            if not image:
                self.logger.error("Nao foi possivel criar imagem do icone")
                return False

            self._icon = pystray.Icon(
                name="skycamos",
                icon=image,
                title=self._tooltip,
                menu=self._create_menu()
            )

            # Inicia em thread separada
            self._running = True
            self._thread = threading.Thread(
                target=self._icon.run,
                daemon=True
            )
            self._thread.start()

            self.logger.info("System tray iniciado")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao iniciar system tray: {e}")
            return False

    def stop(self) -> None:
        """Para o icone na bandeja."""
        if not self._running:
            return

        self._running = False

        if self._icon:
            try:
                self._icon.stop()
            except Exception as e:
                self.logger.debug(f"Erro ao parar icone: {e}")

        self._icon = None
        self.logger.info("System tray parado")

    def show_notification(
        self,
        title: str,
        message: str,
        timeout: int = 5000
    ) -> bool:
        """
        Exibe notificacao do sistema.

        Args:
            title: Titulo da notificacao
            message: Mensagem
            timeout: Duracao em milissegundos

        Returns:
            True se exibiu com sucesso
        """
        if not self._icon:
            return False

        try:
            self._icon.notify(message, title)
            self.logger.debug(f"Notificacao: {title}")
            return True
        except Exception as e:
            self.logger.debug(f"Erro ao exibir notificacao: {e}")
            return False

    def update_status(
        self,
        backend_running: bool = False,
        camera_count: int = 0,
        error_message: str = ""
    ) -> None:
        """
        Atualiza status exibido.

        Args:
            backend_running: Se o backend esta rodando
            camera_count: Numero de cameras conectadas
            error_message: Mensagem de erro (se houver)
        """
        self._backend_running = backend_running
        self._camera_count = camera_count

        # Determina status
        if error_message:
            self.status = TrayStatus.ERROR
            self._tooltip = f"SkyCamOS - ERRO: {error_message}"
        elif not backend_running:
            self.status = TrayStatus.OFFLINE
            self._tooltip = "SkyCamOS - Backend offline"
        elif camera_count == 0:
            self.status = TrayStatus.WARNING
            self._tooltip = "SkyCamOS - Nenhuma camera conectada"
        else:
            self.status = TrayStatus.OK
            self._tooltip = f"SkyCamOS - {camera_count} camera(s) online"

        self._update_icon()

    def update_from_process_state(self, state: ProcessState) -> None:
        """
        Atualiza status baseado no estado do processo.

        Args:
            state: Estado do processo backend
        """
        state_map = {
            ProcessState.RUNNING: TrayStatus.OK,
            ProcessState.STARTING: TrayStatus.WARNING,
            ProcessState.STOPPING: TrayStatus.WARNING,
            ProcessState.RESTARTING: TrayStatus.WARNING,
            ProcessState.CRASHED: TrayStatus.ERROR,
            ProcessState.STOPPED: TrayStatus.OFFLINE
        }

        self._backend_running = state == ProcessState.RUNNING
        self.status = state_map.get(state, TrayStatus.OFFLINE)
        self._update_icon()


class TrayManager(LoggerMixin):
    """
    Gerenciador do System Tray.
    Integra o icone com os servicos da aplicacao.
    """

    def __init__(self):
        """Inicializa o gerenciador."""
        self._tray: Optional[SystemTrayIcon] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def tray(self) -> Optional[SystemTrayIcon]:
        """Retorna instancia do tray."""
        return self._tray

    def setup(
        self,
        loop: asyncio.AbstractEventLoop,
        on_open: Optional[Callable] = None,
        on_quit: Optional[Callable] = None
    ) -> bool:
        """
        Configura o system tray.

        Args:
            loop: Event loop asyncio
            on_open: Callback para abrir
            on_quit: Callback para sair

        Returns:
            True se configurou com sucesso
        """
        self._loop = loop

        self._tray = SystemTrayIcon(
            on_open=on_open,
            on_quit=on_quit
        )

        return self._tray.is_available

    def start(self) -> bool:
        """Inicia o tray."""
        if self._tray:
            return self._tray.start()
        return False

    def stop(self) -> None:
        """Para o tray."""
        if self._tray:
            self._tray.stop()

    def notify(self, title: str, message: str) -> bool:
        """
        Envia notificacao.

        Args:
            title: Titulo
            message: Mensagem

        Returns:
            True se enviou
        """
        if self._tray:
            return self._tray.show_notification(title, message)
        return False
