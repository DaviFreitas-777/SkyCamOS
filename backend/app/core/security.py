"""
Modulo de Seguranca do SkyCamOS.

Este modulo implementa funcionalidades de seguranca,
incluindo hashing de senhas, geracao e validacao de tokens JWT.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger(__name__)

# Contexto para hashing de senhas usando bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde ao hash.

    Args:
        plain_password: Senha em texto plano.
        hashed_password: Hash da senha armazenada.

    Returns:
        bool: True se a senha corresponde, False caso contrario.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Erro ao verificar senha: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Gera o hash de uma senha.

    Args:
        password: Senha em texto plano.

    Returns:
        str: Hash da senha.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    user_id: int,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Cria um token JWT de acesso.

    Args:
        subject: Subject do token (geralmente username).
        user_id: ID do usuario.
        role: Papel/role do usuario.
        expires_delta: Tempo de expiracao customizado.

    Returns:
        str: Token JWT codificado.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "sub": subject,
        "user_id": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
        "type": "access",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    return encoded_jwt


def create_refresh_token(
    subject: str,
    user_id: int,
) -> str:
    """
    Cria um token JWT de refresh.

    Args:
        subject: Subject do token (geralmente username).
        user_id: ID do usuario.

    Returns:
        str: Token JWT de refresh codificado.
    """
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    to_encode = {
        "sub": subject,
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict[str, Any]]:
    """
    Verifica e decodifica um token JWT.

    Args:
        token: Token JWT a ser verificado.
        token_type: Tipo esperado do token (access ou refresh).

    Returns:
        Optional[dict]: Payload do token se valido, None caso contrario.

    Raises:
        JWTError: Se o token for invalido ou expirado.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        # Verifica o tipo do token
        if payload.get("type") != token_type:
            logger.warning(f"Tipo de token invalido: esperado {token_type}")
            return None

        # Verifica se tem os campos obrigatorios
        if "sub" not in payload or "user_id" not in payload:
            logger.warning("Token sem campos obrigatorios")
            return None

        return payload

    except JWTError as e:
        logger.warning(f"Erro ao verificar token: {e}")
        return None


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decodifica um token JWT sem validar expiracao.

    Util para inspecao de tokens.

    Args:
        token: Token JWT a ser decodificado.

    Returns:
        Optional[dict]: Payload do token, None se invalido.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": False},
        )
        return payload
    except JWTError as e:
        logger.warning(f"Erro ao decodificar token: {e}")
        return None


class TokenBlacklist:
    """
    Gerenciador de blacklist de tokens.

    Armazena tokens revogados em memoria.
    Em producao, considere usar Redis.
    """

    def __init__(self) -> None:
        """Inicializa a blacklist."""
        self._blacklist: set[str] = set()

    def add(self, jti: str) -> None:
        """
        Adiciona um token a blacklist.

        Args:
            jti: JWT ID do token a ser revogado.
        """
        self._blacklist.add(jti)
        logger.info(f"Token {jti[:8]}... adicionado a blacklist")

    def is_blacklisted(self, jti: str) -> bool:
        """
        Verifica se um token esta na blacklist.

        Args:
            jti: JWT ID a verificar.

        Returns:
            bool: True se esta na blacklist.
        """
        return jti in self._blacklist

    def remove_expired(self) -> None:
        """
        Remove tokens expirados da blacklist.

        Deve ser chamado periodicamente para limpar memoria.
        """
        # TODO: Implementar limpeza baseada em expiracao
        pass

    def clear(self) -> None:
        """Limpa toda a blacklist."""
        self._blacklist.clear()
        logger.info("Blacklist de tokens limpa")


# Instancia global da blacklist
token_blacklist = TokenBlacklist()


def revoke_token(token: str) -> bool:
    """
    Revoga um token adicionando-o a blacklist.

    Args:
        token: Token JWT a ser revogado.

    Returns:
        bool: True se revogado com sucesso.
    """
    payload = decode_token(token)
    if payload and "jti" in payload:
        token_blacklist.add(payload["jti"])
        return True
    return False


def is_token_revoked(token: str) -> bool:
    """
    Verifica se um token foi revogado.

    Args:
        token: Token JWT a verificar.

    Returns:
        bool: True se foi revogado.
    """
    payload = decode_token(token)
    if payload and "jti" in payload:
        return token_blacklist.is_blacklisted(payload["jti"])
    return True  # Token invalido e considerado revogado


# Funcoes de autorizacao baseada em roles


def check_permission(user_role: str, required_roles: list[str]) -> bool:
    """
    Verifica se o usuario tem permissao baseado no role.

    Args:
        user_role: Role atual do usuario.
        required_roles: Lista de roles permitidos.

    Returns:
        bool: True se tem permissao.
    """
    # Admin tem acesso a tudo
    if user_role == "admin":
        return True

    return user_role in required_roles


def can_view_cameras(role: str) -> bool:
    """Verifica se pode visualizar cameras."""
    return check_permission(role, ["admin", "operator", "viewer"])


def can_manage_cameras(role: str) -> bool:
    """Verifica se pode gerenciar cameras (CRUD)."""
    return check_permission(role, ["admin", "operator"])


def can_manage_users(role: str) -> bool:
    """Verifica se pode gerenciar usuarios."""
    return check_permission(role, ["admin"])


def can_manage_recordings(role: str) -> bool:
    """Verifica se pode gerenciar gravacoes."""
    return check_permission(role, ["admin", "operator"])


def can_acknowledge_events(role: str) -> bool:
    """Verifica se pode reconhecer eventos."""
    return check_permission(role, ["admin", "operator"])
