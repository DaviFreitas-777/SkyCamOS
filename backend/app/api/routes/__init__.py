"""
Rotas da API do SkyCamOS.

Este pacote contem todos os endpoints organizados por dominio.
"""

from app.api.routes import analytics, auth, cameras, events, export, health, notifications, recordings, settings, storage, stream

__all__ = [
    "analytics",
    "auth",
    "cameras",
    "events",
    "export",
    "health",
    "notifications",
    "recordings",
    "settings",
    "storage",
    "stream",
]
