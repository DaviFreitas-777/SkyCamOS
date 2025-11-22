"""
Modelo de Usuario do SkyCamOS.

Define a estrutura da tabela de usuarios no banco de dados,
incluindo campos para autenticacao e permissoes.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """
    Modelo de usuario do sistema.

    Representa um usuario que pode acessar o sistema de monitoramento,
    com diferentes niveis de permissao.

    Attributes:
        id: Identificador unico do usuario.
        username: Nome de usuario para login.
        email: Email do usuario.
        hashed_password: Senha criptografada.
        full_name: Nome completo do usuario.
        is_active: Indica se o usuario esta ativo.
        is_superuser: Indica se o usuario tem permissoes administrativas.
        role: Papel do usuario (admin, operator, viewer).
        created_at: Data de criacao do registro.
        updated_at: Data da ultima atualizacao.
        last_login: Data do ultimo login.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), default="viewer", nullable=False
    )  # admin, operator, viewer
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relacionamentos
    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        "Event", back_populates="user", lazy="selectin"
    )

    def __repr__(self) -> str:
        """Representacao string do usuario."""
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    @property
    def is_admin(self) -> bool:
        """Verifica se o usuario e administrador."""
        return self.is_superuser or self.role == "admin"

    @property
    def can_manage_cameras(self) -> bool:
        """Verifica se o usuario pode gerenciar cameras."""
        return self.role in ("admin", "operator")
