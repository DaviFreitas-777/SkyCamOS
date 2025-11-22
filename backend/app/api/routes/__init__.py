"""
Rotas da API do SkyCamOS.

Este pacote contem todos os endpoints organizados por dominio.
"""

from app.api.routes import auth, cameras, events, recordings, stream

__all__ = [
    "auth",
    "cameras",
    "events",
    "recordings",
    "stream",
]
