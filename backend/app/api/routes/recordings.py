"""
Rotas de Gravacoes do SkyCamOS.

Endpoints para listar, visualizar e gerenciar gravacoes de video.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_active_user, get_current_admin_user
from app.config import settings
from app.core.database import get_db
from app.models.recording import Recording, RecordingStatus
from app.models.user import User
from app.schemas.recording import (
    RecordingListResponse,
    RecordingResponse,
    RecordingUpdate,
    RecordingFilter,
    StorageStats,
)
from app.services.storage_manager import storage_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=RecordingListResponse,
    summary="Listar gravacoes",
    description="Retorna lista paginada de gravacoes.",
)
async def list_recordings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1, description="Numero da pagina"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por pagina"),
    camera_id: Optional[int] = Query(None, description="Filtrar por camera"),
    recording_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrar por status"),
    start_date: Optional[datetime] = Query(None, description="Data inicial"),
    end_date: Optional[datetime] = Query(None, description="Data final"),
    has_motion: Optional[bool] = Query(None, description="Apenas com movimento"),
    is_starred: Optional[bool] = Query(None, description="Apenas favoritas"),
) -> RecordingListResponse:
    """
    Lista gravacoes com paginacao e filtros.

    Args:
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.
        page: Numero da pagina.
        page_size: Itens por pagina.
        camera_id: Filtro por camera.
        recording_type: Filtro por tipo.
        status_filter: Filtro por status.
        start_date: Data inicial.
        end_date: Data final.
        has_motion: Filtro por movimento.
        is_starred: Filtro por favoritas.

    Returns:
        RecordingListResponse: Lista paginada de gravacoes.
    """
    # Query base
    query = select(Recording)

    # Filtros
    if camera_id:
        query = query.where(Recording.camera_id == camera_id)

    if recording_type:
        query = query.where(Recording.recording_type == recording_type)

    if status_filter:
        query = query.where(Recording.status == status_filter)

    if start_date:
        query = query.where(Recording.start_time >= start_date)

    if end_date:
        query = query.where(Recording.start_time <= end_date)

    if has_motion is not None:
        query = query.where(Recording.has_motion == has_motion)

    if is_starred is not None:
        query = query.where(Recording.is_starred == is_starred)

    # Conta total
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Calcula totais
    totals_query = select(
        func.sum(Recording.file_size_bytes),
        func.sum(Recording.duration_seconds),
    ).select_from(query.subquery())
    result = await db.execute(totals_query)
    totals = result.first()
    total_size = totals[0] or 0
    total_duration = totals[1] or 0

    # Paginacao
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Recording.start_time.desc())

    # Executa query
    result = await db.execute(query)
    recordings = result.scalars().all()

    # Calcula total de paginas
    pages = (total + page_size - 1) // page_size

    return RecordingListResponse(
        items=[RecordingResponse.model_validate(r) for r in recordings],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        total_size_bytes=total_size,
        total_duration_seconds=total_duration,
    )


@router.get(
    "/stats",
    response_model=StorageStats,
    summary="Estatisticas de armazenamento",
    description="Retorna estatisticas de uso do armazenamento.",
)
async def get_storage_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StorageStats:
    """
    Retorna estatisticas de armazenamento.

    Args:
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        StorageStats: Estatisticas de armazenamento.
    """
    # Consulta estatisticas do banco
    result = await db.execute(
        select(
            func.count(Recording.id),
            func.sum(Recording.file_size_bytes),
            func.sum(Recording.duration_seconds),
            func.min(Recording.start_time),
            func.max(Recording.start_time),
        )
    )
    stats = result.first()

    total_recordings = stats[0] or 0
    total_size = stats[1] or 0
    total_duration = stats[2] or 0
    oldest = stats[3]
    newest = stats[4]

    # Por tipo
    result = await db.execute(
        select(
            Recording.recording_type,
            func.count(Recording.id),
        ).group_by(Recording.recording_type)
    )
    by_type = {row[0]: row[1] for row in result.all()}

    # Por camera
    result = await db.execute(
        select(
            Recording.camera_id,
            func.count(Recording.id),
        ).group_by(Recording.camera_id)
    )
    by_camera = {str(row[0]): row[1] for row in result.all()}

    # Info de disco
    storage_info = storage_manager.get_storage_info()

    # Formata duracao total
    hours = int(total_duration // 3600)
    minutes = int((total_duration % 3600) // 60)
    duration_formatted = f"{hours}h {minutes}m"

    return StorageStats(
        total_recordings=total_recordings,
        total_size_bytes=total_size,
        total_size_formatted=f"{total_size / (1024**3):.2f} GB",
        total_duration_seconds=total_duration,
        total_duration_formatted=duration_formatted,
        oldest_recording=oldest,
        newest_recording=newest,
        storage_used_percent=storage_info.used_percent,
        storage_available_bytes=storage_info.free_bytes,
        recordings_by_type=by_type,
        recordings_by_camera=by_camera,
    )


@router.get(
    "/{recording_id}",
    response_model=RecordingResponse,
    summary="Obter gravacao",
    description="Retorna detalhes de uma gravacao especifica.",
)
async def get_recording(
    recording_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RecordingResponse:
    """
    Obtem uma gravacao pelo ID.

    Args:
        recording_id: ID da gravacao.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        RecordingResponse: Dados da gravacao.
    """
    result = await db.execute(
        select(Recording).where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()

    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gravacao nao encontrada",
        )

    return RecordingResponse.model_validate(recording)


@router.put(
    "/{recording_id}",
    response_model=RecordingResponse,
    summary="Atualizar gravacao",
    description="Atualiza metadados de uma gravacao.",
)
async def update_recording(
    recording_id: int,
    recording_data: RecordingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RecordingResponse:
    """
    Atualiza uma gravacao.

    Args:
        recording_id: ID da gravacao.
        recording_data: Dados a atualizar.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        RecordingResponse: Gravacao atualizada.
    """
    result = await db.execute(
        select(Recording).where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()

    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gravacao nao encontrada",
        )

    # Atualiza campos
    update_data = recording_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(recording, field):
            setattr(recording, field, value)

    await db.commit()
    await db.refresh(recording)

    return RecordingResponse.model_validate(recording)


@router.delete(
    "/{recording_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir gravacao",
    description="Remove uma gravacao do sistema.",
)
async def delete_recording(
    recording_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """
    Exclui uma gravacao.

    Args:
        recording_id: ID da gravacao.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.
    """
    result = await db.execute(
        select(Recording).where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()

    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gravacao nao encontrada",
        )

    if recording.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Gravacao protegida contra exclusao",
        )

    # Remove arquivo
    try:
        filepath = Path(recording.filepath)
        if filepath.exists():
            filepath.unlink()
    except Exception as e:
        logger.error(f"Erro ao remover arquivo: {e}")

    await db.delete(recording)
    await db.commit()

    logger.info(f"Gravacao excluida: {recording.filename}")


@router.get(
    "/{recording_id}/download",
    summary="Download de gravacao",
    description="Faz download do arquivo de video.",
)
async def download_recording(
    recording_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Download de uma gravacao.

    Args:
        recording_id: ID da gravacao.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        FileResponse: Arquivo de video.
    """
    result = await db.execute(
        select(Recording).where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()

    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gravacao nao encontrada",
        )

    filepath = Path(recording.filepath)

    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo de video nao encontrado",
        )

    return FileResponse(
        path=filepath,
        filename=recording.filename,
        media_type="video/mp4",
    )


