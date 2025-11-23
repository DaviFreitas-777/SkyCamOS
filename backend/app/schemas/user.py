"""
Schemas Pydantic para Usuario.

Define os schemas de validacao para operacoes
relacionadas a usuarios e autenticacao.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """
    Schema base para Usuario.

    Contem campos comuns entre criacao e resposta.
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Nome de usuario para login",
        examples=["admin"]
    )
    email: EmailStr = Field(
        ...,
        description="Email do usuario",
        examples=["admin@skycamos.com"]
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Nome completo do usuario",
        examples=["Administrador do Sistema"]
    )
    role: str = Field(
        default="viewer",
        description="Papel do usuario: admin, operator, viewer",
        examples=["admin"]
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Valida se o role e valido."""
        allowed_roles = ["admin", "operator", "viewer"]
        if v not in allowed_roles:
            raise ValueError(f"Role deve ser um de: {', '.join(allowed_roles)}")
        return v


class UserCreate(UserBase):
    """
    Schema para criacao de Usuario.

    Inclui a senha que sera hasheada antes de salvar.
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Senha do usuario (minimo 8 caracteres)",
        examples=["senha_segura_123"]
    )
    is_active: bool = Field(default=True, description="Usuario ativo")
    is_superuser: bool = Field(default=False, description="Usuario administrador")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Valida requisitos minimos da senha."""
        if len(v) < 8:
            raise ValueError("Senha deve ter no minimo 8 caracteres")
        return v


class UserUpdate(BaseModel):
    """
    Schema para atualizacao de Usuario.

    Todos os campos sao opcionais.
    """

    email: Optional[EmailStr] = Field(None, description="Novo email")
    full_name: Optional[str] = Field(None, max_length=100, description="Novo nome completo")
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=100,
        description="Nova senha"
    )
    role: Optional[str] = Field(None, description="Novo papel")
    is_active: Optional[bool] = Field(None, description="Status ativo")
    avatar_url: Optional[str] = Field(None, description="URL do avatar")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Valida se o role e valido."""
        if v is None:
            return v
        allowed_roles = ["admin", "operator", "viewer"]
        if v not in allowed_roles:
            raise ValueError(f"Role deve ser um de: {', '.join(allowed_roles)}")
        return v


class UserResponse(UserBase):
    """
    Schema de resposta para Usuario.

    Exclui informacoes sensiveis como senha.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID do usuario")
    is_active: bool = Field(..., description="Usuario ativo")
    is_superuser: bool = Field(..., description="Usuario administrador")
    avatar_url: Optional[str] = Field(None, description="URL do avatar")
    created_at: datetime = Field(..., description="Data de criacao")
    updated_at: datetime = Field(..., description="Data da ultima atualizacao")
    last_login: Optional[datetime] = Field(None, description="Data do ultimo login")


class LoginRequest(BaseModel):
    """
    Schema para requisicao de login.
    """

    username: str = Field(
        ...,
        description="Nome de usuario ou email",
        examples=["admin"]
    )
    password: str = Field(
        ...,
        description="Senha do usuario",
        examples=["senha_segura_123"]
    )


class Token(BaseModel):
    """
    Schema de resposta com tokens de acesso.
    """

    access_token: str = Field(..., description="Token JWT de acesso")
    refresh_token: Optional[str] = Field(None, description="Token de refresh")
    token_type: str = Field(default="bearer", description="Tipo do token")
    expires_in: int = Field(..., description="Tempo de expiracao em segundos")
    user: UserResponse = Field(..., description="Dados do usuario autenticado")


class TokenPayload(BaseModel):
    """
    Schema do payload do token JWT.
    """

    sub: str = Field(..., description="Subject (username)")
    user_id: int = Field(..., description="ID do usuario")
    role: str = Field(..., description="Papel do usuario")
    exp: int = Field(..., description="Timestamp de expiracao")
    iat: int = Field(..., description="Timestamp de emissao")
    jti: Optional[str] = Field(None, description="JWT ID unico")


class PasswordChange(BaseModel):
    """
    Schema para alteracao de senha.
    """

    current_password: str = Field(..., description="Senha atual")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Nova senha"
    )
    confirm_password: str = Field(..., description="Confirmacao da nova senha")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Valida se as senhas conferem."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Senhas nao conferem")
        return v
