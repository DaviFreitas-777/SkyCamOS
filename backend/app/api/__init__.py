"""
API do SkyCamOS.

Este pacote contem as rotas e endpoints da API REST.
"""

from fastapi import APIRouter

from app.api.routes import analytics, auth, cameras, events, export, health, notifications, recordings, settings, storage, stream

# Router principal da API
api_router = APIRouter()

# Inclui rotas de cada modulo
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Autenticacao"],
)

api_router.include_router(
    cameras.router,
    prefix="/cameras",
    tags=["Cameras"],
)

api_router.include_router(
    recordings.router,
    prefix="/recordings",
    tags=["Gravacoes"],
)

api_router.include_router(
    events.router,
    prefix="/events",
    tags=["Eventos"],
)

api_router.include_router(
    stream.router,
    prefix="/stream",
    tags=["Streaming"],
)

api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["Notificacoes"],
)

api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["Configuracoes"],
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"],
)

api_router.include_router(
    storage.router,
    prefix="/storage",
    tags=["Storage"],
)

api_router.include_router(
    export.router,
    prefix="/export",
    tags=["Exportacao"],
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)
