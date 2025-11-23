"""
Rotas de Analytics do SkyCamOS.

Endpoints para deteccao de pessoas, contagem e line crossing.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.routes.auth import get_current_active_user
from app.models import User, Camera
from app.services.person_detection import person_detection_service, PersonDetectionEvent
from app.services.line_crossing import (
    line_crossing_service,
    VirtualLine,
    CrossingDirection,
    LineCrossingEvent
)
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Schemas ============

class LineCreate(BaseModel):
    """Schema para criar linha virtual."""
    id: str
    name: str
    start_point: List[int]  # [x, y]
    end_point: List[int]    # [x, y]
    direction: str = "both"  # in, out, both


class LineResponse(BaseModel):
    """Schema de resposta para linha."""
    id: str
    name: str
    start_point: List[int]
    end_point: List[int]
    direction: str


class DetectionConfig(BaseModel):
    """Schema de configuracao de deteccao."""
    confidence_threshold: float = 0.5
    cooldown_seconds: int = 5
    use_gpu: bool = False


class PersonDetectionStats(BaseModel):
    """Estatisticas de deteccao de pessoas."""
    camera_id: int
    is_running: bool
    total_detections: int
    total_persons_detected: int
    frames_processed: int
    last_detection: Optional[str]
    tracked_persons: int


class LineCrossingStats(BaseModel):
    """Estatisticas de line crossing."""
    camera_id: int
    is_running: bool
    lines: List[LineResponse]
    total_crossings: int
    counts_by_line: dict
    tracked_objects: int


# ============ Person Detection Endpoints ============

@router.post(
    "/person-detection/{camera_id}/start",
    summary="Iniciar deteccao de pessoas",
    description="Inicia a deteccao de pessoas em uma camera.",
)
async def start_person_detection(
    camera_id: int,
    config: DetectionConfig = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Inicia deteccao de pessoas para uma camera."""
    # Verifica se camera existe
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera nao encontrada"
        )

    config = config or DetectionConfig()

    success = await person_detection_service.start_detection(
        camera_id=camera_id,
        rtsp_url=camera.rtsp_url,
        confidence_threshold=config.confidence_threshold,
        cooldown_seconds=config.cooldown_seconds,
        use_gpu=config.use_gpu,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falha ao iniciar deteccao ou ja esta em execucao"
        )

    logger.info(f"Deteccao de pessoas iniciada para camera {camera_id}")

    return {"message": "Deteccao de pessoas iniciada", "camera_id": camera_id}


@router.post(
    "/person-detection/{camera_id}/stop",
    summary="Parar deteccao de pessoas",
)
async def stop_person_detection(
    camera_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Para deteccao de pessoas para uma camera."""
    await person_detection_service.stop_detection(camera_id)

    logger.info(f"Deteccao de pessoas parada para camera {camera_id}")

    return {"message": "Deteccao de pessoas parada", "camera_id": camera_id}


@router.get(
    "/person-detection/{camera_id}/stats",
    summary="Estatisticas de deteccao de pessoas",
)
async def get_person_detection_stats(
    camera_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Retorna estatisticas de deteccao de pessoas."""
    stats = person_detection_service.get_detector_stats(camera_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detector nao encontrado para esta camera"
        )

    return stats


@router.get(
    "/person-detection/stats",
    summary="Estatisticas globais de deteccao",
)
async def get_all_person_detection_stats(
    current_user: User = Depends(get_current_active_user),
):
    """Retorna estatisticas de todos os detectores."""
    return person_detection_service.get_all_stats()


# ============ Line Crossing Endpoints ============

@router.post(
    "/line-crossing/{camera_id}/start",
    summary="Iniciar deteccao de cruzamento de linha",
)
async def start_line_crossing(
    camera_id: int,
    lines: List[LineCreate] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Inicia deteccao de line crossing para uma camera."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera nao encontrada"
        )

    # Converte linhas
    virtual_lines = []
    if lines:
        for line in lines:
            virtual_lines.append(VirtualLine(
                id=line.id,
                name=line.name,
                start_point=tuple(line.start_point),
                end_point=tuple(line.end_point),
                direction=CrossingDirection(line.direction),
            ))

    success = await line_crossing_service.start_detection(
        camera_id=camera_id,
        rtsp_url=camera.rtsp_url,
        lines=virtual_lines,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falha ao iniciar line crossing ou ja esta em execucao"
        )

    logger.info(f"Line crossing iniciado para camera {camera_id}")

    return {"message": "Line crossing iniciado", "camera_id": camera_id}


@router.post(
    "/line-crossing/{camera_id}/stop",
    summary="Parar deteccao de cruzamento de linha",
)
async def stop_line_crossing(
    camera_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Para deteccao de line crossing para uma camera."""
    await line_crossing_service.stop_detection(camera_id)

    logger.info(f"Line crossing parado para camera {camera_id}")

    return {"message": "Line crossing parado", "camera_id": camera_id}


@router.post(
    "/line-crossing/{camera_id}/lines",
    summary="Adicionar linha virtual",
)
async def add_virtual_line(
    camera_id: int,
    line: LineCreate,
    current_user: User = Depends(get_current_active_user),
):
    """Adiciona uma linha virtual para deteccao."""
    virtual_line = VirtualLine(
        id=line.id,
        name=line.name,
        start_point=tuple(line.start_point),
        end_point=tuple(line.end_point),
        direction=CrossingDirection(line.direction),
    )

    success = line_crossing_service.add_line(camera_id, virtual_line)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detector nao encontrado para esta camera"
        )

    return {"message": "Linha adicionada", "line": line.dict()}


@router.delete(
    "/line-crossing/{camera_id}/lines/{line_id}",
    summary="Remover linha virtual",
)
async def remove_virtual_line(
    camera_id: int,
    line_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Remove uma linha virtual."""
    success = line_crossing_service.remove_line(camera_id, line_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detector ou linha nao encontrados"
        )

    return {"message": "Linha removida"}


@router.get(
    "/line-crossing/{camera_id}/counts",
    summary="Contagens de cruzamento",
)
async def get_crossing_counts(
    camera_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Retorna contagens de cruzamento."""
    counts = line_crossing_service.get_counts(camera_id)

    if counts is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detector nao encontrado para esta camera"
        )

    return counts


@router.post(
    "/line-crossing/{camera_id}/counts/reset",
    summary="Resetar contagens",
)
async def reset_crossing_counts(
    camera_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Reseta contagens de cruzamento."""
    success = line_crossing_service.reset_counts(camera_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detector nao encontrado"
        )

    return {"message": "Contagens resetadas"}


@router.get(
    "/line-crossing/{camera_id}/stats",
    summary="Estatisticas de line crossing",
)
async def get_line_crossing_stats(
    camera_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Retorna estatisticas de line crossing."""
    stats = line_crossing_service.get_detector_stats(camera_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detector nao encontrado"
        )

    return stats
