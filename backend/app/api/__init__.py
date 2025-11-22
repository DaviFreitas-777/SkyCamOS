"""
API do SkyCamOS.

Este pacote contem as rotas e endpoints da API REST.
"""

from fastapi import APIRouter

from app.api.routes import auth, cameras, events, recordings, stream

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
