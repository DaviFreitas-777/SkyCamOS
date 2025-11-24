"""
Servico de Gravacao do SkyCamOS.

Este modulo implementa a gravacao continua e por eventos
de streams de cameras IP usando FFmpeg com copy codec
para evitar re-encoding e economizar espaco/CPU.
"""

import asyncio
import logging
import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2

from app.config import settings
from app.models.camera import Camera
from app.models.recording import Recording, RecordingStatus, RecordingType

logger = logging.getLogger(__name__)


class FFmpegRecorder:
    """
    Gravador usando FFmpeg com copy codec.

    Salva o stream H.264 bruto sem re-encoding para:
    - Arquivos menores
    - Menor uso de CPU
    - Sem perda de qualidade
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
        self._process: Optional[subprocess.Popen] = None
        self._current_recording: Optional[dict] = None
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._start_time: Optional[datetime] = None

    @property
    def is_recording(self) -> bool:
        """Retorna se esta gravando."""
        return self._is_recording

    def _get_ffmpeg_path(self) -> str:
        """Retorna o caminho do FFmpeg."""
        # Tenta encontrar FFmpeg no PATH
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            return ffmpeg
        # Windows: tenta locais comuns incluindo winget
        import glob
        common_paths = [
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
            "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
        ]
        # Adiciona path do winget (instalacao via winget install Gyan.FFmpeg)
        winget_pattern = os.path.expanduser(
            "~\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg*\\ffmpeg-*\\bin\\ffmpeg.exe"
        )
        winget_paths = glob.glob(winget_pattern)
        if winget_paths:
            common_paths.extend(winget_paths)
        for path in common_paths:
            if os.path.exists(path):
                return path
        return "ffmpeg"  # Tenta usar do PATH

    async def start(self) -> bool:
        """
        Inicia a gravacao usando FFmpeg.

        Returns:
            bool: True se iniciou com sucesso.
        """
        if self._is_recording:
            logger.warning(f"Camera {self.camera_id} ja esta gravando")
            return False

        logger.info(f"Iniciando gravacao FFmpeg da camera {self.camera_id}")

        try:
            # Garante que o diretorio existe
            self.output_dir.mkdir(parents=True, exist_ok=True)

            self._is_recording = True
            self._stop_event.clear()
            self._start_time = datetime.utcnow()

            # Inicia task de gravacao em segmentos
            self._task = asyncio.create_task(self._recording_loop())

            logger.info(f"Gravacao FFmpeg iniciada para camera {self.camera_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar gravacao FFmpeg: {e}")
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

        logger.info(f"Parando gravacao FFmpeg da camera {self.camera_id}")

        self._is_recording = False
        self._stop_event.set()

        # Para processo FFmpeg
        if self._process and self._process.poll() is None:
            try:
                # Envia 'q' para FFmpeg parar graciosamente
                self._process.stdin.write(b'q')
                self._process.stdin.flush()
                await asyncio.sleep(1)
            except Exception:
                pass

            if self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()

        # Aguarda task finalizar
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()

        # Retorna info da ultima gravacao
        recording_info = self._current_recording
        self._current_recording = None

        return recording_info

    async def _recording_loop(self) -> None:
        """Loop principal de gravacao em segmentos."""
        while self._is_recording and not self._stop_event.is_set():
            try:
                await self._start_new_segment()

                # Aguarda segmento terminar ou stop event
                segment_task = asyncio.create_task(self._wait_for_segment())
                stop_task = asyncio.create_task(self._stop_event.wait())

                done, pending = await asyncio.wait(
                    [segment_task, stop_task],
                    return_when=asyncio.FIRST_COMPLETED
                )

                for task in pending:
                    task.cancel()

                # Se parou, finaliza segmento
                if self._stop_event.is_set():
                    await self._finalize_segment()
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de gravacao FFmpeg: {e}")
                await asyncio.sleep(5)

    async def _wait_for_segment(self) -> None:
        """Aguarda o segmento atual terminar."""
        if self._process:
            while self._process.poll() is None:
                await asyncio.sleep(1)

    async def _start_new_segment(self) -> None:
        """Inicia um novo segmento de gravacao com FFmpeg."""
        # Finaliza segmento anterior
        await self._finalize_segment()

        # Gera nome do arquivo (MKV para melhor compatibilidade com raw H.264)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"camera_{self.camera_id}_{timestamp}.mkv"
        filepath = self.output_dir / filename

        ffmpeg_path = self._get_ffmpeg_path()

        # Comando FFmpeg com copy codec (sem re-encoding)
        cmd = [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel", "error",
            "-rtsp_transport", "tcp",
            "-use_wallclock_as_timestamps", "1",
            "-i", self.rtsp_url,
            "-c:v", "copy",  # Copia video sem re-encoding
            "-c:a", "copy",  # Copia audio sem re-encoding
            "-t", str(self.segment_duration),  # Duracao do segmento
            "-y",  # Sobrescreve se existir
            str(filepath)
        ]

        logger.info(f"Iniciando segmento FFmpeg: {filename}")

        try:
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            logger.error("FFmpeg nao encontrado! Instale FFmpeg no sistema.")
            self._is_recording = False
            return

        self._current_recording = {
            "camera_id": self.camera_id,
            "filename": filename,
            "filepath": str(filepath),
            "start_time": datetime.utcnow(),
            "codec": "copy (H.264)",
            "format": "mkv",
        }

    async def _finalize_segment(self) -> None:
        """Finaliza o segmento atual."""
        if self._process and self._process.poll() is None:
            try:
                self._process.stdin.write(b'q')
                self._process.stdin.flush()
            except Exception:
                pass
            self._process.wait(timeout=10)

        if self._current_recording:
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
                    f"({self._current_recording['duration_seconds']:.1f}s, "
                    f"{self._current_recording['file_size_bytes'] / 1024 / 1024:.1f}MB)"
                )


# Manter compatibilidade com CameraRecorder (alias)
CameraRecorder = FFmpegRecorder


class RecordingService:
    """
    Servico principal de gravacao.

    Gerencia gravadores para multiplas cameras.
    """

    def __init__(self) -> None:
        """Inicializa o servico de gravacao."""
        self._recorders: dict[int, FFmpegRecorder] = {}
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

        # Cria gravador FFmpeg
        recorder = FFmpegRecorder(
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

    async def export_to_mp4(
        self,
        source_path: Path,
        output_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """
        Exporta gravacao MKV para MP4.

        Usado quando usuario quer baixar um trecho especifico.

        Args:
            source_path: Caminho do arquivo MKV.
            output_path: Caminho de saida (opcional).

        Returns:
            Optional[Path]: Caminho do arquivo MP4 ou None se falhar.
        """
        if not source_path.exists():
            return None

        if output_path is None:
            output_path = source_path.with_suffix(".mp4")

        ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"

        cmd = [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(source_path),
            "-c:v", "copy",
            "-c:a", "aac",  # Converte audio para AAC (compativel com MP4)
            "-y",
            str(output_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            if result.returncode == 0 and output_path.exists():
                logger.info(f"Exportado para MP4: {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Erro ao exportar para MP4: {e}")

        return None


# Instancia global do servico
recording_service = RecordingService()
