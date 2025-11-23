"""
Modelo de Camera do SkyCamOS.

Define a estrutura da tabela de cameras no banco de dados,
incluindo configuracoes de conexao e streaming.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CameraStatus(str, Enum):
    """Status possiveis de uma camera."""

    ONLINE = "online"
    OFFLINE = "offline"
    RECORDING = "recording"
    ERROR = "error"
    CONNECTING = "connecting"


class CameraProtocol(str, Enum):
    """Protocolos de conexao suportados."""

    RTSP = "rtsp"
    ONVIF = "onvif"
    HTTP = "http"
    RTMP = "rtmp"


class Camera(Base):
    """
    Modelo de camera IP do sistema.

    Representa uma camera de vigilancia conectada ao sistema,
    armazenando informacoes de conexao, configuracao e estado.

    Attributes:
        id: Identificador unico da camera.
        name: Nome amigavel da camera.
        description: Descricao ou localizacao da camera.
        ip_address: Endereco IP da camera.
        port: Porta de conexao.
        protocol: Protocolo de comunicacao (RTSP, ONVIF, etc).
        username: Usuario para autenticacao na camera.
        password: Senha para autenticacao na camera.
        rtsp_url: URL completa do stream RTSP.
        onvif_path: Path do servico ONVIF.
        manufacturer: Fabricante da camera.
        model: Modelo da camera.
        firmware_version: Versao do firmware.
        status: Status atual da camera.
        is_recording: Indica se esta gravando.
        motion_detection_enabled: Indica se deteccao de movimento esta ativa.
        ptz_capable: Indica se a camera suporta PTZ.
        audio_enabled: Indica se audio esta habilitado.
        resolution_width: Largura da resolucao do video.
        resolution_height: Altura da resolucao do video.
        fps: Frames por segundo.
        bitrate: Taxa de bits do video.
        snapshot_url: URL para captura de snapshot.
        latitude: Latitude para geolocalizacao.
        longitude: Longitude para geolocalizacao.
        created_at: Data de criacao do registro.
        updated_at: Data da ultima atualizacao.
        last_seen: Ultima vez que a camera foi vista online.
    """

    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Conexao
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    port: Mapped[int] = mapped_column(Integer, default=554, nullable=False)
    protocol: Mapped[str] = mapped_column(
        String(20), default=CameraProtocol.RTSP.value, nullable=False
    )
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rtsp_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rtsp_substream_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    onvif_path: Mapped[str] = mapped_column(
        String(100), default="/onvif/device_service", nullable=False
    )

    # Informacoes do dispositivo
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)

    # Estado
    status: Mapped[str] = mapped_column(
        String(20), default=CameraStatus.OFFLINE.value, nullable=False
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_recording: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    motion_detection_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Capacidades
    ptz_capable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    audio_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_way_audio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Configuracoes de video
    resolution_width: Mapped[int] = mapped_column(Integer, default=1920, nullable=False)
    resolution_height: Mapped[int] = mapped_column(Integer, default=1080, nullable=False)
    fps: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    codec: Mapped[str] = mapped_column(String(20), default="H.264", nullable=False)

    # URLs auxiliares
    snapshot_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Geolocalizacao
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Configuracoes de gravacao
    recording_schedule: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON com agendamento
    retention_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    pre_recording_seconds: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    post_recording_seconds: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_recording: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relacionamentos
    recordings: Mapped[list["Recording"]] = relationship(  # noqa: F821
        "Recording",
        back_populates="camera",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        "Event",
        back_populates="camera",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Representacao string da camera."""
        return f"<Camera(id={self.id}, name='{self.name}', ip='{self.ip_address}')>"

    @property
    def resolution(self) -> str:
        """Retorna a resolucao formatada."""
        return f"{self.resolution_width}x{self.resolution_height}"

    @property
    def rtsp_full_url(self) -> str:
        """Constroi a URL RTSP completa se nao estiver definida."""
        if self.rtsp_url:
            return self.rtsp_url

        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"

        return f"rtsp://{auth}{self.ip_address}:{self.port}/stream1"

    @property
    def is_online(self) -> bool:
        """Verifica se a camera esta online."""
        return self.status in (CameraStatus.ONLINE.value, CameraStatus.RECORDING.value)

    @property
    def stream_url(self) -> str:
        """Retorna a URL de streaming MJPEG do backend."""
        return f"/api/v1/stream/{self.id}/mjpeg"
