"""
Modelos SQLAlchemy do SkyCamOS.

Este pacote contem todos os modelos de banco de dados
utilizados pela aplicacao.
"""

from app.models.camera import Camera
from app.models.event import Event
from app.models.recording import Recording
from app.models.user import User
from app.models.storage_pool import StoragePool, CameraStorageAssignment

__all__ = [
    "Camera",
    "Event",
    "Recording",
    "User",
    "StoragePool",
    "CameraStorageAssignment",
]
