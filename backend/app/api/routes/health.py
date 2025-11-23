"""
Rotas de Health Check do SkyCamOS.

Endpoints para verificar o status da aplicacao.
"""

import logging
import time
from datetime import datetime

from fastapi import APIRouter

from app import __version__
from app.config import settings
from app.core.database import check_db_connection
from app.services.storage_manager import storage_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Timestamp de inicio da aplicacao
_start_time = time.time()


def get_uptime() -> str:
    """
    Calcula o tempo de atividade da aplicacao.

    Returns:
        str: Uptime formatado (ex: "2d 5h 30m 15s")
    """
    elapsed = int(time.time() - _start_time)

    days = elapsed // 86400
    hours = (elapsed % 86400) // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")

    return " ".join(parts)


def get_uptime_seconds() -> int:
    """
    Retorna o tempo de atividade em segundos.

    Returns:
        int: Uptime em segundos
    """
    return int(time.time() - _start_time)


@router.get(
    "",
    summary="Health Check",
    description="Verifica se a API esta funcionando corretamente.",
)
async def health_check() -> dict:
    """
    Endpoint de health check basico.

    Returns:
        dict: Status da aplicacao.
    """
    return {
        "status": "ok",
        "version": __version__,
        "uptime": get_uptime(),
        "uptime_seconds": get_uptime_seconds(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/detailed",
    summary="Health Check Detalhado",
    description="Retorna informacoes detalhadas do status da aplicacao.",
)
async def health_check_detailed() -> dict:
    """
    Endpoint de health check detalhado.

    Verifica todos os servicos e retorna status completo.

    Returns:
        dict: Status detalhado da aplicacao.
    """
    # Verifica banco de dados
    db_ok = await check_db_connection()

    # Verifica armazenamento
    try:
        storage_info = storage_manager.get_storage_info()
        storage_ok = storage_info.free_bytes > 0
        storage_details = {
            "total_bytes": storage_info.total_bytes,
            "free_bytes": storage_info.free_bytes,
            "used_percent": storage_info.used_percent,
        }
    except Exception as e:
        storage_ok = False
        storage_details = {"error": str(e)}

    # Status geral
    all_ok = db_ok and storage_ok

    return {
        "status": "ok" if all_ok else "degraded",
        "version": __version__,
        "uptime": get_uptime(),
        "uptime_seconds": get_uptime_seconds(),
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "checks": {
            "database": {
                "status": "ok" if db_ok else "error",
                "type": "sqlite",
            },
            "storage": {
                "status": "ok" if storage_ok else "error",
                **storage_details,
            },
        },
    }


@router.get(
    "/live",
    summary="Liveness Probe",
    description="Probe de liveness para Kubernetes/Docker.",
)
async def liveness_probe() -> dict:
    """
    Probe de liveness - verifica se a aplicacao esta viva.

    Returns:
        dict: Status de liveness.
    """
    return {"status": "alive"}


@router.get(
    "/ready",
    summary="Readiness Probe",
    description="Probe de readiness para Kubernetes/Docker.",
)
async def readiness_probe() -> dict:
    """
    Probe de readiness - verifica se a aplicacao esta pronta.

    Returns:
        dict: Status de readiness.
    """
    db_ok = await check_db_connection()

    if not db_ok:
        return {
            "status": "not_ready",
            "reason": "database_unavailable",
        }

    return {"status": "ready"}
