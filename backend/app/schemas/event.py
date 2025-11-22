"""
Schemas Pydantic para Evento.

Define os schemas de validacao para operacoes
relacionadas a eventos do sistema.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventBase(BaseModel):
    """
    Schema base para Evento.

    Contem campos comuns entre criacao e resposta.
    """

    event_type: str = Field(
        default="motion",
        description="Tipo do evento",
        examples=["motion", "person", "vehicle", "tamper", "connection_lost"]
    )
    severity: str = Field(
        default="info",
        description="Severidade: info, low, medium, high, critical",
        examples=["medium"]
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Titulo do evento",
        examples=["Movimento detectado na Camera 1"]
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Descricao detalhada"
    )

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Valida o tipo de evento."""
        allowed = [
            "motion", "person", "vehicle", "face", "intrusion",
            "line_crossing", "object_left", "object_removed", "tamper",
            "connection_lost", "connection_restored", "recording_started",
            "recording_stopped", "storage_warning", "system", "custom"
        ]
        if v.lower() not in allowed:
            raise ValueError(f"Tipo deve ser um de: {', '.join(allowed)}")
        return v.lower()

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Valida a severidade."""
        allowed = ["info", "low", "medium", "high", "critical"]
        if v.lower() not in allowed:
            raise ValueError(f"Severidade deve ser um de: {', '.join(allowed)}")
        return v.lower()


class EventCreate(EventBase):
    """
    Schema para criacao de Evento.
    """

    camera_id: Optional[int] = Field(None, description="ID da camera")
    recording_id: Optional[int] = Field(None, description="ID da gravacao")
    user_id: Optional[int] = Field(None, description="ID do usuario")

    timestamp: Optional[datetime] = Field(
        None,
        description="Timestamp do evento (default: agora)"
    )
    duration_seconds: Optional[float] = Field(
        None,
        ge=0,
        description="Duracao do evento"
    )

    snapshot_path: Optional[str] = Field(None, description="Caminho do snapshot")
    video_clip_path: Optional[str] = Field(None, description="Caminho do clipe")

    confidence: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Nivel de confianca 0-100"
    )
    bounding_box: Optional[Dict[str, int]] = Field(
        None,
        description="Coordenadas do objeto: {x, y, width, height}"
    )
    detection_zone: Optional[str] = Field(
        None,
        max_length=100,
        description="Nome da zona de deteccao"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados adicionais"
    )
    source: Optional[str] = Field(
        None,
        max_length=50,
        description="Origem do evento: camera, system, user"
    )

    @field_validator("bounding_box")
    @classmethod
    def validate_bounding_box(cls, v: Optional[Dict[str, int]]) -> Optional[str]:
        """Converte bounding_box para JSON string."""
        if v is None:
            return None
        import json
        return json.dumps(v)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: Optional[Dict[str, Any]]) -> Optional[str]:
        """Converte metadata para JSON string."""
        if v is None:
            return None
        import json
        return json.dumps(v)


class EventUpdate(BaseModel):
    """
    Schema para atualizacao de Evento.
    """

    is_starred: Optional[bool] = Field(None, description="Marcar como favorito")
    is_false_positive: Optional[bool] = Field(
        None,
        description="Marcar como falso positivo"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Notas sobre o evento"
    )


class EventAcknowledge(BaseModel):
    """
    Schema para reconhecimento de Evento.
    """

    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Notas do reconhecimento"
    )


class EventResponse(EventBase):
    """
    Schema de resposta para Evento.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID do evento")
    camera_id: Optional[int] = None
    recording_id: Optional[int] = None
    user_id: Optional[int] = None

    timestamp: datetime = Field(..., description="Timestamp do evento")
    duration_seconds: Optional[float] = None
    end_timestamp: Optional[datetime] = None

    snapshot_path: Optional[str] = None
    video_clip_path: Optional[str] = None
    thumbnail_path: Optional[str] = None

    confidence: Optional[float] = None
    bounding_box: Optional[str] = None
    detection_zone: Optional[str] = None

    metadata: Optional[str] = None
    source: Optional[str] = None

    is_read: bool = Field(..., description="Evento lido")
    is_acknowledged: bool = Field(..., description="Evento reconhecido")
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    notes: Optional[str] = None

    notification_sent: bool = Field(..., description="Notificacao enviada")
    notification_sent_at: Optional[datetime] = None

    is_false_positive: bool = Field(..., description="Falso positivo")
    is_starred: bool = Field(..., description="Favorito")

    is_motion_event: bool = Field(..., description="E evento de movimento")
    is_critical: bool = Field(..., description="E evento critico")
    needs_attention: bool = Field(..., description="Precisa de atencao")

    created_at: datetime

    # Dados relacionados (opcionais, preenchidos conforme necessidade)
    camera_name: Optional[str] = Field(None, description="Nome da camera")


