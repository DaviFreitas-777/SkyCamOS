"""
Rotas de Configuracoes do SkyCamOS.

Endpoints para gerenciamento de configuracoes do sistema.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings as app_settings
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


class GeneralSettings(BaseModel):
    """Configuracoes gerais do sistema."""
    app_name: str = "SkyCamOS"
    language: str = "pt-BR"
    timezone: str = "America/Sao_Paulo"
    date_format: str = "DD/MM/YYYY"
    time_format: str = "24h"


class RecordingSettings(BaseModel):
    """Configuracoes de gravacao."""
    enabled: bool = True
    mode: str = "continuous"  # continuous, motion, scheduled
    retention_days: int = 30
    max_storage_gb: int = 100
    quality: str = "high"  # low, medium, high


class NotificationSettings(BaseModel):
    """Configuracoes de notificacoes."""
    push_enabled: bool = True
    email_enabled: bool = False
    sound_enabled: bool = True
    motion_alerts: bool = True
    offline_alerts: bool = True


class MotionSettings(BaseModel):
    """Configuracoes de deteccao de movimento."""
    enabled: bool = True
    sensitivity: int = 50  # 0-100
    min_area: int = 500
    cooldown_seconds: int = 5


class SystemSettings(BaseModel):
    """Todas as configuracoes do sistema."""
    general: GeneralSettings = GeneralSettings()
    recording: RecordingSettings = RecordingSettings()
    notifications: NotificationSettings = NotificationSettings()
    motion: MotionSettings = MotionSettings()


class SettingsUpdateRequest(BaseModel):
    """Request para atualizacao de configuracoes."""
    general: Optional[GeneralSettings] = None
    recording: Optional[RecordingSettings] = None
    notifications: Optional[NotificationSettings] = None
    motion: Optional[MotionSettings] = None


# Armazenamento em memoria (em producao, salvar no banco)
current_settings = SystemSettings()


@router.get("", response_model=SystemSettings)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna todas as configuracoes do sistema.
    """
    # Atualizar com valores reais do config.py onde aplicavel
    settings_response = SystemSettings(
        general=GeneralSettings(
            app_name=app_settings.app_name,
        ),
        recording=RecordingSettings(
            retention_days=app_settings.retention_days,
            max_storage_gb=app_settings.max_storage_gb,
        ),
        notifications=NotificationSettings(
            push_enabled=app_settings.push_notification_enabled,
        ),
        motion=MotionSettings(
            sensitivity=100 - app_settings.motion_threshold,  # Inverter para UI
            min_area=app_settings.motion_min_area,
            cooldown_seconds=app_settings.motion_cooldown_seconds,
        ),
    )

    return settings_response


@router.put("", response_model=SystemSettings)
async def update_settings(
    settings_update: SettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza configuracoes do sistema.

    Requer permissao de administrador.
    """
    # Verificar se usuario e admin
    if current_user.role != "admin" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar configuracoes")

    global current_settings

    if settings_update.general:
        current_settings.general = settings_update.general

    if settings_update.recording:
        current_settings.recording = settings_update.recording

    if settings_update.notifications:
        current_settings.notifications = settings_update.notifications

    if settings_update.motion:
        current_settings.motion = settings_update.motion

    logger.info(f"Configuracoes atualizadas por {current_user.username}")

    return current_settings


@router.get("/storage")
async def get_storage_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna informacoes de uso de armazenamento.
    """
    import shutil
    from pathlib import Path

    recordings_path = Path(app_settings.recordings_path)

    # Calcular uso de disco
    try:
        if recordings_path.exists():
            total, used, free = shutil.disk_usage(recordings_path)
        else:
            total, used, free = shutil.disk_usage(".")

        # Calcular espaco usado pelas gravacoes
        recordings_size = 0
        if recordings_path.exists():
            for file in recordings_path.rglob("*"):
                if file.is_file():
                    recordings_size += file.stat().st_size

        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "recordings_gb": round(recordings_size / (1024**3), 2),
            "max_storage_gb": app_settings.max_storage_gb,
            "retention_days": app_settings.retention_days,
        }
    except Exception as e:
        logger.error(f"Erro ao obter info de armazenamento: {e}")
        return {
            "total_gb": 0,
            "used_gb": 0,
            "free_gb": 0,
            "recordings_gb": 0,
            "max_storage_gb": app_settings.max_storage_gb,
            "retention_days": app_settings.retention_days,
        }


@router.get("/system")
async def get_system_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna informacoes do sistema.
    """
    import platform
    import sys

    return {
        "app_name": app_settings.app_name,
        "app_version": app_settings.app_version,
        "environment": app_settings.environment,
        "python_version": sys.version,
        "platform": platform.system(),
        "platform_version": platform.version(),
        "debug": app_settings.debug,
    }
