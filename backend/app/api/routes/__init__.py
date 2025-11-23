"""
Rotas da API do SkyCamOS.

Este pacote contem todos os endpoints organizados por dominio.
"""

from app.api.routes import analytics, auth, cameras, events, notifications, recordings, settings, stream

__all__ = [
    "analytics",
    "auth",
    "cameras",
    "events",
    "notifications",
    "recordings",
    "settings",
    "stream",
]
