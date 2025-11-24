"""
Gerenciador de Gravacao Automatica do SkyCamOS.

Este modulo monitora cameras e inicia/para gravacao automaticamente
baseado no status da camera (online/offline).
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import async_session_factory
from app.models.camera import Camera
from app.services.recording_service import recording_service

logger = logging.getLogger(__name__)


class AutoRecordingManager:
    """
    Gerenciador de gravacao automatica.

    Monitora cameras periodicamente e inicia gravacao quando
    a camera fica online, para quando fica offline.
    """

    def __init__(self, check_interval: int = 30) -> None:
        """
        Inicializa o gerenciador.

        Args:
            check_interval: Intervalo entre verificacoes em segundos.
        """
        self._check_interval = check_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._cameras_recording: set[int] = set()

    @property
    def is_running(self) -> bool:
        """Retorna se o gerenciador esta rodando."""
        return self._running

    @property
    def cameras_recording(self) -> set[int]:
        """Retorna IDs das cameras em gravacao automatica."""
        return self._cameras_recording.copy()

    async def start(self) -> None:
        """Inicia o gerenciador de gravacao automatica."""
        if self._running:
            logger.warning("AutoRecordingManager ja esta rodando")
            return

        logger.info("Iniciando AutoRecordingManager...")
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("AutoRecordingManager iniciado com sucesso")

    async def stop(self) -> None:
        """Para o gerenciador e todas as gravacoes automaticas."""
        if not self._running:
            return

        logger.info("Parando AutoRecordingManager...")
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Para todas as gravacoes automaticas
        await recording_service.stop_all()
        self._cameras_recording.clear()

        logger.info("AutoRecordingManager parado")

    async def _monitoring_loop(self) -> None:
        """Loop principal de monitoramento."""
        # Aguarda um pouco antes de iniciar (para o sistema estabilizar)
        await asyncio.sleep(5)

        while self._running:
            try:
                await self._check_cameras()
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")

            await asyncio.sleep(self._check_interval)

    async def _check_cameras(self) -> None:
        """Verifica todas as cameras e gerencia gravacao."""
        async with async_session_factory() as db:
            # Busca todas as cameras habilitadas
            result = await db.execute(
                select(Camera).where(Camera.is_enabled == True)
            )
            cameras = result.scalars().all()

            for camera in cameras:
                await self._process_camera(camera, db)

    async def _process_camera(self, camera: Camera, db: AsyncSession) -> None:
        """
        Processa uma camera individual.

        Args:
            camera: Objeto Camera.
            db: Sessao do banco de dados.
        """
        camera_id = camera.id
        is_recording = camera_id in self._cameras_recording
        should_record = camera.status in ("online", "recording") and camera.is_enabled

        # Camera deve gravar mas nao esta
        if should_record and not is_recording:
            await self._start_auto_recording(camera, db)

        # Camera esta gravando mas nao deveria
        elif not should_record and is_recording:
            await self._stop_auto_recording(camera, db)

    async def _start_auto_recording(self, camera: Camera, db: AsyncSession) -> None:
        """
        Inicia gravacao automatica de uma camera.

        Args:
            camera: Objeto Camera.
            db: Sessao do banco de dados.
        """
        logger.info(f"Iniciando gravacao automatica da camera {camera.id} ({camera.name})")

        try:
            recording_info = await recording_service.start_recording(camera)

            if recording_info:
                self._cameras_recording.add(camera.id)

                # Atualiza status no banco
                camera.is_recording = True
                camera.status = "recording"
                await db.commit()

                logger.info(f"Gravacao automatica iniciada: camera {camera.id}")
            else:
                logger.warning(f"Falha ao iniciar gravacao automatica: camera {camera.id}")

        except Exception as e:
            logger.error(f"Erro ao iniciar gravacao automatica camera {camera.id}: {e}")

    async def _stop_auto_recording(self, camera: Camera, db: AsyncSession) -> None:
        """
        Para gravacao automatica de uma camera.

        Args:
            camera: Objeto Camera.
            db: Sessao do banco de dados.
        """
        logger.info(f"Parando gravacao automatica da camera {camera.id} ({camera.name})")

        try:
            await recording_service.stop_recording(camera.id)
            self._cameras_recording.discard(camera.id)

            # Atualiza status no banco
            camera.is_recording = False
            if camera.status == "recording":
                camera.status = "online" if camera.is_enabled else "offline"
            await db.commit()

            logger.info(f"Gravacao automatica parada: camera {camera.id}")

        except Exception as e:
            logger.error(f"Erro ao parar gravacao automatica camera {camera.id}: {e}")

    async def start_camera_recording(self, camera_id: int) -> bool:
        """
        Inicia gravacao de uma camera especifica (chamado externamente).

        Args:
            camera_id: ID da camera.

        Returns:
            bool: True se iniciou com sucesso.
        """
        async with async_session_factory() as db:
            result = await db.execute(
                select(Camera).where(Camera.id == camera_id)
            )
            camera = result.scalar_one_or_none()

            if camera is None:
                return False

            await self._start_auto_recording(camera, db)
            return camera_id in self._cameras_recording

    async def stop_camera_recording(self, camera_id: int) -> bool:
        """
        Para gravacao de uma camera especifica (chamado externamente).

        Args:
            camera_id: ID da camera.

        Returns:
            bool: True se parou com sucesso.
        """
        if camera_id not in self._cameras_recording:
            return False

        async with async_session_factory() as db:
            result = await db.execute(
                select(Camera).where(Camera.id == camera_id)
            )
            camera = result.scalar_one_or_none()

            if camera:
                await self._stop_auto_recording(camera, db)

            return camera_id not in self._cameras_recording


# Instancia global do gerenciador
auto_recording_manager = AutoRecordingManager()
