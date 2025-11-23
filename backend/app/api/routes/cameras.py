"""
Rotas de Cameras do SkyCamOS.

Endpoints para CRUD de cameras, descoberta ONVIF e testes de conexao.
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_active_user, get_current_admin_user
from app.core.database import get_db
from app.models.camera import Camera, CameraStatus
from app.models.user import User
from app.schemas.camera import (
    CameraCreate,
    CameraListResponse,
    CameraResponse,
    CameraUpdate,
    CameraStatusUpdate,
    CameraDiscovery,
    CameraTestConnection,
    CameraTestResult,
)
from app.services.onvif_discovery import onvif_discovery_service
from app.services.ssdp_discovery import ssdp_discovery_service
from app.services.stream_service import stream_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=CameraListResponse,
    summary="Listar cameras",
    description="Retorna lista paginada de cameras cadastradas.",
)
async def list_cameras(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1, description="Numero da pagina"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por pagina"),
    status_filter: Optional[str] = Query(None, description="Filtrar por status"),
    search: Optional[str] = Query(None, description="Busca por nome ou IP"),
    enabled_only: bool = Query(False, description="Apenas cameras habilitadas"),
) -> CameraListResponse:
    """
    Lista cameras com paginacao e filtros.

    Args:
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.
        page: Numero da pagina.
        page_size: Itens por pagina.
        status_filter: Filtro de status.
        search: Termo de busca.
        enabled_only: Apenas habilitadas.

    Returns:
        CameraListResponse: Lista paginada de cameras.
    """
    # Query base
    query = select(Camera)

    # Filtros
    if status_filter:
        query = query.where(Camera.status == status_filter)

    if enabled_only:
        query = query.where(Camera.is_enabled == True)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Camera.name.ilike(search_term)) |
            (Camera.ip_address.ilike(search_term)) |
            (Camera.description.ilike(search_term))
        )

    # Conta total
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Paginacao
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Camera.name)

    # Executa query
    result = await db.execute(query)
    cameras = result.scalars().all()

    # Calcula total de paginas
    pages = (total + page_size - 1) // page_size

    return CameraListResponse(
        items=[CameraResponse.model_validate(c) for c in cameras],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Obter camera",
    description="Retorna detalhes de uma camera especifica.",
)
async def get_camera(
    camera_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> CameraResponse:
    """
    Obtem uma camera pelo ID.

    Args:
        camera_id: ID da camera.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        CameraResponse: Dados da camera.
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera nao encontrada",
        )

    return CameraResponse.model_validate(camera)


@router.post(
    "",
    response_model=CameraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar camera",
    description="Cadastra uma nova camera no sistema.",
)
async def create_camera(
    camera_data: CameraCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> CameraResponse:
    """
    Cria uma nova camera.

    Args:
        camera_data: Dados da camera.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        CameraResponse: Camera criada.
    """
    # Verifica permissao
    if not current_user.can_manage_cameras:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissao para criar cameras",
        )

    # Verifica se IP ja existe
    result = await db.execute(
        select(Camera).where(Camera.ip_address == camera_data.ip_address)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ja existe uma camera com este IP",
        )

    # Cria camera
    camera = Camera(
        name=camera_data.name,
        description=camera_data.description,
        ip_address=camera_data.ip_address,
        port=camera_data.port,
        protocol=camera_data.protocol,
        username=camera_data.username,
        password=camera_data.password,
        rtsp_url=camera_data.rtsp_url,
        rtsp_substream_url=camera_data.rtsp_substream_url,
        onvif_path=camera_data.onvif_path,
        manufacturer=camera_data.manufacturer,
        model=camera_data.model,
        motion_detection_enabled=camera_data.motion_detection_enabled,
        audio_enabled=camera_data.audio_enabled,
        resolution_width=camera_data.resolution_width,
        resolution_height=camera_data.resolution_height,
        fps=camera_data.fps,
        latitude=camera_data.latitude,
        longitude=camera_data.longitude,
        location_name=camera_data.location_name,
        retention_days=camera_data.retention_days,
        status=CameraStatus.CONNECTING.value,
    )

    db.add(camera)
    await db.commit()
    await db.refresh(camera)

    logger.info(f"Camera criada: {camera.name} ({camera.ip_address})")

    return CameraResponse.model_validate(camera)


@router.put(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Atualizar camera",
    description="Atualiza os dados de uma camera.",
)
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> CameraResponse:
    """
    Atualiza uma camera.

    Args:
        camera_id: ID da camera.
        camera_data: Dados a atualizar.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        CameraResponse: Camera atualizada.
    """
    # Verifica permissao
    if not current_user.can_manage_cameras:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissao para atualizar cameras",
        )

    # Busca camera
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera nao encontrada",
        )

    # Atualiza campos fornecidos
    update_data = camera_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(camera, field):
            setattr(camera, field, value)

    await db.commit()
    await db.refresh(camera)

    logger.info(f"Camera atualizada: {camera.name}")

    return CameraResponse.model_validate(camera)


