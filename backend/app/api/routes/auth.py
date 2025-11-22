"""
Rotas de Autenticacao do SkyCamOS.

Endpoints para login, logout, registro e gerenciamento de tokens.
"""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
    revoke_token,
    is_token_revoked,
)
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency para obter o usuario atual do token.

    Args:
        token: Token JWT do header Authorization.
        db: Sessao do banco de dados.

    Returns:
        User: Usuario autenticado.

    Raises:
        HTTPException: Se token invalido ou usuario nao encontrado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verifica se token foi revogado
    if is_token_revoked(token):
        raise credentials_exception

    # Valida token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    username = payload.get("sub")
    if username is None:
        raise credentials_exception

    # Busca usuario
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inativo",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency para verificar se usuario esta ativo.

    Args:
        current_user: Usuario atual.

    Returns:
        User: Usuario ativo.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inativo",
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency para verificar se usuario e admin.

    Args:
        current_user: Usuario atual.

    Returns:
        User: Usuario administrador.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user


@router.post(
    "/login",
    response_model=Token,
    summary="Login de usuario",
    description="Autentica usuario e retorna tokens de acesso.",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Realiza login do usuario.

    Args:
        form_data: Dados do formulario OAuth2 (username e password).
        db: Sessao do banco de dados.

    Returns:
        Token: Tokens de acesso e refresh.
    """
    # Busca usuario por username ou email
    result = await db.execute(
        select(User).where(
            (User.username == form_data.username) |
            (User.email == form_data.username)
        )
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inativo",
        )

    # Atualiza ultimo login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Gera tokens
    access_token = create_access_token(
        subject=user.username,
        user_id=user.id,
        role=user.role,
    )
    refresh_token = create_refresh_token(
        subject=user.username,
        user_id=user.id,
    )

    logger.info(f"Usuario {user.username} autenticado")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registro de usuario",
    description="Cria um novo usuario no sistema.",
)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Registra um novo usuario.

    Args:
        user_data: Dados do novo usuario.
        db: Sessao do banco de dados.

    Returns:
        UserResponse: Usuario criado.
    """
    # Verifica se username ja existe
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuario ja esta em uso",
        )

    # Verifica se email ja existe
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ja esta em uso",
        )

    # Cria usuario
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"Usuario {user.username} registrado")

    return UserResponse.model_validate(user)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Renovar token",
    description="Renova o token de acesso usando o refresh token.",
)
async def refresh_token(
    refresh_token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Renova o token de acesso.

    Args:
        refresh_token: Token de refresh.
        db: Sessao do banco de dados.

    Returns:
        Token: Novos tokens.
    """
    # Valida refresh token
    payload = verify_token(refresh_token, token_type="refresh")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido ou expirado",
        )

    # Busca usuario
    username = payload.get("sub")
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao encontrado ou inativo",
        )

    # Gera novos tokens
    new_access_token = create_access_token(
        subject=user.username,
        user_id=user.id,
        role=user.role,
    )
    new_refresh_token = create_refresh_token(
        subject=user.username,
        user_id=user.id,
    )

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Invalida o token de acesso atual.",
)
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    """
    Realiza logout invalidando o token.

    Args:
        token: Token de acesso atual.
    """
    revoke_token(token)
    logger.info("Token revogado via logout")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Dados do usuario atual",
    description="Retorna os dados do usuario autenticado.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """
    Retorna dados do usuario atual.

    Args:
        current_user: Usuario autenticado.

    Returns:
        UserResponse: Dados do usuario.
    """
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Atualizar perfil",
    description="Atualiza os dados do usuario autenticado.",
)
async def update_me(
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Atualiza dados do usuario atual.

    Args:
        user_data: Dados a atualizar.
        current_user: Usuario autenticado.
        db: Sessao do banco de dados.

    Returns:
        UserResponse: Usuario atualizado.
    """
    # Atualiza campos fornecidos
    if user_data.email is not None:
        # Verifica se email ja esta em uso
        result = await db.execute(
            select(User).where(
                (User.email == user_data.email) &
                (User.id != current_user.id)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email ja esta em uso",
            )
        current_user.email = user_data.email

    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name

    if user_data.password is not None:
        current_user.hashed_password = get_password_hash(user_data.password)

    if user_data.avatar_url is not None:
        current_user.avatar_url = user_data.avatar_url

    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)
