"""
Aplicacao Principal do SkyCamOS Backend.

Este modulo inicializa a aplicacao FastAPI, configura middlewares,
rotas e eventos de lifecycle.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import api_router
from app.config import settings
from app.core.database import close_db, create_initial_data, init_db
from app.services.storage_manager import storage_manager

# Configuracao de logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia o ciclo de vida da aplicacao.

    Executa inicializacoes no startup e limpezas no shutdown.

    Args:
        app: Instancia da aplicacao FastAPI.

    Yields:
        None: Controle para a aplicacao executar.
    """
    # Startup
    logger.info(f"Iniciando {settings.app_name} v{__version__}")

    try:
        # Inicializa banco de dados
        await init_db()

        # Cria dados iniciais (usuario admin)
        await create_initial_data()

        # Inicia gerenciador de armazenamento
        await storage_manager.start()

        logger.info("Aplicacao iniciada com sucesso")

    except Exception as e:
        logger.error(f"Erro na inicializacao: {e}")
        raise

    yield

    # Shutdown
    logger.info("Encerrando aplicacao...")

    try:
        # Para servicos
        await storage_manager.stop()

        # Fecha conexoes de banco
        await close_db()

        logger.info("Aplicacao encerrada com sucesso")

    except Exception as e:
        logger.error(f"Erro no encerramento: {e}")


# Cria aplicacao FastAPI
app = FastAPI(
    title=settings.app_name,
    description="""
    ## SkyCamOS - Sistema de Monitoramento de Cameras IP

    API REST para gerenciamento de cameras de vigilancia, gravacoes e eventos.

    ### Funcionalidades

    * **Cameras**: CRUD de cameras IP, descoberta ONVIF, teste de conexao
    * **Gravacoes**: Listagem, download, streaming de videos gravados
    * **Eventos**: Alertas de movimento, notificacoes, reconhecimento
    * **Streaming**: MJPEG, WebSocket para video em tempo real
    * **Autenticacao**: JWT com refresh token

    ### Autenticacao

    Use o endpoint `/api/v1/auth/login` para obter um token de acesso.
    Inclua o token no header `Authorization: Bearer <token>` nas requisicoes.
    """,
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Middleware CORS - permite qualquer origem em desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite qualquer origem (ajustar em producao)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Handler de erros de validacao
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handler para erros de validacao de request.

    Args:
        request: Request que causou o erro.
        exc: Excecao de validacao.

    Returns:
        JSONResponse: Resposta de erro formatada.
    """
    errors = []
    for error in exc.errors():
        loc = " -> ".join(str(x) for x in error["loc"])
        errors.append({
            "field": loc,
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Erro de validacao",
            "errors": errors,
        },
    )


# Handler de erros genericos
@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handler para erros genericos nao tratados.

    Args:
        request: Request que causou o erro.
        exc: Excecao ocorrida.

    Returns:
        JSONResponse: Resposta de erro.
    """
    logger.error(f"Erro nao tratado: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Erro interno do servidor",
            "message": str(exc) if settings.debug else "Ocorreu um erro inesperado",
        },
    )


# Inclui rotas da API
app.include_router(api_router, prefix="/api/v1")


# Rotas de health check
@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Verifica se a aplicacao esta funcionando.",
)
async def health_check() -> dict:
    """
    Endpoint de health check.

    Returns:
        dict: Status da aplicacao.
    """
    return {
        "status": "healthy",
        "version": __version__,
        "environment": settings.environment,
    }


@app.get(
    "/health/ready",
    tags=["Health"],
    summary="Readiness Check",
    description="Verifica se a aplicacao esta pronta para receber requisicoes.",
)
async def readiness_check() -> dict:
    """
    Endpoint de readiness check.

    Verifica se todos os servicos estao prontos.

    Returns:
        dict: Status de prontidao.
    """
    from app.core.database import check_db_connection

    # Verifica banco de dados
    db_ok = await check_db_connection()

    # Verifica armazenamento
    storage_info = storage_manager.get_storage_info()
    storage_ok = storage_info.free_bytes > 0

    all_ok = db_ok and storage_ok

    return {
        "ready": all_ok,
        "checks": {
            "database": "ok" if db_ok else "error",
            "storage": "ok" if storage_ok else "error",
        },
    }


@app.get(
    "/",
    tags=["Root"],
    summary="Root",
    description="Endpoint raiz da API.",
)
async def root() -> dict:
    """
    Endpoint raiz.

    Returns:
        dict: Informacoes basicas da API.
    """
    return {
        "name": settings.app_name,
        "version": __version__,
        "docs": "/docs" if settings.debug else None,
        "api": "/api/v1",
    }


# Ponto de entrada para execucao direta
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
