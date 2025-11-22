"""
Rotas de Eventos do SkyCamOS.

Endpoints para listar, visualizar e gerenciar eventos do sistema.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_active_user
from app.core.database import get_db
from app.models.event import Event, EventType, EventSeverity
from app.models.camera import Camera
from app.models.user import User
from app.schemas.event import (
    EventCreate,
    EventListResponse,
    EventResponse,
    EventUpdate,
    EventAcknowledge,
    EventStats,
    EventBulkAction,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=EventListResponse,
    summary="Listar eventos",
    description="Retorna lista paginada de eventos do sistema.",
)
async def list_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1, description="Numero da pagina"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por pagina"),
    camera_id: Optional[int] = Query(None, description="Filtrar por camera"),
    event_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    severity: Optional[str] = Query(None, description="Filtrar por severidade"),
    start_date: Optional[datetime] = Query(None, description="Data inicial"),
    end_date: Optional[datetime] = Query(None, description="Data final"),
    is_read: Optional[bool] = Query(None, description="Filtrar por lido"),
    is_acknowledged: Optional[bool] = Query(None, description="Filtrar por reconhecido"),
    is_starred: Optional[bool] = Query(None, description="Apenas favoritos"),
) -> EventListResponse:
    """
    Lista eventos com paginacao e filtros.

    Args:
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.
        page: Numero da pagina.
        page_size: Itens por pagina.
        camera_id: Filtro por camera.
        event_type: Filtro por tipo.
        severity: Filtro por severidade.
        start_date: Data inicial.
        end_date: Data final.
        is_read: Filtro por lido.
        is_acknowledged: Filtro por reconhecido.
        is_starred: Filtro por favoritos.

    Returns:
        EventListResponse: Lista paginada de eventos.
    """
    # Query base
    query = select(Event)

    # Filtros
    if camera_id:
        query = query.where(Event.camera_id == camera_id)

    if event_type:
        query = query.where(Event.event_type == event_type)

    if severity:
        query = query.where(Event.severity == severity)

    if start_date:
        query = query.where(Event.timestamp >= start_date)

    if end_date:
        query = query.where(Event.timestamp <= end_date)

    if is_read is not None:
        query = query.where(Event.is_read == is_read)

    if is_acknowledged is not None:
        query = query.where(Event.is_acknowledged == is_acknowledged)

    if is_starred is not None:
        query = query.where(Event.is_starred == is_starred)

    # Conta total
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Conta nao lidos e nao reconhecidos
    unread_query = select(func.count()).where(Event.is_read == False)
    result = await db.execute(unread_query)
    unread_count = result.scalar()

    unack_query = select(func.count()).where(Event.is_acknowledged == False)
    result = await db.execute(unack_query)
    unack_count = result.scalar()

    # Paginacao
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Event.timestamp.desc())

    # Executa query
    result = await db.execute(query)
    events = result.scalars().all()

    # Calcula total de paginas
    pages = (total + page_size - 1) // page_size

    # Adiciona nome da camera a cada evento
    event_responses = []
    for event in events:
        event_dict = EventResponse.model_validate(event).model_dump()
        if event.camera_id:
            camera_result = await db.execute(
                select(Camera.name).where(Camera.id == event.camera_id)
            )
            camera_name = camera_result.scalar_one_or_none()
            event_dict["camera_name"] = camera_name
        event_responses.append(EventResponse(**event_dict))

    return EventListResponse(
        items=event_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        unread_count=unread_count,
        unacknowledged_count=unack_count,
    )


@router.get(
    "/stats",
    response_model=EventStats,
    summary="Estatisticas de eventos",
    description="Retorna estatisticas dos eventos.",
)
async def get_event_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> EventStats:
    """
    Retorna estatisticas de eventos.

    Args:
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        EventStats: Estatisticas de eventos.
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # Total
    result = await db.execute(select(func.count(Event.id)))
    total = result.scalar()

    # Hoje
    result = await db.execute(
        select(func.count(Event.id)).where(Event.timestamp >= today_start)
    )
    today = result.scalar()

    # Esta semana
    result = await db.execute(
        select(func.count(Event.id)).where(Event.timestamp >= week_start)
    )
    this_week = result.scalar()

    # Este mes
    result = await db.execute(
        select(func.count(Event.id)).where(Event.timestamp >= month_start)
    )
    this_month = result.scalar()

    # Nao lidos
    result = await db.execute(
        select(func.count(Event.id)).where(Event.is_read == False)
    )
    unread = result.scalar()

    # Nao reconhecidos
    result = await db.execute(
        select(func.count(Event.id)).where(Event.is_acknowledged == False)
    )
    unack = result.scalar()

    # Criticos
    result = await db.execute(
        select(func.count(Event.id)).where(
            Event.severity.in_(["high", "critical"])
        )
    )
    critical = result.scalar()

    # Por tipo
    result = await db.execute(
        select(Event.event_type, func.count(Event.id)).group_by(Event.event_type)
    )
    by_type = {row[0]: row[1] for row in result.all()}

    # Por severidade
    result = await db.execute(
        select(Event.severity, func.count(Event.id)).group_by(Event.severity)
    )
    by_severity = {row[0]: row[1] for row in result.all()}

    # Por camera
    result = await db.execute(
        select(Event.camera_id, func.count(Event.id))
        .where(Event.camera_id.isnot(None))
        .group_by(Event.camera_id)
    )
    by_camera = {str(row[0]): row[1] for row in result.all()}

    # Por hora do dia (ultimas 24h)
    yesterday = now - timedelta(days=1)
    result = await db.execute(
        select(
            func.strftime("%H", Event.timestamp),
            func.count(Event.id)
        )
        .where(Event.timestamp >= yesterday)
        .group_by(func.strftime("%H", Event.timestamp))
    )
    by_hour = {row[0]: row[1] for row in result.all()}

    return EventStats(
        total_events=total,
        events_today=today,
        events_this_week=this_week,
        events_this_month=this_month,
        unread_count=unread,
        unacknowledged_count=unack,
        critical_count=critical,
        events_by_type=by_type,
        events_by_severity=by_severity,
        events_by_camera=by_camera,
        events_by_hour=by_hour,
    )


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Obter evento",
    description="Retorna detalhes de um evento especifico.",
)
async def get_event(
    event_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> EventResponse:
    """
    Obtem um evento pelo ID.

    Args:
        event_id: ID do evento.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        EventResponse: Dados do evento.
    """
    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento nao encontrado",
        )

    # Marca como lido automaticamente
    if not event.is_read:
        event.is_read = True
        await db.commit()
        await db.refresh(event)

    return EventResponse.model_validate(event)


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar evento",
    description="Cria um novo evento no sistema.",
)
async def create_event(
    event_data: EventCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> EventResponse:
    """
    Cria um novo evento.

    Args:
        event_data: Dados do evento.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        EventResponse: Evento criado.
    """
    event = Event(
        camera_id=event_data.camera_id,
        recording_id=event_data.recording_id,
        user_id=event_data.user_id or current_user.id,
        event_type=event_data.event_type,
        severity=event_data.severity,
        title=event_data.title,
        description=event_data.description,
        timestamp=event_data.timestamp or datetime.utcnow(),
        duration_seconds=event_data.duration_seconds,
        snapshot_path=event_data.snapshot_path,
        video_clip_path=event_data.video_clip_path,
        confidence=event_data.confidence,
        bounding_box=event_data.bounding_box,
        detection_zone=event_data.detection_zone,
        metadata=event_data.metadata,
        source=event_data.source or "user",
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    logger.info(f"Evento criado: {event.title}")

    return EventResponse.model_validate(event)


@router.put(
    "/{event_id}",
    response_model=EventResponse,
    summary="Atualizar evento",
    description="Atualiza os dados de um evento.",
)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> EventResponse:
    """
    Atualiza um evento.

    Args:
        event_id: ID do evento.
        event_data: Dados a atualizar.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        EventResponse: Evento atualizado.
    """
    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento nao encontrado",
        )

    # Atualiza campos
    update_data = event_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(event, field):
            setattr(event, field, value)

    await db.commit()
    await db.refresh(event)

    return EventResponse.model_validate(event)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir evento",
    description="Remove um evento do sistema.",
)
async def delete_event(
    event_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """
    Exclui um evento.

    Args:
        event_id: ID do evento.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.
    """
    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento nao encontrado",
        )

    await db.delete(event)
    await db.commit()