class EventListResponse(BaseModel):
    """
    Schema de resposta para lista de eventos.
    """

    items: List[EventResponse] = Field(..., description="Lista de eventos")
    total: int = Field(..., description="Total de eventos")
    page: int = Field(default=1, description="Pagina atual")
    page_size: int = Field(default=20, description="Itens por pagina")
    pages: int = Field(..., description="Total de paginas")
    unread_count: int = Field(default=0, description="Total nao lidos")
    unacknowledged_count: int = Field(
        default=0,
        description="Total nao reconhecidos"
    )


class EventFilter(BaseModel):
    """
    Schema para filtros de busca de eventos.
    """

    camera_id: Optional[int] = Field(None, description="Filtrar por camera")
    camera_ids: Optional[List[int]] = Field(None, description="Filtrar por cameras")
    event_type: Optional[str] = Field(None, description="Filtrar por tipo")
    event_types: Optional[List[str]] = Field(None, description="Filtrar por tipos")
    severity: Optional[str] = Field(None, description="Filtrar por severidade")
    min_severity: Optional[str] = Field(
        None,
        description="Severidade minima"
    )
    start_date: Optional[datetime] = Field(None, description="Data inicial")
    end_date: Optional[datetime] = Field(None, description="Data final")
    is_read: Optional[bool] = Field(None, description="Filtrar por lido/nao lido")
    is_acknowledged: Optional[bool] = Field(
        None,
        description="Filtrar por reconhecido"
    )
    is_starred: Optional[bool] = Field(None, description="Somente favoritos")
    has_snapshot: Optional[bool] = Field(None, description="Somente com snapshot")
    search: Optional[str] = Field(
        None,
        max_length=100,
        description="Busca por texto"
    )


class EventStats(BaseModel):
    """
    Schema para estatisticas de eventos.
    """

    total_events: int = Field(..., description="Total de eventos")
    events_today: int = Field(..., description="Eventos hoje")
    events_this_week: int = Field(..., description="Eventos esta semana")
    events_this_month: int = Field(..., description="Eventos este mes")
    unread_count: int = Field(..., description="Nao lidos")
    unacknowledged_count: int = Field(..., description="Nao reconhecidos")
    critical_count: int = Field(..., description="Eventos criticos")
    events_by_type: Dict[str, int] = Field(..., description="Por tipo")
    events_by_severity: Dict[str, int] = Field(..., description="Por severidade")
    events_by_camera: Dict[str, int] = Field(..., description="Por camera")
    events_by_hour: Dict[str, int] = Field(..., description="Por hora do dia")


class EventBulkAction(BaseModel):
    """
    Schema para acoes em lote de eventos.
    """

    event_ids: List[int] = Field(
        ...,
        min_length=1,
        description="IDs dos eventos"
    )
    action: str = Field(
        ...,
        description="Acao: mark_read, mark_unread, acknowledge, delete, star, unstar"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Notas para reconhecimento"
    )

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Valida a acao."""
        allowed = [
            "mark_read", "mark_unread", "acknowledge",
            "delete", "star", "unstar"
        ]
        if v.lower() not in allowed:
            raise ValueError(f"Acao deve ser um de: {', '.join(allowed)}")
        return v.lower()
