# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Configuration
Configuracoes centralizadas da aplicacao
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

from .utils.logger import get_logger

logger = get_logger("config")

# Carrega variaveis de ambiente
load_dotenv()


# Diretorios padroes
APP_NAME = "SkyCamOS"
APP_VERSION = "1.0.0"

# Diretorio base da aplicacao
BASE_DIR = Path(__file__).parent.parent
APP_DIR = Path.home() / f".{APP_NAME.lower()}"
CONFIG_DIR = APP_DIR / "config"
DATA_DIR = APP_DIR / "data"
LOGS_DIR = APP_DIR / "logs"
RECORDINGS_DIR = APP_DIR / "recordings"


@dataclass
class ServerConfig:
    """Configuracoes do servidor backend."""
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1
    auto_restart: bool = True
    restart_delay: float = 5.0
    health_check_interval: float = 30.0
    startup_timeout: float = 30.0


@dataclass
class DiscoveryConfig:
    """Configuracoes de descoberta de cameras."""
    onvif_enabled: bool = True
    ssdp_enabled: bool = True
    scan_interval: float = 300.0  # 5 minutos
    scan_timeout: float = 10.0
    onvif_ports: list = field(default_factory=lambda: [80, 8080, 554, 8899])
    default_username: str = "admin"
    default_password: str = "admin"


@dataclass
class StorageConfig:
    """Configuracoes de armazenamento."""
    recordings_dir: Path = RECORDINGS_DIR
    max_storage_gb: float = 100.0
    min_free_space_gb: float = 10.0
    fifo_enabled: bool = True
    check_interval: float = 60.0  # 1 minuto
    warning_threshold_percent: float = 80.0
    critical_threshold_percent: float = 95.0


@dataclass
class UIConfig:
    """Configuracoes de interface."""
    system_tray_enabled: bool = True
    start_minimized: bool = False
    show_notifications: bool = True
    notification_duration: int = 5000  # milissegundos
    theme: str = "dark"


@dataclass
class LoggingConfig:
    """Configuracoes de logging."""
    level: str = "INFO"
    console_output: bool = True
    file_output: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class AutoStartConfig:
    """Configuracoes de auto-inicio."""
    enabled: bool = False
    start_minimized: bool = True
    delay_seconds: float = 10.0


@dataclass
class AppConfig:
    """Configuracao completa da aplicacao."""
    server: ServerConfig = field(default_factory=ServerConfig)
    discovery: DiscoveryConfig = field(default_factory=DiscoveryConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    auto_start: AutoStartConfig = field(default_factory=AutoStartConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Converte configuracao para dicionario."""
        data = asdict(self)
        # Converte Path para string
        data['storage']['recordings_dir'] = str(self.storage.recordings_dir)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Cria configuracao a partir de dicionario."""
        config = cls()

        if 'server' in data:
            config.server = ServerConfig(**data['server'])

        if 'discovery' in data:
            config.discovery = DiscoveryConfig(**data['discovery'])

        if 'storage' in data:
            storage_data = data['storage'].copy()
            if 'recordings_dir' in storage_data:
                storage_data['recordings_dir'] = Path(storage_data['recordings_dir'])
            config.storage = StorageConfig(**storage_data)

        if 'ui' in data:
            config.ui = UIConfig(**data['ui'])

        if 'logging' in data:
            config.logging = LoggingConfig(**data['logging'])

        if 'auto_start' in data:
            config.auto_start = AutoStartConfig(**data['auto_start'])

        return config


class ConfigManager:
    """
    Gerenciador de configuracoes.
    Carrega, salva e valida configuracoes da aplicacao.
    """

    CONFIG_FILE = "config.json"

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Inicializa o gerenciador de configuracoes.

        Args:
            config_dir: Diretorio para arquivos de configuracao
        """
        self.config_dir = config_dir or CONFIG_DIR
        self.config_file = self.config_dir / self.CONFIG_FILE
        self._config: Optional[AppConfig] = None

        # Garante que os diretorios existem
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Cria diretorios necessarios se nao existirem."""
        directories = [
            APP_DIR,
            CONFIG_DIR,
            DATA_DIR,
            LOGS_DIR,
            RECORDINGS_DIR
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Diretorio verificado: {directory}")

    @property
    def config(self) -> AppConfig:
        """Retorna a configuracao atual."""
        if self._config is None:
            self._config = self.load()
        return self._config

    def load(self) -> AppConfig:
        """
        Carrega configuracoes do arquivo.

        Returns:
            Configuracao carregada ou padrao
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self._config = AppConfig.from_dict(data)
                logger.info(f"Configuracao carregada de {self.config_file}")

            except json.JSONDecodeError as e:
                logger.error(f"Erro ao ler configuracao JSON: {e}")
                self._config = AppConfig()

            except Exception as e:
                logger.error(f"Erro ao carregar configuracao: {e}")
                self._config = AppConfig()
        else:
            logger.info("Arquivo de configuracao nao existe, usando padrao")
            self._config = AppConfig()
            self.save()  # Salva configuracao padrao

        return self._config

    def save(self) -> bool:
        """
        Salva configuracoes no arquivo.

        Returns:
            True se salvou com sucesso
        """
        try:
            data = self.config.to_dict()

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuracao salva em {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar configuracao: {e}")
            return False

    def reset(self) -> AppConfig:
        """
        Reseta configuracoes para o padrao.

        Returns:
            Nova configuracao padrao
        """
        self._config = AppConfig()
        self.save()
        logger.info("Configuracao resetada para padrao")
        return self._config

    def update(self, **kwargs) -> bool:
        """
        Atualiza valores especificos da configuracao.

        Args:
            **kwargs: Valores a atualizar (ex: server__port=8080)

        Returns:
            True se atualizou com sucesso
        """
        try:
            for key, value in kwargs.items():
                parts = key.split('__')

                if len(parts) == 2:
                    section, param = parts
                    section_obj = getattr(self.config, section, None)

                    if section_obj is not None and hasattr(section_obj, param):
                        setattr(section_obj, param, value)
                        logger.debug(f"Configuracao atualizada: {section}.{param} = {value}")

            return self.save()

        except Exception as e:
            logger.error(f"Erro ao atualizar configuracao: {e}")
            return False

    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Obtem valor de variavel de ambiente.

        Args:
            key: Nome da variavel
            default: Valor padrao

        Returns:
            Valor da variavel ou padrao
        """
        return os.environ.get(f"SKYCAMOS_{key.upper()}", default)


# Instancia global do gerenciador de configuracoes
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """
    Obtem a configuracao atual.

    Returns:
        Configuracao da aplicacao
    """
    return config_manager.config


def save_config() -> bool:
    """
    Salva a configuracao atual.

    Returns:
        True se salvou com sucesso
    """
    return config_manager.save()
