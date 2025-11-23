"""
Schemas Pydantic para Camera.

Define os schemas de validacao para operacoes
relacionadas a cameras IP.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, IPvAnyAddress


class CameraBase(BaseModel):
    """
    Schema base para Camera.

    Contem campos comuns entre criacao e resposta.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nome amigavel da camera",
        examples=["Camera Entrada Principal"]
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Descricao ou localizacao da camera",
        examples=["Camera PTZ na entrada principal do edificio"]
    )
    ip_address: str = Field(
        ...,
        description="Endereco IP da camera",
        examples=["192.168.1.100"]
    )
    port: int = Field(
        default=554,
        ge=1,
        le=65535,
        description="Porta de conexao RTSP",
        examples=[554]
    )
    protocol: str = Field(
        default="rtsp",
        description="Protocolo de comunicacao: rtsp, onvif, http, rtmp",
        examples=["rtsp"]
    )

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v: str) -> str:
        """Valida se o protocolo e suportado."""
        allowed = ["rtsp", "onvif", "http", "rtmp"]
        if v.lower() not in allowed:
            raise ValueError(f"Protocolo deve ser um de: {', '.join(allowed)}")
        return v.lower()


class CameraCreate(CameraBase):
    """
    Schema para criacao de Camera.

    Inclui campos de autenticacao e configuracao.
    """

    username: Optional[str] = Field(
        None,
        max_length=100,
        description="Usuario para autenticacao na camera",
        examples=["admin"]
    )
    password: Optional[str] = Field(
        None,
        max_length=255,
        description="Senha para autenticacao na camera"
    )
    rtsp_url: Optional[str] = Field(
        None,
        description="URL completa do stream RTSP (opcional se IP/porta fornecidos)",
        examples=["rtsp://admin:senha@192.168.1.100:554/stream1"]
    )
    rtsp_substream_url: Optional[str] = Field(
        None,
        description="URL do substream de menor qualidade"
    )
    onvif_path: str = Field(
        default="/onvif/device_service",
        description="Path do servico ONVIF"
    )

    # Informacoes do dispositivo
    manufacturer: Optional[str] = Field(None, max_length=100, description="Fabricante")
    model: Optional[str] = Field(None, max_length=100, description="Modelo")

    # Configuracoes
    motion_detection_enabled: bool = Field(
        default=True,
        description="Habilitar deteccao de movimento"
    )
    audio_enabled: bool = Field(default=False, description="Habilitar audio")

    # Video
    resolution_width: int = Field(default=1920, ge=320, le=7680, description="Largura")
    resolution_height: int = Field(default=1080, ge=240, le=4320, description="Altura")
    fps: int = Field(default=25, ge=1, le=120, description="Frames por segundo")

    # Geolocalizacao
    latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Latitude"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Longitude"
    )
    location_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Nome da localizacao"
    )

    # Gravacao
    retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Dias de retencao das gravacoes"
    )


class CameraUpdate(BaseModel):
    """
    Schema para atualizacao de Camera.

    Todos os campos sao opcionais.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    ip_address: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[str] = None
    username: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, max_length=255)
    rtsp_url: Optional[str] = None
    rtsp_substream_url: Optional[str] = None
    onvif_path: Optional[str] = None

    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    firmware_version: Optional[str] = Field(None, max_length=50)

    is_enabled: Optional[bool] = None
    motion_detection_enabled: Optional[bool] = None
    audio_enabled: Optional[bool] = None

    resolution_width: Optional[int] = Field(None, ge=320, le=7680)
    resolution_height: Optional[int] = Field(None, ge=240, le=4320)
    fps: Optional[int] = Field(None, ge=1, le=120)

    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    location_name: Optional[str] = Field(None, max_length=200)

    retention_days: Optional[int] = Field(None, ge=1, le=365)

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v: Optional[str]) -> Optional[str]:
        """Valida se o protocolo e suportado."""
        if v is None:
            return v
        allowed = ["rtsp", "onvif", "http", "rtmp"]
        if v.lower() not in allowed:
            raise ValueError(f"Protocolo deve ser um de: {', '.join(allowed)}")
        return v.lower()


class CameraStatusUpdate(BaseModel):
    """
    Schema para atualizacao de status da camera.
    """

    status: str = Field(
        ...,
        description="Novo status: online, offline, recording, error, connecting"
    )
    is_recording: Optional[bool] = Field(None, description="Em gravacao")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Valida se o status e valido."""
        allowed = ["online", "offline", "recording", "error", "connecting"]
        if v.lower() not in allowed:
            raise ValueError(f"Status deve ser um de: {', '.join(allowed)}")
        return v.lower()


