"""
Servico de Deteccao de Movimento do SkyCamOS.

Este modulo implementa a deteccao de movimento em streams
de video utilizando OpenCV.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MotionEvent:
    """
    Representa um evento de movimento detectado.

    Attributes:
        camera_id: ID da camera onde foi detectado.
        timestamp: Momento da deteccao.
        area: Area do movimento em pixels.
        confidence: Nivel de confianca da deteccao (0-100).
        bounding_box: Coordenadas do retangulo envolvente.
        frame: Frame onde foi detectado (opcional).
    """

    camera_id: int
    timestamp: datetime
    area: int
    confidence: float
    bounding_box: dict
    contours_count: int = 0
    frame: Optional[np.ndarray] = None

    def to_dict(self) -> dict:
        """Converte para dicionario (sem frame)."""
        return {
            "camera_id": self.camera_id,
            "timestamp": self.timestamp.isoformat(),
            "area": self.area,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box,
            "contours_count": self.contours_count,
        }


class MotionDetector:
    """
    Detector de movimento para uma camera.

    Utiliza subtracao de background para detectar movimento.
    """

    def __init__(
        self,
        camera_id: int,
        rtsp_url: str,
        threshold: Optional[int] = None,
        min_area: Optional[int] = None,
        cooldown_seconds: Optional[int] = None,
    ) -> None:
        """
        Inicializa o detector de movimento.

        Args:
            camera_id: ID da camera.
            rtsp_url: URL RTSP do stream.
            threshold: Limiar de deteccao (0-255).
            min_area: Area minima para considerar movimento.
            cooldown_seconds: Intervalo minimo entre deteccoes.
        """
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.threshold = threshold or settings.motion_threshold
        self.min_area = min_area or settings.motion_min_area
        self.cooldown_seconds = cooldown_seconds or settings.motion_cooldown_seconds

        self._is_running = False
        self._capture: Optional[cv2.VideoCapture] = None
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True,
        )
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._last_motion: Optional[datetime] = None
        self._callbacks: list[Callable[[MotionEvent], None]] = []

        # Estatisticas
        self._total_detections = 0
        self._frames_processed = 0

    @property
    def is_running(self) -> bool:
        """Retorna se esta em execucao."""
        return self._is_running

    @property
    def total_detections(self) -> int:
        """Retorna total de deteccoes."""
        return self._total_detections

    def add_callback(self, callback: Callable[[MotionEvent], None]) -> None:
        """
        Adiciona callback para eventos de movimento.

        Args:
            callback: Funcao a ser chamada quando movimento for detectado.
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[MotionEvent], None]) -> None:
        """
        Remove callback.

        Args:
            callback: Funcao a ser removida.
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def start(self) -> bool:
        """
        Inicia a deteccao de movimento.

        Returns:
            bool: True se iniciou com sucesso.
        """
        if self._is_running:
            logger.warning(f"Detector {self.camera_id} ja esta em execucao")
            return False

        logger.info(f"Iniciando deteccao de movimento para camera {self.camera_id}")

        try:
            self._capture = cv2.VideoCapture(self.rtsp_url)

            if not self._capture.isOpened():
                logger.error(f"Falha ao abrir stream: {self.rtsp_url}")
                return False

            self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 3)

            self._is_running = True
            self._stop_event.clear()

            self._task = asyncio.create_task(self._detection_loop())

            logger.info(f"Deteccao de movimento iniciada para camera {self.camera_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar deteccao: {e}")
            await self.stop()
            return False

    async def stop(self) -> None:
        """Para a deteccao de movimento."""
        if not self._is_running:
            return

        logger.info(f"Parando deteccao de movimento para camera {self.camera_id}")

        self._is_running = False
        self._stop_event.set()

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()

        if self._capture:
            self._capture.release()
            self._capture = None

    async def _detection_loop(self) -> None:
        """Loop principal de deteccao."""
        while self._is_running and not self._stop_event.is_set():
            try:
                ret, frame = self._capture.read()

                if not ret:
                    logger.warning(f"Falha ao ler frame da camera {self.camera_id}")
                    await asyncio.sleep(0.5)

                    # Tenta reconectar
                    self._capture.release()
                    self._capture = cv2.VideoCapture(self.rtsp_url)
                    continue

                # Processa frame
                motion_event = self._process_frame(frame)

                if motion_event:
                    # Verifica cooldown
                    now = datetime.utcnow()
                    if self._last_motion:
                        elapsed = (now - self._last_motion).total_seconds()
                        if elapsed < self.cooldown_seconds:
                            continue

                    self._last_motion = now
                    self._total_detections += 1

                    # Notifica callbacks
                    for callback in self._callbacks:
                        try:
                            callback(motion_event)
                        except Exception as e:
                            logger.error(f"Erro em callback de movimento: {e}")

                self._frames_processed += 1

                # Pausa para nao sobrecarregar CPU
                await asyncio.sleep(0.033)  # ~30 fps

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de deteccao: {e}")
                await asyncio.sleep(1)

    def _process_frame(self, frame: np.ndarray) -> Optional[MotionEvent]:
        """
        Processa um frame para detectar movimento.

        Args:
            frame: Frame a ser processado.

        Returns:
            Optional[MotionEvent]: Evento de movimento ou None.
        """
        # Redimensiona para processamento mais rapido
        small_frame = cv2.resize(frame, (640, 360))

        # Converte para escala de cinza
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

        # Aplica blur para reduzir ruido
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)

        # Aplica subtracao de background
        fg_mask = self._bg_subtractor.apply(blurred)

        # Remove sombras (valor 127 no MOG2)
        _, thresh = cv2.threshold(fg_mask, 250, 255, cv2.THRESH_BINARY)

        # Dilata para preencher buracos
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dilated = cv2.dilate(thresh, kernel, iterations=2)

        # Encontra contornos
        contours, _ = cv2.findContours(
            dilated,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:
            return None

        # Filtra contornos por area
        significant_contours = [
            c for c in contours
            if cv2.contourArea(c) >= self.min_area
        ]

        if not significant_contours:
            return None

        # Calcula area total e bounding box combinado
        total_area = sum(cv2.contourArea(c) for c in significant_contours)

        # Combina todos os contornos em um bounding box
        all_points = np.vstack(significant_contours)
        x, y, w, h = cv2.boundingRect(all_points)

        # Ajusta coordenadas para resolucao original
        scale_x = frame.shape[1] / 640
        scale_y = frame.shape[0] / 360

        bounding_box = {
            "x": int(x * scale_x),
            "y": int(y * scale_y),
            "width": int(w * scale_x),
            "height": int(h * scale_y),
        }

        # Calcula confianca baseada na area
        frame_area = 640 * 360
        confidence = min(100, (total_area / frame_area) * 1000)

        return MotionEvent(
            camera_id=self.camera_id,
            timestamp=datetime.utcnow(),
            area=int(total_area * scale_x * scale_y),
            confidence=round(confidence, 2),
            bounding_box=bounding_box,
            contours_count=len(significant_contours),
            frame=frame,
        )

    def get_stats(self) -> dict:
        """
        Retorna estatisticas do detector.

        Returns:
            dict: Estatisticas de deteccao.
        """
        return {
            "camera_id": self.camera_id,
            "is_running": self._is_running,
            "total_detections": self._total_detections,
            "frames_processed": self._frames_processed,
            "last_motion": self._last_motion.isoformat() if self._last_motion else None,
            "settings": {
                "threshold": self.threshold,
                "min_area": self.min_area,
                "cooldown_seconds": self.cooldown_seconds,
            },
        }


class MotionDetectionService:
    """
    Servico principal de deteccao de movimento.

    Gerencia detectores para multiplas cameras.
    """

    def __init__(self) -> None:
        """Inicializa o servico."""
        self._detectors: dict[int, MotionDetector] = {}
        self._event_handlers: list[Callable[[MotionEvent], None]] = []

    def add_event_handler(self, handler: Callable[[MotionEvent], None]) -> None:
        """
        Adiciona handler global para eventos.

        Args:
            handler: Funcao a ser chamada para todos os eventos.
        """
        self._event_handlers.append(handler)

    async def start_detection(
        self,
        camera_id: int,
        rtsp_url: str,
        **kwargs,
    ) -> bool:
        """
        Inicia deteccao para uma camera.

        Args:
            camera_id: ID da camera.
            rtsp_url: URL RTSP.
            **kwargs: Parametros adicionais do detector.

        Returns:
            bool: True se iniciou com sucesso.
        """
        if camera_id in self._detectors and self._detectors[camera_id].is_running:
            return False

        detector = MotionDetector(camera_id, rtsp_url, **kwargs)

        # Adiciona handlers globais
        for handler in self._event_handlers:
            detector.add_callback(handler)

        success = await detector.start()

        if success:
            self._detectors[camera_id] = detector

        return success

    async def stop_detection(self, camera_id: int) -> None:
        """
        Para deteccao de uma camera.

        Args:
            camera_id: ID da camera.
        """
        if camera_id in self._detectors:
            await self._detectors[camera_id].stop()
            del self._detectors[camera_id]

    async def stop_all(self) -> None:
        """Para todas as deteccoes."""
        for camera_id in list(self._detectors.keys()):
            await self.stop_detection(camera_id)

    def get_detector_stats(self, camera_id: int) -> Optional[dict]:
        """
        Retorna estatisticas de um detector.

        Args:
            camera_id: ID da camera.

        Returns:
            Optional[dict]: Estatisticas ou None.
        """
        if camera_id in self._detectors:
            return self._detectors[camera_id].get_stats()
        return None


# Instancia global do servico
motion_detection_service = MotionDetectionService()
