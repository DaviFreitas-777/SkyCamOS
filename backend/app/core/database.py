"""
Configuracao do Banco de Dados do SkyCamOS.

Este modulo configura a conexao com o banco de dados SQLite
utilizando SQLAlchemy async com aiosqlite.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """
    Classe base para todos os modelos SQLAlchemy.

    Todos os modelos devem herdar desta classe para
    serem incluidos nas migracoes e criacao de tabelas.
    """

    pass


# Configuracao do engine async para SQLite
# Para SQLite, usamos StaticPool para compatibilidade com async
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Session factory async
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency que fornece uma sessao de banco de dados.

    Utilizado como dependency injection no FastAPI para
    injetar uma sessao de banco em cada request.

    Yields:
        AsyncSession: Sessao do banco de dados.

    Example:
        @app.get("/cameras")
        async def get_cameras(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Erro na transacao do banco: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Inicializa o banco de dados.

    Cria todas as tabelas definidas nos modelos
    que herdam de Base.

    Deve ser chamado na inicializacao da aplicacao.
    """
    logger.info("Inicializando banco de dados...")

    async with engine.begin() as conn:
        # Importa todos os modelos para registrar nas metadata
        from app.models import Camera, Event, Recording, User  # noqa: F401

        # Cria todas as tabelas
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Banco de dados inicializado com sucesso.")


async def close_db() -> None:
    """
    Fecha conexoes com o banco de dados.

    Deve ser chamado no shutdown da aplicacao.
    """
    logger.info("Fechando conexoes do banco de dados...")
    await engine.dispose()
    logger.info("Conexoes do banco fechadas.")


async def create_initial_data() -> None:
    """
    Cria dados iniciais no banco de dados.

    Cria o usuario administrador padrao se nao existir.
    """
    from sqlalchemy import select

    from app.core.security import get_password_hash
    from app.models import User

    logger.info("Verificando dados iniciais...")

    async with async_session_factory() as session:
        # Verifica se ja existe um usuario admin
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()

        if admin is None:
            logger.info("Criando usuario administrador padrao...")

            admin = User(
                username="admin",
                email="admin@skycamos.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrador",
                is_active=True,
                is_superuser=True,
                role="admin",
            )
            session.add(admin)
            await session.commit()

            logger.info(
                "Usuario admin criado. Login: admin / Senha: admin123 "
                "(ALTERE A SENHA EM PRODUCAO!)"
            )
        else:
            logger.info("Usuario admin ja existe.")


async def check_db_connection() -> bool:
    """
    Verifica se a conexao com o banco esta funcionando.

    Returns:
        bool: True se a conexao esta OK, False caso contrario.
    """
    from sqlalchemy import text

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Erro ao verificar conexao com banco: {e}")
        return False