@router.get(
    "/{recording_id}/stream",
    summary="Stream de gravacao",
    description="Transmite o video para visualizacao.",
)
async def stream_recording(
    recording_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Stream de uma gravacao.

    Args:
        recording_id: ID da gravacao.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        StreamingResponse: Stream de video.
    """
    result = await db.execute(
        select(Recording).where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()

    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gravacao nao encontrada",
        )

    filepath = Path(recording.filepath)

    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo de video nao encontrado",
        )

    def iterfile():
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):  # 64KB chunks
                yield chunk

    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(filepath.stat().st_size),
        },
    )


@router.post(
    "/{recording_id}/lock",
    response_model=RecordingResponse,
    summary="Proteger gravacao",
    description="Protege uma gravacao contra exclusao automatica.",
)
async def lock_recording(
    recording_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RecordingResponse:
    """
    Protege uma gravacao.

    Args:
        recording_id: ID da gravacao.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        RecordingResponse: Gravacao atualizada.
    """
    result = await db.execute(
        select(Recording).where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()

    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gravacao nao encontrada",
        )

    recording.is_locked = True
    await db.commit()
    await db.refresh(recording)

    return RecordingResponse.model_validate(recording)


@router.post(
    "/{recording_id}/unlock",
    response_model=RecordingResponse,
    summary="Desproteger gravacao",
    description="Remove a protecao de uma gravacao.",
)
async def unlock_recording(
    recording_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RecordingResponse:
    """
    Remove protecao de uma gravacao.

    Args:
        recording_id: ID da gravacao.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        RecordingResponse: Gravacao atualizada.
    """
    result = await db.execute(
        select(Recording).where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()

    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gravacao nao encontrada",
        )

    recording.is_locked = False
    await db.commit()
    await db.refresh(recording)

    return RecordingResponse.model_validate(recording)


@router.post(
    "/cleanup",
    summary="Limpeza de armazenamento",
    description="Executa limpeza manual do armazenamento.",
)
async def cleanup_storage(
    current_user: Annotated[User, Depends(get_current_admin_user)],
) -> dict:
    """
    Executa limpeza de armazenamento.

    Args:
        current_user: Usuario administrador.

    Returns:
        dict: Resultado da limpeza.
    """
    result = await storage_manager.cleanup()
    return result
