"""
Configuracoes do SkyCamOS Backend.

Este modulo centraliza todas as configuracoes da aplicacao,
carregando valores do arquivo .env e definindo valores padrao.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Classe de configuracoes da aplicacao.

    Utiliza Pydantic Settings para carregar configuracoes
    do ambiente e arquivo .env automaticamente.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Aplicacao
    app_name: str = "SkyCamOS"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"

    # Servidor
    host: str = "0.0.0.0"
    port: int = 8000

    # Seguranca
    secret_key: str = "desenvolvimento-chave-insegura-mude-em-producao"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Banco de Dados
    database_url: str = "sqlite+aiosqlite:///./data/skycamos.db"

    # Armazenamento
    recordings_path: str = "./recordings"
    max_storage_gb: int = 100
    retention_days: int = 30

    # ONVIF Discovery
    onvif_discovery_timeout: int = 5
    onvif_default_username: str = "admin"
    onvif_default_password: str = "admin"

    # Streaming
    rtsp_buffer_size: int = 10
    hls_segment_duration: int = 2
    webrtc_stun_server: str = "stun:stun.l.google.com:19302"

    # Notificacoes
    push_notification_enabled: bool = False
    firebase_credentials_path: Optional[str] = None

    # Deteccao de Movimento
    motion_threshold: int = 25
    motion_min_area: int = 500
    motion_cooldown_seconds: int = 5

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/skycamos.log"

    @property
    def recordings_dir(self) -> Path:
        """Retorna o diretorio de gravacoes como Path."""
        path = Path(self.recordings_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def logs_dir(self) -> Path:
        """Retorna o diretorio de logs como Path."""
        path = Path(self.log_file).parent
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def max_storage_bytes(self) -> int:
        """Retorna o armazenamento maximo em bytes."""
        return self.max_storage_gb * 1024 * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna a instancia de configuracoes (cached).

    Utiliza cache para evitar recarregar configuracoes
    multiplas vezes durante a execucao.

    Returns:
        Settings: Instancia de configuracoes da aplicacao.
    """
    return Settings()


# Instancia global para uso direto
settings = get_settings()