@router.delete(
    "/{camera_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir camera",
    description="Remove uma camera do sistema.",
)
async def delete_camera(
    camera_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
) -> None:
    """
    Exclui uma camera.

    Args:
        camera_id: ID da camera.
        db: Sessao do banco de dados.
        current_user: Usuario administrador.
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera nao encontrada",
        )

    await db.delete(camera)
    await db.commit()

    logger.info(f"Camera excluida: {camera.name}")


@router.patch(
    "/{camera_id}/status",
    response_model=CameraResponse,
    summary="Atualizar status",
    description="Atualiza o status de uma camera.",
)
async def update_camera_status(
    camera_id: int,
    status_data: CameraStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> CameraResponse:
    """
    Atualiza status de uma camera.

    Args:
        camera_id: ID da camera.
        status_data: Novo status.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        CameraResponse: Camera atualizada.
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera nao encontrada",
        )

    camera.status = status_data.status

    if status_data.is_recording is not None:
        camera.is_recording = status_data.is_recording

    await db.commit()
    await db.refresh(camera)

    return CameraResponse.model_validate(camera)


@router.post(
    "/discover",
    response_model=list[CameraDiscovery],
    summary="Descobrir cameras",
    description="Busca cameras ONVIF e SSDP na rede local.",
)
async def discover_cameras(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[CameraDiscovery]:
    """
    Descobre cameras na rede via ONVIF e SSDP.

    Executa ambas descobertas em paralelo e combina os resultados.

    Args:
        current_user: Usuario autenticado.

    Returns:
        list[CameraDiscovery]: Cameras descobertas.
    """
    import asyncio

    # Verifica permissao
    if not current_user.can_manage_cameras:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissao para descobrir cameras",
        )

    # Executa descobertas em paralelo
    onvif_task = onvif_discovery_service.discover()
    ssdp_task = ssdp_discovery_service.discover(cameras_only=True)

    onvif_cameras, ssdp_devices = await asyncio.gather(
        onvif_task, ssdp_task, return_exceptions=True
    )

    # Trata excecoes
    if isinstance(onvif_cameras, Exception):
        logger.error(f"Erro na descoberta ONVIF: {onvif_cameras}")
        onvif_cameras = []

    if isinstance(ssdp_devices, Exception):
        logger.error(f"Erro na descoberta SSDP: {ssdp_devices}")
        ssdp_devices = []

    # Combina resultados (ONVIF tem prioridade)
    discovered: dict[str, CameraDiscovery] = {}

    # Adiciona cameras ONVIF
    for c in onvif_cameras:
        discovered[c.ip_address] = CameraDiscovery(
            ip_address=c.ip_address,
            port=c.port,
            protocol="onvif",
            manufacturer=c.manufacturer,
            model=c.model,
            name=c.name,
            onvif_url=c.onvif_url,
            requires_auth=True,
        )

    # Adiciona dispositivos SSDP que nao estao no ONVIF
    for d in ssdp_devices:
        if d.ip_address not in discovered:
            discovered[d.ip_address] = CameraDiscovery(
                ip_address=d.ip_address,
                port=d.port,
                protocol="ssdp",
                manufacturer=d.manufacturer,
                model=d.model,
                name=d.friendly_name or f"Camera {d.ip_address}",
                onvif_url=None,
                requires_auth=True,
            )

    logger.info(f"Total de cameras descobertas: {len(discovered)} (ONVIF: {len(onvif_cameras)}, SSDP: {len(ssdp_devices)})")

    return list(discovered.values())


@router.post(
    "/test",
    response_model=CameraTestResult,
    summary="Testar conexao",
    description="Testa conexao com uma camera.",
)
async def test_camera_connection(
    test_data: CameraTestConnection,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> CameraTestResult:
    """
    Testa conexao com uma camera.

    Args:
        test_data: Dados de conexao.
        current_user: Usuario autenticado.

    Returns:
        CameraTestResult: Resultado do teste.
    """
    # Monta URL RTSP
    if test_data.rtsp_url:
        rtsp_url = test_data.rtsp_url
    else:
        auth = ""
        if test_data.username and test_data.password:
            auth = f"{test_data.username}:{test_data.password}@"
        rtsp_url = f"rtsp://{auth}{test_data.ip_address}:{test_data.port}/stream1"

    # Testa conexao
    result = await stream_service.test_rtsp_connection(rtsp_url)

    return CameraTestResult(
        success=result["success"],
        message=result["message"],
        resolution=result.get("resolution"),
        fps=result.get("fps"),
        snapshot=result.get("snapshot"),
    )


@router.get(
    "/{camera_id}/snapshot",
    summary="Capturar snapshot",
    description="Captura uma imagem da camera.",
)
async def get_camera_snapshot(
    camera_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Captura snapshot de uma camera.

    Args:
        camera_id: ID da camera.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        Response: Imagem JPEG.
    """
    from fastapi.responses import Response

    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera nao encontrada",
        )

    # Tenta obter frame do stream ativo
    frame = await stream_service.get_frame(camera_id)

    if frame is None:
        # Inicia stream temporario para captura
        from app.services.recording_service import recording_service
        frame = await recording_service.capture_snapshot(camera.rtsp_full_url)

    if frame is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel capturar snapshot",
        )

    return Response(
        content=frame,
        media_type="image/jpeg",
    )
