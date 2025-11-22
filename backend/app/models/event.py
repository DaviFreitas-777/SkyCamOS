"""
Modelo de Evento do SkyCamOS.

Define a estrutura da tabela de eventos no banco de dados,
armazenando eventos de movimento, alertas e notificacoes.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.camera import Camera
    from app.models.recording import Recording
    from app.models.user import User


class EventType(str, Enum):
    """Tipos de eventos do sistema."""

    MOTION = "motion"  # Deteccao de movimento
    PERSON = "person"  # Deteccao de pessoa
    VEHICLE = "vehicle"  # Deteccao de veiculo
    FACE = "face"  # Deteccao de face
    INTRUSION = "intrusion"  # Intrusao em zona
    LINE_CROSSING = "line_crossing"  # Cruzamento de linha
    OBJECT_LEFT = "object_left"  # Objeto abandonado
    OBJECT_REMOVED = "object_removed"  # Objeto removido
    TAMPER = "tamper"  # Tamperagem da camera
    CONNECTION_LOST = "connection_lost"  # Perda de conexao
    CONNECTION_RESTORED = "connection_restored"  # Conexao restaurada
    RECORDING_STARTED = "recording_started"  # Gravacao iniciada
    RECORDING_STOPPED = "recording_stopped"  # Gravacao parada
    STORAGE_WARNING = "storage_warning"  # Aviso de armazenamento
    SYSTEM = "system"  # Evento de sistema
    CUSTOM = "custom"  # Evento personalizado


class EventSeverity(str, Enum):
    """Severidade do evento."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Event(Base):
    """
    Modelo de evento do sistema.

    Representa um evento detectado pelo sistema, como movimento,
    alertas de conexao ou notificacoes do sistema.

    Attributes:
        id: Identificador unico do evento.
        camera_id: ID da camera que gerou o evento (pode ser nulo para eventos de sistema).
        recording_id: ID da gravacao associada (se houver).
        user_id: ID do usuario que gerou ou reconheceu o evento.
        event_type: Tipo do evento.
        severity: Severidade do evento.
        title: Titulo curto do evento.
        description: Descricao detalhada do evento.
        timestamp: Momento exato do evento.
        duration_seconds: Duracao do evento em segundos.
        snapshot_path: Caminho da imagem capturada.
        video_clip_path: Caminho do clipe de video.
        confidence: Nivel de confianca da deteccao (0-100).
        bounding_box: Coordenadas do objeto detectado (JSON).
        metadata: Metadados adicionais do evento (JSON).
        is_read: Indica se o evento foi visualizado.
        is_acknowledged: Indica se o evento foi reconhecido/tratado.
        acknowledged_by: Usuario que reconheceu o evento.
        acknowledged_at: Data do reconhecimento.
        notification_sent: Indica se notificacao foi enviada.
        created_at: Data de criacao do registro.
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Relacionamentos opcionais
    camera_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=True, index=True
    )
    recording_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("recordings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Tipo e Severidade
    event_type: Mapped[str] = mapped_column(
        String(30), default=EventType.MOTION.value, nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(
        String(20), default=EventSeverity.INFO.value, nullable=False, index=True
    )

    # Descricao
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps do evento
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Midia associada
    snapshot_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_clip_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Deteccao
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    bounding_box: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON: {"x": 0, "y": 0, "width": 100, "height": 100}
    detection_zone: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Nome da zona de deteccao

    # Metadados
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    source: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # camera, system, user, etc.

    # Status do evento
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_acknowledged: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Notificacao
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Flags
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps do registro
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    camera: Mapped[Optional["Camera"]] = relationship("Camera", back_populates="events")
    recording: Mapped[Optional["Recording"]] = relationship("Recording", back_populates="events")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="events")

    def __repr__(self) -> str:
        """Representacao string do evento."""
        return f"<Event(id={self.id}, type='{self.event_type}', camera_id={self.camera_id})>"

    @property
    def is_motion_event(self) -> bool:
        """Verifica se e um evento de movimento."""
        return self.event_type == EventType.MOTION.value

    @property
    def is_critical(self) -> bool:
        """Verifica se o evento e critico."""
        return self.severity in (EventSeverity.HIGH.value, EventSeverity.CRITICAL.value)

    @property
    def needs_attention(self) -> bool:
        """Verifica se o evento precisa de atencao (nao lido e nao reconhecido)."""
        return not self.is_read and not self.is_acknowledged

    def mark_as_read(self) -> None:
        """Marca o evento como lido."""
        self.is_read = True

    def acknowledge(self, username: str, notes: Optional[str] = None) -> None:
        """
        Reconhece o evento.

        Args:
            username: Nome do usuario que esta reconhecendo.
            notes: Notas opcionais sobre o reconhecimento.
        """
        self.is_acknowledged = True
        self.is_read = True
        self.acknowledged_by = username
        self.acknowledged_at = datetime.utcnow()
        if notes:
            self.notes = notes