class CameraResponse(CameraBase):
    """
    Schema de resposta para Camera.

    Inclui todos os campos, exceto senha.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID da camera")
    username: Optional[str] = None
    rtsp_url: Optional[str] = None
    rtsp_substream_url: Optional[str] = None
    onvif_path: str

    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    mac_address: Optional[str] = None

    status: str
    is_enabled: bool
    is_recording: bool
    motion_detection_enabled: bool

    ptz_capable: bool
    audio_enabled: bool
    two_way_audio: bool

    resolution_width: int
    resolution_height: int
    resolution: str
    fps: int
    bitrate: Optional[int] = None
    codec: str

    snapshot_url: Optional[str] = None
    thumbnail_path: Optional[str] = None
    stream_url: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None

    retention_days: int

    created_at: datetime
    updated_at: datetime
    last_seen: Optional[datetime] = None
    last_recording: Optional[datetime] = None

    is_online: bool

    @model_validator(mode='after')
    def populate_stream_url(self) -> 'CameraResponse':
        """Popula stream_url com base no ID da camera."""
        if not self.stream_url and self.id:
            self.stream_url = f"/api/v1/stream/{self.id}/mjpeg"
        return self


class CameraListResponse(BaseModel):
    """
    Schema de resposta para lista de cameras.
    """

    items: List[CameraResponse] = Field(..., description="Lista de cameras")
    total: int = Field(..., description="Total de cameras")
    page: int = Field(default=1, description="Pagina atual")
    page_size: int = Field(default=20, description="Itens por pagina")
    pages: int = Field(..., description="Total de paginas")


class CameraDiscovery(BaseModel):
    """
    Schema para resultado de descoberta de camera.
    """

    ip_address: str = Field(..., description="IP descoberto")
    port: int = Field(..., description="Porta")
    protocol: str = Field(..., description="Protocolo detectado")
    manufacturer: Optional[str] = Field(None, description="Fabricante detectado")
    model: Optional[str] = Field(None, description="Modelo detectado")
    name: Optional[str] = Field(None, description="Nome sugerido")
    onvif_url: Optional[str] = Field(None, description="URL ONVIF")
    rtsp_url: Optional[str] = Field(None, description="URL RTSP sugerida")
    requires_auth: bool = Field(default=True, description="Requer autenticacao")


class CameraTestConnection(BaseModel):
    """
    Schema para teste de conexao de camera.
    """

    ip_address: str = Field(..., description="IP da camera")
    port: int = Field(default=554, description="Porta")
    protocol: str = Field(default="rtsp", description="Protocolo")
    username: Optional[str] = Field(None, description="Usuario")
    password: Optional[str] = Field(None, description="Senha")
    rtsp_url: Optional[str] = Field(None, description="URL RTSP completa")


class CameraTestResult(BaseModel):
    """
    Schema de resultado do teste de conexao.
    """

    success: bool = Field(..., description="Conexao bem sucedida")
    message: str = Field(..., description="Mensagem de resultado")
    latency_ms: Optional[float] = Field(None, description="Latencia em ms")
    resolution: Optional[str] = Field(None, description="Resolucao detectada")
    codec: Optional[str] = Field(None, description="Codec detectado")
    fps: Optional[int] = Field(None, description="FPS detectado")
    snapshot: Optional[str] = Field(None, description="Snapshot em base64")