@router.post(
    "/{event_id}/acknowledge",
    response_model=EventResponse,
    summary="Reconhecer evento",
    description="Marca um evento como reconhecido/tratado.",
)
async def acknowledge_event(
    event_id: int,
    ack_data: EventAcknowledge,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> EventResponse:
    """
    Reconhece um evento.

    Args:
        event_id: ID do evento.
        ack_data: Dados do reconhecimento.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        EventResponse: Evento atualizado.
    """
    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento nao encontrado",
        )

    event.acknowledge(current_user.username, ack_data.notes)
    await db.commit()
    await db.refresh(event)

    logger.info(f"Evento {event_id} reconhecido por {current_user.username}")

    return EventResponse.model_validate(event)


@router.post(
    "/{event_id}/read",
    response_model=EventResponse,
    summary="Marcar como lido",
    description="Marca um evento como lido.",
)
async def mark_event_read(
    event_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> EventResponse:
    """
    Marca evento como lido.

    Args:
        event_id: ID do evento.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        EventResponse: Evento atualizado.
    """
    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento nao encontrado",
        )

    event.is_read = True
    await db.commit()
    await db.refresh(event)

    return EventResponse.model_validate(event)


@router.post(
    "/bulk",
    summary="Acao em lote",
    description="Executa uma acao em multiplos eventos.",
)
async def bulk_action(
    action_data: EventBulkAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Executa acao em lote em eventos.

    Args:
        action_data: Dados da acao.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        dict: Resultado da acao.
    """
    result = await db.execute(
        select(Event).where(Event.id.in_(action_data.event_ids))
    )
    events = result.scalars().all()

    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum evento encontrado",
        )

    processed = 0
    action = action_data.action

    for event in events:
        if action == "mark_read":
            event.is_read = True
        elif action == "mark_unread":
            event.is_read = False
        elif action == "acknowledge":
            event.acknowledge(current_user.username, action_data.notes)
        elif action == "delete":
            await db.delete(event)
        elif action == "star":
            event.is_starred = True
        elif action == "unstar":
            event.is_starred = False

        processed += 1

    await db.commit()

    logger.info(f"Acao em lote '{action}' executada em {processed} eventos")

    return {
        "action": action,
        "processed": processed,
        "total_requested": len(action_data.event_ids),
    }


@router.post(
    "/mark-all-read",
    summary="Marcar todos como lidos",
    description="Marca todos os eventos como lidos.",
)
async def mark_all_read(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    camera_id: Optional[int] = Query(None, description="Apenas de uma camera"),
) -> dict:
    """
    Marca todos os eventos como lidos.

    Args:
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.
        camera_id: Filtrar por camera.

    Returns:
        dict: Resultado da acao.
    """
    query = select(Event).where(Event.is_read == False)

    if camera_id:
        query = query.where(Event.camera_id == camera_id)

    result = await db.execute(query)
    events = result.scalars().all()

    for event in events:
        event.is_read = True

    await db.commit()

    return {
        "marked_read": len(events),
    }
