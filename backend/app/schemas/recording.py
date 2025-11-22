"""
Schemas Pydantic para Gravacao.

Define os schemas de validacao para operacoes
relacionadas a gravacoes de video.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecordingBase(BaseModel):
    """
    Schema base para Gravacao.

    Contem campos comuns entre criacao e resposta.
    """

    camera_id: int = Field(..., description="ID da camera", examples=[1])
    recording_type: str = Field(
        default="continuous",
        description="Tipo: continuous, motion, scheduled, manual, alarm",
        examples=["continuous"]
    )

    @field_validator("recording_type")
    @classmethod
    def validate_recording_type(cls, v: str) -> str:
        """Valida o tipo de gravacao."""
        allowed = ["continuous", "motion", "scheduled", "manual", "alarm"]
        if v.lower() not in allowed:
            raise ValueError(f"Tipo deve ser um de: {', '.join(allowed)}")
        return v.lower()


class RecordingCreate(RecordingBase):
    """
    Schema para criacao de Gravacao.

    Usado principalmente internamente pelo sistema.
    """

    filename: str = Field(..., description="Nome do arquivo")
    filepath: str = Field(..., description="Caminho completo do arquivo")
    start_time: Optional[datetime] = Field(
        None,
        description="Horario de inicio (default: agora)"
    )
    resolution: Optional[str] = Field(None, description="Resolucao do video")
    fps: Optional[int] = Field(None, ge=1, le=120, description="FPS")
    codec: Optional[str] = Field(None, description="Codec de video")
    has_audio: bool = Field(default=False, description="Contem audio")


class RecordingUpdate(BaseModel):
    """
    Schema para atualizacao de Gravacao.

    Permite marcar gravacoes como favoritas, protegidas, etc.
    """

    is_locked: Optional[bool] = Field(
        None,
        description="Proteger contra exclusao automatica"
    )
    is_starred: Optional[bool] = Field(
        None,
        description="Marcar como favorita"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Notas sobre a gravacao"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Tags para organizacao"
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[str]:
        """Converte lista de tags para JSON string."""
        if v is None:
            return None
        import json
        return json.dumps(v)


class RecordingComplete(BaseModel):
    """
    Schema para finalizar uma gravacao.
    """

    end_time: Optional[datetime] = Field(
        None,
        description="Horario de fim (default: agora)"
    )
    duration_seconds: Optional[float] = Field(
        None,
        ge=0,
        description="Duracao em segundos"
    )
    file_size_bytes: Optional[int] = Field(
        None,
        ge=0,
        description="Tamanho do arquivo em bytes"
    )
    status: str = Field(
        default="completed",
        description="Status final: completed, failed"
    )
    thumbnail_path: Optional[str] = Field(
        None,
        description="Caminho da miniatura"
    )


class RecordingResponse(BaseModel):
    """
    Schema de resposta para Gravacao.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID da gravacao")
    camera_id: int = Field(..., description="ID da camera")

    filename: str = Field(..., description="Nome do arquivo")
    filepath: str = Field(..., description="Caminho do arquivo")
    thumbnail_path: Optional[str] = None

    recording_type: str = Field(..., description="Tipo de gravacao")
    status: str = Field(..., description="Status")

    start_time: datetime = Field(..., description="Inicio")
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    duration_formatted: str = Field(..., description="Duracao formatada HH:MM:SS")

    file_size_bytes: Optional[int] = None
    file_size_formatted: str = Field(..., description="Tamanho formatado")

    resolution: Optional[str] = None
    fps: Optional[int] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    has_audio: bool

    is_locked: bool = Field(..., description="Protegida contra exclusao")
    is_starred: bool = Field(..., description="Marcada como favorita")
    notes: Optional[str] = None
    tags: Optional[str] = None

    event_count: int = Field(..., description="Numero de eventos")
    has_motion: bool = Field(..., description="Contem movimento")

    is_complete: bool = Field(..., description="Gravacao completa")

    created_at: datetime
    updated_at: datetime


class RecordingListResponse(BaseModel):
    """
    Schema de resposta para lista de gravacoes.
    """

    items: List[RecordingResponse] = Field(..., description="Lista de gravacoes")
    total: int = Field(..., description="Total de gravacoes")
    page: int = Field(default=1, description="Pagina atual")
    page_size: int = Field(default=20, description="Itens por pagina")
    pages: int = Field(..., description="Total de paginas")
    total_size_bytes: Optional[int] = Field(
        None,
        description="Tamanho total em bytes"
    )
    total_duration_seconds: Optional[float] = Field(
        None,
        description="Duracao total em segundos"
    )


class RecordingFilter(BaseModel):
    """
    Schema para filtros de busca de gravacoes.
    """

    camera_id: Optional[int] = Field(None, description="Filtrar por camera")
    camera_ids: Optional[List[int]] = Field(None, description="Filtrar por cameras")
    recording_type: Optional[str] = Field(None, description="Filtrar por tipo")
    status: Optional[str] = Field(None, description="Filtrar por status")
    start_date: Optional[datetime] = Field(None, description="Data inicial")
    end_date: Optional[datetime] = Field(None, description="Data final")
    has_motion: Optional[bool] = Field(None, description="Somente com movimento")
    is_starred: Optional[bool] = Field(None, description="Somente favoritas")
    is_locked: Optional[bool] = Field(None, description="Somente protegidas")
    min_duration: Optional[int] = Field(
        None,
        ge=0,
        description="Duracao minima em segundos"
    )
    search: Optional[str] = Field(
        None,
        max_length=100,
        description="Busca por texto em notas/tags"
    )


class RecordingExport(BaseModel):
    """
    Schema para exportacao de gravacao.
    """

    format: str = Field(
        default="mp4",
        description="Formato de saida: mp4, avi, mkv"
    )
    start_time: Optional[datetime] = Field(
        None,
        description="Inicio do corte"
    )
    end_time: Optional[datetime] = Field(
        None,
        description="Fim do corte"
    )
    include_audio: bool = Field(
        default=True,
        description="Incluir audio se disponivel"
    )
    quality: str = Field(
        default="original",
        description="Qualidade: original, high, medium, low"
    )

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Valida formato de saida."""
        allowed = ["mp4", "avi", "mkv", "webm"]
        if v.lower() not in allowed:
            raise ValueError(f"Formato deve ser um de: {', '.join(allowed)}")
        return v.lower()

    @field_validator("quality")
    @classmethod
    def validate_quality(cls, v: str) -> str:
        """Valida qualidade."""
        allowed = ["original", "high", "medium", "low"]
        if v.lower() not in allowed:
            raise ValueError(f"Qualidade deve ser um de: {', '.join(allowed)}")
        return v.lower()


class StorageStats(BaseModel):
    """
    Schema para estatisticas de armazenamento.
    """

    total_recordings: int = Field(..., description="Total de gravacoes")
    total_size_bytes: int = Field(..., description="Tamanho total em bytes")
    total_size_formatted: str = Field(..., description="Tamanho formatado")
    total_duration_seconds: float = Field(..., description="Duracao total")
    total_duration_formatted: str = Field(..., description="Duracao formatada")
    oldest_recording: Optional[datetime] = Field(None, description="Gravacao mais antiga")
    newest_recording: Optional[datetime] = Field(None, description="Gravacao mais recente")
    storage_used_percent: float = Field(..., description="Porcentagem de uso")
    storage_available_bytes: int = Field(..., description="Espaco disponivel")
    recordings_by_type: dict = Field(..., description="Contagem por tipo")
    recordings_by_camera: dict = Field(..., description="Contagem por camera")
