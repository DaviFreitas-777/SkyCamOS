"""
Servico de Streaming do SkyCamOS.

Este modulo implementa a conversao de streams RTSP para
WebRTC e HLS para visualizacao no navegador.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from pathlib import Path

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class StreamInfo:
    """
    Informacoes de um stream ativo.

    Attributes:
        camera_id: ID da camera.
        rtsp_url: URL RTSP original.
        started_at: Momento de inicio.
        viewers: Numero de visualizadores.
        resolution: Resolucao do stream.
        fps: Frames por segundo.
        bitrate: Taxa de bits.
    """

    camera_id: int
    rtsp_url: str
    started_at: datetime
    viewers: int = 0
    resolution: Optional[str] = None
    fps: Optional[int] = None
    bitrate: Optional[int] = None

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            "camera_id": self.camera_id,
            "rtsp_url": self.rtsp_url,
            "started_at": self.started_at.isoformat(),
            "viewers": self.viewers,
            "resolution": self.resolution,
            "fps": self.fps,
            "bitrate": self.bitrate,
        }


class RTSPReader:
    """
    Leitor de stream RTSP.

    Captura frames de um stream RTSP e os disponibiliza
    para transmissao.
    """

    def __init__(self, rtsp_url: str, buffer_size: int = 5) -> None:
        """
        Inicializa o leitor RTSP.

        Args:
            rtsp_url: URL do stream RTSP.
            buffer_size: Tamanho do buffer de frames.
        """
        self.rtsp_url = rtsp_url
        self.buffer_size = buffer_size

        self._capture: Optional[cv2.VideoCapture] = None
        self._is_running = False
        self._current_frame: Optional[np.ndarray] = None
        self._frame_lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        # Propriedades do stream
        self.width: int = 0
        self.height: int = 0
        self.fps: float = 0

    async def start(self) -> bool:
        """
        Inicia a captura do stream.

        Returns:
            bool: True se iniciou com sucesso.
        """
        if self._is_running:
            return True

        try:
            self._capture = cv2.VideoCapture(self.rtsp_url)

            if not self._capture.isOpened():
                logger.error(f"Falha ao abrir stream: {self.rtsp_url}")
                return False

            # Obtem propriedades
            self.width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = self._capture.get(cv2.CAP_PROP_FPS) or 25

            # Configura buffer
            self._capture.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)

            self._is_running = True
            self._stop_event.clear()

            # Inicia task de leitura
            self._task = asyncio.create_task(self._read_loop())

            logger.info(
                f"Stream RTSP iniciado: {self.width}x{self.height} @ {self.fps}fps"
            )
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar stream RTSP: {e}")
            return False

    async def stop(self) -> None:
        """Para a captura do stream."""
        self._is_running = False
        self._stop_event.set()

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=3.0)
            except asyncio.TimeoutError:
                self._task.cancel()

        if self._capture:
            self._capture.release()
            self._capture = None

    async def _read_loop(self) -> None:
        """Loop de leitura de frames."""
        while self._is_running and not self._stop_event.is_set():
            try:
                ret, frame = self._capture.read()

                if ret:
                    async with self._frame_lock:
                        self._current_frame = frame
                else:
                    # Tenta reconectar
                    await asyncio.sleep(0.5)
                    self._capture.release()
                    self._capture = cv2.VideoCapture(self.rtsp_url)

                # Controle de taxa de frames
                await asyncio.sleep(1.0 / max(self.fps, 1))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro na leitura de frame: {e}")
                await asyncio.sleep(0.1)

    async def get_frame(self) -> Optional[np.ndarray]:
        """
        Obtem o frame atual.

        Returns:
            Optional[np.ndarray]: Frame atual ou None.
        """
        async with self._frame_lock:
            if self._current_frame is not None:
                return self._current_frame.copy()
        return None

    async def get_jpeg_frame(self, quality: int = 80) -> Optional[bytes]:
        """
        Obtem o frame atual como JPEG.

        Args:
            quality: Qualidade do JPEG (0-100).

        Returns:
            Optional[bytes]: Frame em JPEG ou None.
        """
        frame = await self.get_frame()

        if frame is None:
            return None

        _, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, quality],
        )

        return buffer.tobytes()


class MJPEGStreamer:
    """
    Streamer MJPEG para transmissao via HTTP.

    Converte frames para MJPEG e os transmite
    via boundary multipart.
    """

    def __init__(self, reader: RTSPReader, fps: int = 15) -> None:
        """
        Inicializa o streamer MJPEG.

        Args:
            reader: Leitor RTSP.
            fps: FPS de saida.
        """
        self.reader = reader
        self.fps = fps
        self._clients: set = set()

    async def stream_generator(self):
        """
        Gerador de frames MJPEG.

        Yields:
            bytes: Frames MJPEG formatados como multipart.
        """
        boundary = b"--frame\r\n"
        content_type = b"Content-Type: image/jpeg\r\n\r\n"

        while True:
            frame_data = await self.reader.get_jpeg_frame()

            if frame_data:
                yield boundary + content_type + frame_data + b"\r\n"

            await asyncio.sleep(1.0 / self.fps)

    @property
    def client_count(self) -> int:
        """Retorna numero de clientes conectados."""
        return len(self._clients)


class StreamService:
    """
    Servico principal de streaming.

    Gerencia streams para multiplas cameras.
    """

    def __init__(self) -> None:
        """Inicializa o servico de streaming."""
        self._readers: dict[int, RTSPReader] = {}
        self._streamers: dict[int, MJPEGStreamer] = {}
        self._stream_info: dict[int, StreamInfo] = {}

    async def start_stream(
        self,
        camera_id: int,
        rtsp_url: str,
    ) -> Optional[StreamInfo]:
        """
        Inicia um stream para uma camera.

        Args:
            camera_id: ID da camera.
            rtsp_url: URL RTSP.

        Returns:
            Optional[StreamInfo]: Info do stream ou None se falhar.
        """
        if camera_id in self._readers:
            # Stream ja existe, retorna info
            return self._stream_info.get(camera_id)

        reader = RTSPReader(rtsp_url)
        success = await reader.start()

        if not success:
            return None

        streamer = MJPEGStreamer(reader)

        self._readers[camera_id] = reader
        self._streamers[camera_id] = streamer

        info = StreamInfo(
            camera_id=camera_id,
            rtsp_url=rtsp_url,
            started_at=datetime.utcnow(),
            resolution=f"{reader.width}x{reader.height}",
            fps=int(reader.fps),
        )

        self._stream_info[camera_id] = info

        logger.info(f"Stream iniciado para camera {camera_id}")

        return info

    async def stop_stream(self, camera_id: int) -> None:
        """
        Para o stream de uma camera.

        Args:
            camera_id: ID da camera.
        """
        if camera_id in self._readers:
            await self._readers[camera_id].stop()
            del self._readers[camera_id]
            del self._streamers[camera_id]
            del self._stream_info[camera_id]

            logger.info(f"Stream parado para camera {camera_id}")

    async def stop_all(self) -> None:
        """Para todos os streams."""
        for camera_id in list(self._readers.keys()):
            await self.stop_stream(camera_id)

    async def get_frame(self, camera_id: int) -> Optional[bytes]:
        """
        Obtem um frame JPEG de uma camera.

        Args:
            camera_id: ID da camera.

        Returns:
            Optional[bytes]: Frame JPEG ou None.
        """
        if camera_id not in self._readers:
            return None

        return await self._readers[camera_id].get_jpeg_frame()

    def get_mjpeg_streamer(self, camera_id: int) -> Optional[MJPEGStreamer]:
        """
        Obtem o streamer MJPEG de uma camera.

        Args:
            camera_id: ID da camera.

        Returns:
            Optional[MJPEGStreamer]: Streamer ou None.
        """
        return self._streamers.get(camera_id)

    def get_stream_info(self, camera_id: int) -> Optional[StreamInfo]:
        """
        Obtem informacoes de um stream.

        Args:
            camera_id: ID da camera.

        Returns:
            Optional[StreamInfo]: Info do stream ou None.
        """
        return self._stream_info.get(camera_id)

    def get_all_streams(self) -> list[StreamInfo]:
        """
        Lista todos os streams ativos.

        Returns:
            list[StreamInfo]: Lista de streams.
        """
        return list(self._stream_info.values())

    async def test_rtsp_connection(
        self,
        rtsp_url: str,
        timeout: int = 10,
    ) -> dict:
        """
        Testa conexao com um stream RTSP.

        Args:
            rtsp_url: URL RTSP a testar.
            timeout: Timeout em segundos.

        Returns:
            dict: Resultado do teste.
        """
        try:
            cap = cv2.VideoCapture(rtsp_url)

            if not cap.isOpened():
                return {
                    "success": False,
                    "message": "Falha ao abrir stream RTSP",
                }

            # Tenta ler um frame
            ret, frame = cap.read()

            if not ret:
                cap.release()
                return {
                    "success": False,
                    "message": "Falha ao ler frame do stream",
                }

            # Obtem propriedades
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            cap.release()

            # Gera snapshot base64
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            import base64
            snapshot_b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

            return {
                "success": True,
                "message": "Conexao bem sucedida",
                "resolution": f"{width}x{height}",
                "fps": int(fps) if fps > 0 else None,
                "snapshot": f"data:image/jpeg;base64,{snapshot_b64}",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Erro: {str(e)}",
            }


# Instancia global do servico
stream_service = StreamService()
