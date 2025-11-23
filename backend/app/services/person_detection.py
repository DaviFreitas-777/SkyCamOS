"""
Servico de Deteccao de Pessoas do SkyCamOS.

Este modulo implementa a deteccao de pessoas em streams
de video utilizando modelos de deep learning.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, List, Tuple

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DetectedPerson:
    """
    Representa uma pessoa detectada.

    Attributes:
        x: Coordenada X do canto superior esquerdo.
        y: Coordenada Y do canto superior esquerdo.
        width: Largura do bounding box.
        height: Altura do bounding box.
        confidence: Nivel de confianca (0-1).
        track_id: ID de tracking (se disponivel).
    """
    x: int
    y: int
    width: int
    height: int
    confidence: float
    track_id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": round(self.confidence, 3),
            "track_id": self.track_id
        }


@dataclass
class PersonDetectionEvent:
    """
    Representa um evento de deteccao de pessoas.

    Attributes:
        camera_id: ID da camera.
        timestamp: Momento da deteccao.
        persons: Lista de pessoas detectadas.
        frame: Frame onde foi detectado (opcional).
    """
    camera_id: int
    timestamp: datetime
    persons: List[DetectedPerson]
    total_count: int
    frame: Optional[np.ndarray] = None

    def to_dict(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "timestamp": self.timestamp.isoformat(),
            "persons": [p.to_dict() for p in self.persons],
            "total_count": self.total_count,
        }


class PersonDetector:
    """
    Detector de pessoas usando modelo de deep learning.

    Utiliza MobileNet SSD pre-treinado no COCO dataset.
    Alternativa: YOLO (requer mais recursos).
    """

    # Classes do COCO que nos interessam
    PERSON_CLASS_ID = 15  # MobileNet SSD
    CONFIDENCE_THRESHOLD = 0.5

    def __init__(
        self,
        camera_id: int,
        rtsp_url: str,
        confidence_threshold: float = 0.5,
        cooldown_seconds: int = 5,
        use_gpu: bool = False,
    ) -> None:
        """
        Inicializa o detector de pessoas.

        Args:
            camera_id: ID da camera.
            rtsp_url: URL RTSP do stream.
            confidence_threshold: Limiar de confianca (0-1).
            cooldown_seconds: Intervalo minimo entre deteccoes.
            use_gpu: Se deve usar GPU (CUDA).
        """
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.confidence_threshold = confidence_threshold
        self.cooldown_seconds = cooldown_seconds
        self.use_gpu = use_gpu

        self._is_running = False
        self._capture: Optional[cv2.VideoCapture] = None
        self._net: Optional[cv2.dnn.Net] = None
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._last_detection: Optional[datetime] = None
        self._callbacks: List[Callable[[PersonDetectionEvent], None]] = []

        # Estatisticas
        self._total_detections = 0
        self._frames_processed = 0
        self._total_persons_detected = 0

        # Tracking simples
        self._next_track_id = 1
        self._tracked_persons: dict = {}

    def _load_model(self) -> bool:
        """
        Carrega o modelo de deteccao.

        Returns:
            bool: True se carregou com sucesso.
        """
        try:
            # Caminhos dos arquivos do modelo
            models_dir = Path(__file__).parent.parent / "models"
            models_dir.mkdir(exist_ok=True)

            prototxt = models_dir / "MobileNetSSD_deploy.prototxt"
            caffemodel = models_dir / "MobileNetSSD_deploy.caffemodel"

            # Verifica se modelo existe, senao usa HOG como fallback
            if prototxt.exists() and caffemodel.exists():
                self._net = cv2.dnn.readNetFromCaffe(str(prototxt), str(caffemodel))

                if self.use_gpu and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                    self._net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                    self._net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                    logger.info("Usando GPU para deteccao de pessoas")
                else:
                    self._net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                    self._net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

                logger.info("Modelo MobileNet SSD carregado")
                return True
            else:
                # Fallback: usar HOG detector (mais lento, mas nao precisa de arquivos)
                logger.warning("Modelo nao encontrado, usando HOG detector como fallback")
                self._hog = cv2.HOGDescriptor()
                self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
                return True

        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            return False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def add_callback(self, callback: Callable[[PersonDetectionEvent], None]) -> None:
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[PersonDetectionEvent], None]) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def start(self) -> bool:
        """Inicia a deteccao de pessoas."""
        if self._is_running:
            logger.warning(f"Person detector {self.camera_id} ja esta em execucao")
            return False

        logger.info(f"Iniciando deteccao de pessoas para camera {self.camera_id}")

        if not self._load_model():
            return False

        try:
            self._capture = cv2.VideoCapture(self.rtsp_url)

            if not self._capture.isOpened():
                logger.error(f"Falha ao abrir stream: {self.rtsp_url}")
                return False

            self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 3)

            self._is_running = True
            self._stop_event.clear()

            self._task = asyncio.create_task(self._detection_loop())

            logger.info(f"Deteccao de pessoas iniciada para camera {self.camera_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar deteccao: {e}")
            await self.stop()
            return False

    async def stop(self) -> None:
        """Para a deteccao de pessoas."""
        if not self._is_running:
            return

        logger.info(f"Parando deteccao de pessoas para camera {self.camera_id}")

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
        frame_skip = 0

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

                # Processa apenas 1 a cada 3 frames para performance
                frame_skip += 1
                if frame_skip % 3 != 0:
                    await asyncio.sleep(0.01)
                    continue

                # Processa frame
                detection_event = self._process_frame(frame)

                if detection_event and detection_event.total_count > 0:
                    # Verifica cooldown
                    now = datetime.utcnow()
                    if self._last_detection:
                        elapsed = (now - self._last_detection).total_seconds()
                        if elapsed < self.cooldown_seconds:
                            await asyncio.sleep(0.033)
                            continue

                    self._last_detection = now
                    self._total_detections += 1
                    self._total_persons_detected += detection_event.total_count

                    # Notifica callbacks
                    for callback in self._callbacks:
                        try:
                            callback(detection_event)
                        except Exception as e:
                            logger.error(f"Erro em callback de pessoa: {e}")

                self._frames_processed += 1

                # Pausa para nao sobrecarregar CPU
                await asyncio.sleep(0.033)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de deteccao de pessoas: {e}")
                await asyncio.sleep(1)

    def _process_frame(self, frame: np.ndarray) -> Optional[PersonDetectionEvent]:
        """
        Processa um frame para detectar pessoas.
        """
        persons = []

        if self._net is not None:
            persons = self._detect_with_dnn(frame)
        elif hasattr(self, '_hog'):
            persons = self._detect_with_hog(frame)

        if not persons:
            return None

        return PersonDetectionEvent(
            camera_id=self.camera_id,
            timestamp=datetime.utcnow(),
            persons=persons,
            total_count=len(persons),
            frame=frame,
        )

    def _detect_with_dnn(self, frame: np.ndarray) -> List[DetectedPerson]:
        """Deteccao usando DNN (MobileNet SSD)."""
        persons = []
        h, w = frame.shape[:2]

        # Prepara o blob
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)),
            0.007843,
            (300, 300),
            127.5
        )

        self._net.setInput(blob)
        detections = self._net.forward()

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > self.confidence_threshold:
                class_id = int(detections[0, 0, i, 1])

                # Classe 15 = pessoa no MobileNet SSD COCO
                if class_id == 15:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    x1, y1, x2, y2 = box.astype("int")

                    persons.append(DetectedPerson(
                        x=max(0, x1),
                        y=max(0, y1),
                        width=x2 - x1,
                        height=y2 - y1,
                        confidence=float(confidence),
                        track_id=self._get_track_id(x1, y1, x2 - x1, y2 - y1)
                    ))

        return persons

    def _detect_with_hog(self, frame: np.ndarray) -> List[DetectedPerson]:
        """Deteccao usando HOG + SVM (fallback)."""
        persons = []

        # Redimensiona para performance
        small = cv2.resize(frame, (640, 480))
        scale = frame.shape[1] / 640

        # Detecta pessoas
        rects, weights = self._hog.detectMultiScale(
            small,
            winStride=(8, 8),
            padding=(4, 4),
            scale=1.05
        )

        for (x, y, w, h), weight in zip(rects, weights):
            if weight > self.confidence_threshold:
                persons.append(DetectedPerson(
                    x=int(x * scale),
                    y=int(y * scale),
                    width=int(w * scale),
                    height=int(h * scale),
                    confidence=float(weight),
                    track_id=self._get_track_id(int(x * scale), int(y * scale), int(w * scale), int(h * scale))
                ))

        return persons

    def _get_track_id(self, x: int, y: int, w: int, h: int) -> int:
        """
        Obtem ID de tracking para uma deteccao.
        Usa IOU para associar com deteccoes anteriores.
        """
        center = (x + w // 2, y + h // 2)

        # Procura por pessoa proxima ja rastreada
        best_id = None
        best_dist = float('inf')

        for track_id, (tx, ty) in self._tracked_persons.items():
            dist = ((center[0] - tx) ** 2 + (center[1] - ty) ** 2) ** 0.5
            if dist < best_dist and dist < 100:  # Threshold de 100 pixels
                best_dist = dist
                best_id = track_id

        if best_id is not None:
            self._tracked_persons[best_id] = center
            return best_id
        else:
            # Nova pessoa
            track_id = self._next_track_id
            self._next_track_id += 1
            self._tracked_persons[track_id] = center
            return track_id

    def get_stats(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "is_running": self._is_running,
            "total_detections": self._total_detections,
            "total_persons_detected": self._total_persons_detected,
            "frames_processed": self._frames_processed,
            "last_detection": self._last_detection.isoformat() if self._last_detection else None,
            "tracked_persons": len(self._tracked_persons),
            "settings": {
                "confidence_threshold": self.confidence_threshold,
                "cooldown_seconds": self.cooldown_seconds,
                "use_gpu": self.use_gpu,
            },
        }


class PersonDetectionService:
    """
    Servico principal de deteccao de pessoas.
    Gerencia detectores para multiplas cameras.
    """

    def __init__(self) -> None:
        self._detectors: dict[int, PersonDetector] = {}
        self._event_handlers: List[Callable[[PersonDetectionEvent], None]] = []

    def add_event_handler(self, handler: Callable[[PersonDetectionEvent], None]) -> None:
        self._event_handlers.append(handler)

    async def start_detection(
        self,
        camera_id: int,
        rtsp_url: str,
        **kwargs,
    ) -> bool:
        if camera_id in self._detectors and self._detectors[camera_id].is_running:
            return False

        detector = PersonDetector(camera_id, rtsp_url, **kwargs)

        for handler in self._event_handlers:
            detector.add_callback(handler)

        success = await detector.start()

        if success:
            self._detectors[camera_id] = detector

        return success

    async def stop_detection(self, camera_id: int) -> None:
        if camera_id in self._detectors:
            await self._detectors[camera_id].stop()
            del self._detectors[camera_id]

    async def stop_all(self) -> None:
        for camera_id in list(self._detectors.keys()):
            await self.stop_detection(camera_id)

    def get_detector_stats(self, camera_id: int) -> Optional[dict]:
        if camera_id in self._detectors:
            return self._detectors[camera_id].get_stats()
        return None

    def get_all_stats(self) -> dict:
        return {
            "detectors": {
                cam_id: det.get_stats()
                for cam_id, det in self._detectors.items()
            },
            "total_active": len(self._detectors),
        }


# Instancia global do servico
person_detection_service = PersonDetectionService()
