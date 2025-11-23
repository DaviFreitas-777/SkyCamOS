"""
Modelo de Storage Pool do SkyCamOS.

Define pools de armazenamento para distribuir gravacoes
em multiplos discos/diretorios.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StoragePoolStatus(str, Enum):
    """Status possiveis de um pool de storage."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    FULL = "full"
    ERROR = "error"


class StoragePool(Base):
    """
    Modelo de pool de armazenamento.

    Representa um disco/diretorio onde gravacoes podem ser salvas.
    Permite distribuir gravacoes em multiplos discos.

    Attributes:
        id: Identificador unico do pool.
        name: Nome amigavel do pool (ex: "Disco E", "NAS Principal").
        path: Caminho absoluto do diretorio de gravacoes.
        max_size_gb: Tamanho maximo em GB (0 = sem limite).
        priority: Prioridade de uso (menor = mais prioritario).
        status: Status atual do pool.
        is_default: Se e o pool padrao para novas cameras.
    """

    __tablename__ = "storage_pools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)

    # Limites
    max_size_gb: Mapped[int] = mapped_column(Integer, default=0)  # 0 = sem limite
    min_free_gb: Mapped[int] = mapped_column(Integer, default=10)  # Espaco minimo livre
    retention_days: Mapped[int] = mapped_column(Integer, default=30)

    # Configuracoes
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=StoragePoolStatus.ACTIVE.value
    )

    # Estatisticas (atualizadas periodicamente)
    total_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    used_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    free_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    recording_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<StoragePool(id={self.id}, name='{self.name}', path='{self.path}')>"

    @property
    def usage_percent(self) -> float:
        """Retorna percentual de uso do disco."""
        if self.total_size_bytes == 0:
            return 0.0
        return (self.used_size_bytes / self.total_size_bytes) * 100

    @property
    def free_gb(self) -> float:
        """Retorna espaco livre em GB."""
        return self.free_size_bytes / (1024 ** 3)

    @property
    def is_available(self) -> bool:
        """Verifica se o pool esta disponivel para gravacao."""
        return (
            self.is_enabled and
            self.status == StoragePoolStatus.ACTIVE.value and
            self.free_gb >= self.min_free_gb
        )


class CameraStorageAssignment(Base):
    """
    Associacao entre camera e pool de storage.

    Permite que cada camera grave em um pool especifico.

    Attributes:
        camera_id: ID da camera.
        storage_pool_id: ID do pool de storage.
        is_primary: Se e o storage primario da camera.
    """

    __tablename__ = "camera_storage_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False
    )
    storage_pool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("storage_pools.id", ondelete="CASCADE"), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<CameraStorageAssignment(camera={self.camera_id}, pool={self.storage_pool_id})>"
