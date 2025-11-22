"""
Modelo de Gravacao do SkyCamOS.

Define a estrutura da tabela de gravacoes no banco de dados,
armazenando metadados dos arquivos de video gravados.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.camera import Camera


class RecordingType(str, Enum):
    """Tipos de gravacao."""

    CONTINUOUS = "continuous"  # Gravacao continua
    MOTION = "motion"  # Gravacao por movimento
    SCHEDULED = "scheduled"  # Gravacao agendada
    MANUAL = "manual"  # Gravacao manual
    ALARM = "alarm"  # Gravacao por alarme


class RecordingStatus(str, Enum):
    """Status da gravacao."""

    RECORDING = "recording"  # Em andamento
    COMPLETED = "completed"  # Finalizada
    FAILED = "failed"  # Falhou
    PROCESSING = "processing"  # Processando
    DELETED = "deleted"  # Marcada para exclusao


class Recording(Base):
    """
    Modelo de gravacao de video do sistema.

    Representa um arquivo de gravacao associado a uma camera,
    contendo metadados como duracao, tamanho e timestamps.

    Attributes:
        id: Identificador unico da gravacao.
        camera_id: ID da camera que gerou a gravacao.
        filename: Nome do arquivo de video.
        filepath: Caminho completo do arquivo.
        recording_type: Tipo da gravacao (continua, movimento, etc).
        status: Status atual da gravacao.
        start_time: Horario de inicio da gravacao.
        end_time: Horario de fim da gravacao.
        duration_seconds: Duracao em segundos.
        file_size_bytes: Tamanho do arquivo em bytes.
        resolution: Resolucao do video.
        fps: Frames por segundo.
        codec: Codec de video utilizado.
        has_audio: Indica se tem audio.
        thumbnail_path: Caminho da miniatura.
        is_locked: Indica se gravacao esta protegida contra exclusao.
        is_starred: Indica se gravacao esta marcada como favorita.
        created_at: Data de criacao do registro.
    """

    __tablename__ = "recordings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Arquivo
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tipo e Status
    recording_type: Mapped[str] = mapped_column(
        String(20), default=RecordingType.CONTINUOUS.value, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=RecordingStatus.RECORDING.value, nullable=False, index=True
    )

    # Timestamps da gravacao
    start_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Metadados do arquivo
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    has_audio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Marcadores
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array de tags

    # Eventos relacionados
    event_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_motion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps do registro
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    camera: Mapped["Camera"] = relationship("Camera", back_populates="recordings")
    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        "Event",
        back_populates="recording",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Representacao string da gravacao."""
        return f"<Recording(id={self.id}, camera_id={self.camera_id}, filename='{self.filename}')>"

    @property
    def duration_formatted(self) -> str:
        """Retorna a duracao formatada como HH:MM:SS."""
        if not self.duration_seconds:
            return "00:00:00"

        hours = int(self.duration_seconds // 3600)
        minutes = int((self.duration_seconds % 3600) // 60)
        seconds = int(self.duration_seconds % 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def file_size_formatted(self) -> str:
        """Retorna o tamanho do arquivo formatado."""
        if not self.file_size_bytes:
            return "0 B"

        size = self.file_size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024

        return f"{size:.2f} PB"

    @property
    def is_complete(self) -> bool:
        """Verifica se a gravacao esta completa."""
        return self.status == RecordingStatus.COMPLETED.value
