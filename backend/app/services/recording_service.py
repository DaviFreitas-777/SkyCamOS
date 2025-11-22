"""
Servico de Gravacao do SkyCamOS.

Este modulo implementa a gravacao continua e por eventos
de streams de cameras IP.
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from app.config import settings
from app.models.camera import Camera
from app.models.recording import Recording, RecordingStatus, RecordingType

logger = logging.getLogger(__name__)


class CameraRecorder:
    """
    Gravador para uma camera individual.

    Gerencia a captura e gravacao do stream de uma camera.
    """

    def __init__(
        self,
        camera_id: int,
        rtsp_url: str,
        output_dir: Path,
        segment_duration: int = 300,  # 5 minutos por segmento
    ) -> None:
        """
        Inicializa o gravador.

        Args:
            camera_id: ID da camera.
            rtsp_url: URL RTSP do stream.
            output_dir: Diretorio para salvar as gravacoes.
            segment_duration: Duracao de cada segmento em segundos.
        """
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.output_dir = output_dir
        self.segment_duration = segment_duration

        self._is_recording = False
        self._capture: Optional[cv2.VideoCapture] = None
        self._writer: Optional[cv2.VideoWriter] = None
        self._current_recording: Optional[dict] = None
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        # Estatisticas
        self._frames_recorded = 0
        self._bytes_written = 0
        self._start_time: Optional[datetime] = None

    @property
    def is_recording(self) -> bool:
        """Retorna se esta gravando."""
        return self._is_recording

    async def start(self) -> bool:
        """
        Inicia a gravacao.

        Returns:
            bool: True se iniciou com sucesso.
        """
        if self._is_recording:
            logger.warning(f"Camera {self.camera_id} ja esta gravando")
            return False

        logger.info(f"Iniciando gravacao da camera {self.camera_id}")

        try:
            # Abre captura RTSP
            self._capture = cv2.VideoCapture(self.rtsp_url)

            if not self._capture.isOpened():
                logger.error(f"Falha ao abrir stream: {self.rtsp_url}")
                return False

            # Configura parametros de captura
            self._capture.set(cv2.CAP_PROP_BUFFERSIZE, settings.rtsp_buffer_size)

            self._is_recording = True
            self._stop_event.clear()
            self._start_time = datetime.utcnow()

            # Inicia task de gravacao
            self._task = asyncio.create_task(self._recording_loop())

            logger.info(f"Gravacao iniciada para camera {self.camera_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar gravacao: {e}")
            await self.stop()
            return False

    async def stop(self) -> Optional[dict]:
        """
        Para a gravacao.

        Returns:
            Optional[dict]: Informacoes da gravacao finalizada.
        """
        if not self._is_recording:
            return None

        logger.info(f"Parando gravacao da camera {self.camera_id}")

        self._is_recording = False
        self._stop_event.set()

        # Aguarda task finalizar
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()

        # Libera recursos
        if self._writer:
            self._writer.release()
            self._writer = None

        if self._capture:
            self._capture.release()
            self._capture = None

        # Retorna info da ultima gravacao
        recording_info = self._current_recording
        self._current_recording = None

        return recording_info

    async def _recording_loop(self) -> None:
        """Loop principal de gravacao."""
        segment_start = datetime.utcnow()
        frames_in_segment = 0

        while self._is_recording and not self._stop_event.is_set():
            try:
                # Verifica se precisa criar novo segmento
                elapsed = (datetime.utcnow() - segment_start).total_seconds()
                if elapsed >= self.segment_duration or self._writer is None:
                    await self._start_new_segment()
                    segment_start = datetime.utcnow()
                    frames_in_segment = 0

                # Captura frame
                ret, frame = self._capture.read()

                if not ret:
                    logger.warning(f"Falha ao ler frame da camera {self.camera_id}")
                    await asyncio.sleep(0.1)

                    # Tenta reconectar
                    self._capture.release()
                    self._capture = cv2.VideoCapture(self.rtsp_url)
                    continue

                # Grava frame
                if self._writer:
                    self._writer.write(frame)
                    self._frames_recorded += 1
                    frames_in_segment += 1

                # Pequena pausa para nao sobrecarregar CPU
                await asyncio.sleep(0.001)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de gravacao: {e}")
                await asyncio.sleep(1)

        # Finaliza segmento atual
        await self._finalize_segment()

    async def _start_new_segment(self) -> None:
        """Inicia um novo segmento de gravacao."""
        # Finaliza segmento anterior
        await self._finalize_segment()

        # Gera nome do arquivo
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"camera_{self.camera_id}_{timestamp}.mp4"
        filepath = self.output_dir / filename

        # Garante que o diretorio existe
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Obtem propriedades do video
        fps = self._capture.get(cv2.CAP_PROP_FPS) or 25
        width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Cria writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(
            str(filepath),
            fourcc,
            fps,
            (width, height),
        )

        self._current_recording = {
            "camera_id": self.camera_id,
            "filename": filename,
            "filepath": str(filepath),
            "start_time": datetime.utcnow(),
            "resolution": f"{width}x{height}",
            "fps": int(fps),
            "codec": "mp4v",
        }

        logger.info(f"Novo segmento iniciado: {filename}")

    async def _finalize_segment(self) -> None:
        """Finaliza o segmento atual."""
        if self._writer is None:
            return

        self._writer.release()
        self._writer = None

        if self._current_recording:
            # Atualiza info do segmento
            filepath = Path(self._current_recording["filepath"])
            self._current_recording["end_time"] = datetime.utcnow()
            self._current_recording["duration_seconds"] = (
                self._current_recording["end_time"] -
                self._current_recording["start_time"]
            ).total_seconds()

            if filepath.exists():
                self._current_recording["file_size_bytes"] = filepath.stat().st_size

            logger.info(
                f"Segmento finalizado: {self._current_recording['filename']} "
                f"({self._current_recording['duration_seconds']:.1f}s)"
            )


class RecordingService:
    """
    Servico principal de gravacao.

    Gerencia gravadores para multiplas cameras.
    """

    def __init__(self) -> None:
        """Inicializa o servico de gravacao."""
        self._recorders: dict[int, CameraRecorder] = {}
        self._recordings: list[dict] = []
        self._output_dir = settings.recordings_dir

    @property
    def active_recordings(self) -> int:
        """Retorna numero de gravacoes ativas."""
        return sum(1 for r in self._recorders.values() if r.is_recording)

    async def start_recording(
        self,
        camera: Camera,
        recording_type: str = RecordingType.CONTINUOUS.value,
    ) -> Optional[dict]:
        """
        Inicia gravacao de uma camera.

        Args:
            camera: Objeto Camera.
            recording_type: Tipo de gravacao.

        Returns:
            Optional[dict]: Informacoes da gravacao ou None se falhar.
        """
        if camera.id in self._recorders and self._recorders[camera.id].is_recording:
            logger.warning(f"Camera {camera.id} ja esta em gravacao")
            return None

        # Cria diretorio especifico para a camera
        camera_dir = self._output_dir / f"camera_{camera.id}"
        camera_dir.mkdir(parents=True, exist_ok=True)

        # Cria gravador
        recorder = CameraRecorder(
            camera_id=camera.id,
            rtsp_url=camera.rtsp_full_url,
            output_dir=camera_dir,
        )

        success = await recorder.start()

        if success:
            self._recorders[camera.id] = recorder
            return {
                "camera_id": camera.id,
                "status": "recording",
                "recording_type": recording_type,
                "started_at": datetime.utcnow().isoformat(),
            }

        return None

    async def stop_recording(self, camera_id: int) -> Optional[dict]:
        """
        Para gravacao de uma camera.

        Args:
            camera_id: ID da camera.

        Returns:
            Optional[dict]: Informacoes da gravacao finalizada.
        """
        if camera_id not in self._recorders:
            return None

        recorder = self._recorders[camera_id]
        recording_info = await recorder.stop()

        del self._recorders[camera_id]

        if recording_info:
            self._recordings.append(recording_info)

        return recording_info

    async def stop_all(self) -> list[dict]:
        """
        Para todas as gravacoes.

        Returns:
            list[dict]: Lista de gravacoes finalizadas.
        """
        results = []

        for camera_id in list(self._recorders.keys()):
            info = await self.stop_recording(camera_id)
            if info:
                results.append(info)

        return results

    def get_recording_status(self, camera_id: int) -> Optional[dict]:
        """
        Obtem status de gravacao de uma camera.

        Args:
            camera_id: ID da camera.

        Returns:
            Optional[dict]: Status ou None se nao esta gravando.
        """
        if camera_id not in self._recorders:
            return None

        recorder = self._recorders[camera_id]

        return {
            "camera_id": camera_id,
            "is_recording": recorder.is_recording,
            "frames_recorded": recorder._frames_recorded,
            "started_at": recorder._start_time.isoformat() if recorder._start_time else None,
        }

    async def capture_snapshot(
        self,
        rtsp_url: str,
        output_path: Optional[Path] = None,
    ) -> Optional[bytes]:
        """
        Captura um snapshot de uma camera.

        Args:
            rtsp_url: URL RTSP da camera.
            output_path: Caminho para salvar (opcional).

        Returns:
            Optional[bytes]: Imagem em bytes ou None se falhar.
        """
        try:
            cap = cv2.VideoCapture(rtsp_url)

            if not cap.isOpened():
                return None

            ret, frame = cap.read()
            cap.release()

            if not ret:
                return None

            # Codifica para JPEG
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(buffer.tobytes())

            return buffer.tobytes()

        except Exception as e:
            logger.error(f"Erro ao capturar snapshot: {e}")
            return None


# Instancia global do servico
recording_service = RecordingService()
