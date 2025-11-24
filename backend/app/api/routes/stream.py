"""
Rotas de Streaming do SkyCamOS.

Endpoints para streaming de video via WebSocket, MJPEG e HLS.
"""

import asyncio
import json
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_active_user
from app.core.database import get_db
from app.core.security import verify_token
from app.models.camera import Camera
from app.models.user import User
from app.services.stream_service import stream_service
from app.services.recording_service import recording_service
from app.services.notification_service import notification_service
from app.services.auto_recording_manager import auto_recording_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{camera_id}/mjpeg",
    summary="Stream MJPEG",
    description="Transmite video em formato MJPEG.",
)
async def mjpeg_stream(
    camera_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    token: str = Query(..., description="Token de autenticacao"),
    fps: int = Query(15, ge=1, le=30, description="Frames por segundo"),
):
    """
    Stream MJPEG de uma camera.

    Args:
        camera_id: ID da camera.
        db: Sessao do banco de dados.
        token: Token de autenticacao.
        fps: FPS do stream.

    Returns:
        StreamingResponse: Stream MJPEG.
    """
    # Valida token
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
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

    # Inicia stream se nao estiver ativo
    stream_info = stream_service.get_stream_info(camera_id)

    if stream_info is None:
        stream_info = await stream_service.start_stream(camera_id, camera.rtsp_full_url)

        if stream_info is None:
            # Atualiza status para erro
            if camera.status != "error":
                camera.status = "error"
                camera.is_recording = False
                await db.commit()

                # Para gravacao automatica se estava gravando
                if camera.id in auto_recording_manager.cameras_recording:
                    asyncio.create_task(auto_recording_manager.stop_camera_recording(camera.id))

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Nao foi possivel iniciar stream",
            )

        # Stream iniciado com sucesso - atualiza status para online
        if camera.status != "online" and camera.status != "recording":
            camera.status = "online"
            from datetime import datetime
            camera.last_seen = datetime.utcnow()
            await db.commit()
            logger.info(f"Camera {camera_id} status atualizado para online")

            # Inicia gravacao automatica
            if auto_recording_manager.is_running and camera.is_enabled:
                asyncio.create_task(auto_recording_manager.start_camera_recording(camera_id))

    # Obtem streamer MJPEG
    streamer = stream_service.get_mjpeg_streamer(camera_id)

    if streamer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Streamer nao disponivel",
        )

    return StreamingResponse(
        streamer.stream_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get(
    "/{camera_id}/snapshot",
    summary="Snapshot",
    description="Captura uma imagem da camera.",
)
async def get_snapshot(
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

    # Tenta obter frame do stream ativo
    frame = await stream_service.get_frame(camera_id)

    if frame is None:
        # Captura snapshot diretamente
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


@router.get(
    "/{camera_id}/info",
    summary="Informacoes do stream",
    description="Retorna informacoes do stream ativo.",
)
async def get_stream_info(
    camera_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Retorna informacoes de um stream.

    Args:
        camera_id: ID da camera.
        current_user: Usuario autenticado.

    Returns:
        dict: Informacoes do stream.
    """
    stream_info = stream_service.get_stream_info(camera_id)

    if stream_info is None:
        return {
            "camera_id": camera_id,
            "is_streaming": False,
        }

    return {
        "camera_id": camera_id,
        "is_streaming": True,
        **stream_info.to_dict(),
    }


@router.post(
    "/{camera_id}/start",
    summary="Iniciar stream",
    description="Inicia o stream de uma camera.",
)
async def start_stream(
    camera_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Inicia stream de uma camera.

    Args:
        camera_id: ID da camera.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        dict: Informacoes do stream.
    """
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

    stream_info = await stream_service.start_stream(camera_id, camera.rtsp_full_url)

    if stream_info is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel iniciar stream",
        )

    return {
        "message": "Stream iniciado",
        **stream_info.to_dict(),
    }


@router.post(
    "/{camera_id}/stop",
    summary="Parar stream",
    description="Para o stream de uma camera.",
)
async def stop_stream(
    camera_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Para stream de uma camera.

    Args:
        camera_id: ID da camera.
        current_user: Usuario autenticado.

    Returns:
        dict: Confirmacao.
    """
    await stream_service.stop_stream(camera_id)

    return {
        "message": "Stream parado",
        "camera_id": camera_id,
    }


@router.get(
    "/active",
    summary="Streams ativos",
    description="Lista todos os streams ativos.",
)
async def list_active_streams(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Lista streams ativos.

    Args:
        current_user: Usuario autenticado.

    Returns:
        dict: Lista de streams.
    """
    streams = stream_service.get_all_streams()

    return {
        "count": len(streams),
        "streams": [s.to_dict() for s in streams],
    }


@router.post(
    "/{camera_id}/recording/start",
    summary="Iniciar gravacao",
    description="Inicia gravacao de uma camera.",
)
async def start_recording(
    camera_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Inicia gravacao de uma camera.

    Args:
        camera_id: ID da camera.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        dict: Informacoes da gravacao.
    """
    # Verifica permissao
    if not current_user.can_manage_cameras:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissao para iniciar gravacao",
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

    recording_info = await recording_service.start_recording(camera)

    if recording_info is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nao foi possivel iniciar gravacao",
        )

    # Atualiza status da camera
    camera.is_recording = True
    camera.status = "recording"
    await db.commit()

    return {
        "message": "Gravacao iniciada",
        **recording_info,
    }


@router.post(
    "/{camera_id}/recording/stop",
    summary="Parar gravacao",
    description="Para gravacao de uma camera.",
)
async def stop_recording(
    camera_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Para gravacao de uma camera.

    Args:
        camera_id: ID da camera.
        db: Sessao do banco de dados.
        current_user: Usuario autenticado.

    Returns:
        dict: Informacoes da gravacao.
    """
    recording_info = await recording_service.stop_recording(camera_id)

    # Atualiza status da camera
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if camera:
        camera.is_recording = False
        camera.status = "online"
        await db.commit()

    return {
        "message": "Gravacao parada",
        "recording": recording_info,
    }


@router.websocket("/ws")
async def websocket_notifications(websocket: WebSocket):
    """
    WebSocket para notificacoes em tempo real.

    Recebe eventos de movimento, alertas e atualizacoes de status.
    """
    await websocket.accept()

    # Obtem token do query param ou header
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=4001, reason="Token nao fornecido")
        return

    # Valida token
    payload = verify_token(token)

    if payload is None:
        await websocket.close(code=4002, reason="Token invalido")
        return

    user_id = str(payload.get("user_id"))
    ws_manager = notification_service.websocket_manager

    # Registra conexao
    await ws_manager.connect(websocket, user_id)

    try:
        # Envia mensagem de boas-vindas
        await websocket.send_json({
            "type": "connected",
            "message": "Conectado ao servidor de notificacoes",
            "user_id": user_id,
        })

        # Loop para manter conexao e processar mensagens
        while True:
            try:
                # Aguarda mensagens do cliente
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,
                )

                # Processa mensagem recebida
                try:
                    message = json.loads(data)
                    msg_type = message.get("type")

                    if msg_type == "ping":
                        await websocket.send_json({"type": "pong"})

                    elif msg_type == "subscribe":
                        # Inscreve para eventos de cameras especificas
                        cameras = message.get("cameras", [])
                        await websocket.send_json({
                            "type": "subscribed",
                            "cameras": cameras,
                        })

                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Envia ping para manter conexao
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado: user {user_id}")
    except Exception as e:
        logger.error(f"Erro no WebSocket: {e}")
    finally:
        await ws_manager.disconnect(websocket, user_id)


@router.websocket("/ws/{camera_id}")
async def websocket_camera_stream(
    websocket: WebSocket,
    camera_id: int,
):
    """
    WebSocket para stream de frames de uma camera.

    Envia frames JPEG em tempo real.
    """
    await websocket.accept()

    # Valida token
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=4001, reason="Token nao fornecido")
        return

    payload = verify_token(token)

    if payload is None:
        await websocket.close(code=4002, reason="Token invalido")
        return

    # Busca camera (precisa de sessao separada para WebSocket)
    from app.core.database import async_session_factory

    async with async_session_factory() as db:
        result = await db.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        camera = result.scalar_one_or_none()

        if camera is None:
            await websocket.close(code=4004, reason="Camera nao encontrada")
            return

        rtsp_url = camera.rtsp_full_url

    # Inicia stream
    stream_info = stream_service.get_stream_info(camera_id)

    if stream_info is None:
        stream_info = await stream_service.start_stream(camera_id, rtsp_url)

        if stream_info is None:
            await websocket.close(code=5003, reason="Falha ao iniciar stream")
            return

    try:
        # Envia frames em loop
        import base64

        while True:
            frame = await stream_service.get_frame(camera_id)

            if frame:
                # Converte para base64
                frame_b64 = base64.b64encode(frame).decode("utf-8")

                await websocket.send_json({
                    "type": "frame",
                    "camera_id": camera_id,
                    "data": frame_b64,
                })

            await asyncio.sleep(1.0 / 15)  # ~15 fps

    except WebSocketDisconnect:
        logger.info(f"WebSocket stream desconectado: camera {camera_id}")
    except Exception as e:
        logger.error(f"Erro no WebSocket stream: {e}")
