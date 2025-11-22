"""
Schemas Pydantic do SkyCamOS.

Este pacote contem todos os schemas de validacao
utilizados pela API para entrada e saida de dados.
"""

from app.schemas.camera import (
    CameraBase,
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraListResponse,
    CameraStatusUpdate,
)
from app.schemas.event import (
    EventBase,
    EventCreate,
    EventResponse,
    EventListResponse,
    EventAcknowledge,
)
from app.schemas.recording import (
    RecordingBase,
    RecordingCreate,
    RecordingResponse,
    RecordingListResponse,
    RecordingUpdate,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    TokenPayload,
    LoginRequest,
)

__all__ = [
    # Camera
    "CameraBase",
    "CameraCreate",
    "CameraUpdate",
    "CameraResponse",
    "CameraListResponse",
    "CameraStatusUpdate",
    # Event
    "EventBase",
    "EventCreate",
    "EventResponse",
    "EventListResponse",
    "EventAcknowledge",
    # Recording
    "RecordingBase",
    "RecordingCreate",
    "RecordingResponse",
    "RecordingListResponse",
    "RecordingUpdate",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "Token",
    "TokenPayload",
    "LoginRequest",
]
