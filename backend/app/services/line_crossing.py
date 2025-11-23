"""
Servico de Deteccao de Cruzamento de Linha do SkyCamOS.

Este modulo implementa a deteccao de objetos/pessoas
cruzando linhas virtuais definidas pelo usuario.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, List, Tuple

import cv2
import numpy as np

from app.config import settings
from app.services.person_detection import PersonDetector, DetectedPerson

logger = logging.getLogger(__name__)


class CrossingDirection(str, Enum):
    """Direcao do cruzamento."""
    IN = "in"       # Entrando (abaixo para cima ou esquerda para direita)
    OUT = "out"     # Saindo (cima para baixo ou direita para esquerda)
    BOTH = "both"   # Ambas as direcoes


@dataclass
class VirtualLine:
    """
    Representa uma linha virtual para deteccao.

    Attributes:
        id: ID unico da linha.
        name: Nome da linha.
        start_point: Ponto inicial (x, y).
        end_point: Ponto final (x, y).
        direction: Direcao a detectar.
        color: Cor para visualizacao (BGR).
    """
    id: str
    name: str
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    direction: CrossingDirection = CrossingDirection.BOTH
    color: Tuple[int, int, int] = (0, 255, 0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "start_point": list(self.start_point),
            "end_point": list(self.end_point),
            "direction": self.direction.value,
        }


@dataclass
class LineCrossingEvent:
    """
    Representa um evento de cruzamento de linha.

    Attributes:
        camera_id: ID da camera.
        line_id: ID da linha cruzada.
        line_name: Nome da linha.
        timestamp: Momento do cruzamento.
        direction: Direcao do cruzamento.
        object_id: ID do objeto que cruzou.
        object_type: Tipo do objeto (person, vehicle, etc).
        confidence: Confianca da deteccao.
    """
    camera_id: int
    line_id: str
    line_name: str
    timestamp: datetime
    direction: CrossingDirection
    object_id: int
    object_type: str = "person"
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "line_id": self.line_id,
            "line_name": self.line_name,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction.value,
            "object_id": self.object_id,
            "object_type": self.object_type,
            "confidence": round(self.confidence, 3),
        }


class LineCrossingDetector:
    """
    Detector de cruzamento de linhas virtuais.

    Combina deteccao de pessoas com rastreamento para
    identificar cruzamentos de linhas definidas.
    """

    def __init__(
        self,
        camera_id: int,
        rtsp_url: str,
        lines: List[VirtualLine] = None,
        cooldown_seconds: int = 2,
    ) -> None:
        """
        Inicializa o detector de cruzamento.

        Args:
            camera_id: ID da camera.
            rtsp_url: URL RTSP do stream.
            lines: Lista de linhas virtuais a monitorar.
            cooldown_seconds: Intervalo entre deteccoes do mesmo objeto.
        """
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.lines = lines or []
        self.cooldown_seconds = cooldown_seconds

        self._is_running = False
        self._capture: Optional[cv2.VideoCapture] = None
        self._person_detector: Optional[PersonDetector] = None
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._callbacks: List[Callable[[LineCrossingEvent], None]] = []

        # Tracking de posicoes anteriores
        self._previous_positions: dict[int, Tuple[int, int]] = {}  # track_id -> (x, y)
        self._crossed_objects: dict[str, set] = {}  # line_id -> set of track_ids that crossed
        self._last_crossing_time: dict[Tuple[str, int], datetime] = {}  # (line_id, track_id) -> time

        # Contadores
        self._counts: dict[str, dict] = {}  # line_id -> {"in": 0, "out": 0}
        self._total_crossings = 0

    def add_line(self, line: VirtualLine) -> None:
        """Adiciona uma linha virtual."""
        self.lines.append(line)
        self._crossed_objects[line.id] = set()
        self._counts[line.id] = {"in": 0, "out": 0}

    def remove_line(self, line_id: str) -> None:
        """Remove uma linha virtual."""
        self.lines = [l for l in self.lines if l.id != line_id]
        self._crossed_objects.pop(line_id, None)
        self._counts.pop(line_id, None)

    def add_callback(self, callback: Callable[[LineCrossingEvent], None]) -> None:
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[LineCrossingEvent], None]) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def start(self) -> bool:
        """Inicia a deteccao de cruzamentos."""
        if self._is_running:
            return False

        logger.info(f"Iniciando line crossing para camera {self.camera_id}")

        try:
            self._capture = cv2.VideoCapture(self.rtsp_url)

            if not self._capture.isOpened():
                logger.error(f"Falha ao abrir stream: {self.rtsp_url}")
                return False

            self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 3)

            # Inicializa detector de pessoas
            self._person_detector = PersonDetector(
                self.camera_id,
                self.rtsp_url,
                confidence_threshold=0.5,
                cooldown_seconds=0  # Sem cooldown para tracking continuo
            )

            self._is_running = True
            self._stop_event.clear()

            self._task = asyncio.create_task(self._detection_loop())

            logger.info(f"Line crossing iniciado para camera {self.camera_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar line crossing: {e}")
            await self.stop()
            return False

    async def stop(self) -> None:
        """Para a deteccao de cruzamentos."""
        if not self._is_running:
            return

        logger.info(f"Parando line crossing para camera {self.camera_id}")

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
        # Carrega modelo do detector de pessoas
        if not self._person_detector._load_model():
            logger.error("Falha ao carregar modelo de deteccao")
            return

        frame_skip = 0

        while self._is_running and not self._stop_event.is_set():
            try:
                ret, frame = self._capture.read()

                if not ret:
                    await asyncio.sleep(0.5)
                    self._capture.release()
                    self._capture = cv2.VideoCapture(self.rtsp_url)
                    continue

                # Processa 1 a cada 2 frames
                frame_skip += 1
                if frame_skip % 2 != 0:
                    await asyncio.sleep(0.01)
                    continue

                # Detecta pessoas
                event = self._person_detector._process_frame(frame)

                if event and event.persons:
                    # Verifica cruzamentos para cada pessoa
                    for person in event.persons:
                        if person.track_id is None:
                            continue

                        center = (
                            person.x + person.width // 2,
                            person.y + person.height
                        )

                        # Verifica cruzamento com cada linha
                        for line in self.lines:
                            crossing = self._check_crossing(
                                person.track_id,
                                center,
                                line
                            )

                            if crossing:
                                self._total_crossings += 1
                                self._counts[line.id][crossing.value] += 1

                                crossing_event = LineCrossingEvent(
                                    camera_id=self.camera_id,
                                    line_id=line.id,
                                    line_name=line.name,
                                    timestamp=datetime.utcnow(),
                                    direction=crossing,
                                    object_id=person.track_id,
                                    confidence=person.confidence,
                                )

                                # Notifica callbacks
                                for callback in self._callbacks:
                                    try:
                                        callback(crossing_event)
                                    except Exception as e:
                                        logger.error(f"Erro em callback: {e}")

                        # Atualiza posicao anterior
                        self._previous_positions[person.track_id] = center

                await asyncio.sleep(0.033)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de line crossing: {e}")
                await asyncio.sleep(1)

    def _check_crossing(
        self,
        track_id: int,
        current_pos: Tuple[int, int],
        line: VirtualLine
    ) -> Optional[CrossingDirection]:
        """
        Verifica se houve cruzamento de linha.

        Args:
            track_id: ID do objeto rastreado.
            current_pos: Posicao atual (x, y).
            line: Linha virtual a verificar.

        Returns:
            Optional[CrossingDirection]: Direcao do cruzamento ou None.
        """
        if track_id not in self._previous_positions:
            return None

        prev_pos = self._previous_positions[track_id]

        # Verifica cooldown
        key = (line.id, track_id)
        if key in self._last_crossing_time:
            elapsed = (datetime.utcnow() - self._last_crossing_time[key]).total_seconds()
            if elapsed < self.cooldown_seconds:
                return None

        # Verifica se cruzou a linha
        crossed, direction = self._line_segment_intersection(
            prev_pos,
            current_pos,
            line.start_point,
            line.end_point
        )

        if not crossed:
            return None

        # Verifica se a direcao corresponde ao filtro
        if line.direction != CrossingDirection.BOTH:
            if direction != line.direction:
                return None

        # Registra cruzamento
        self._last_crossing_time[key] = datetime.utcnow()

        return direction

    def _line_segment_intersection(
        self,
        p1: Tuple[int, int],
        p2: Tuple[int, int],
        p3: Tuple[int, int],
        p4: Tuple[int, int]
    ) -> Tuple[bool, Optional[CrossingDirection]]:
        """
        Verifica se dois segmentos de linha se interceptam.

        Args:
            p1, p2: Pontos do segmento de movimento.
            p3, p4: Pontos da linha virtual.

        Returns:
            Tuple[bool, Optional[CrossingDirection]]: Se cruzou e a direcao.
        """
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4

        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)

        if abs(denom) < 1e-10:
            return False, None

        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom

        if 0 <= ua <= 1 and 0 <= ub <= 1:
            # Houve interseccao - determina direcao
            # Calcula o produto vetorial para determinar o lado
            cross = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)

            if cross > 0:
                return True, CrossingDirection.IN
            else:
                return True, CrossingDirection.OUT

        return False, None

    def get_counts(self) -> dict:
        """Retorna contadores de cruzamento."""
        return {
            "total": self._total_crossings,
            "by_line": self._counts.copy(),
        }

    def reset_counts(self) -> None:
        """Reseta contadores."""
        self._total_crossings = 0
        for line_id in self._counts:
            self._counts[line_id] = {"in": 0, "out": 0}

    def get_stats(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "is_running": self._is_running,
            "lines": [l.to_dict() for l in self.lines],
            "counts": self.get_counts(),
            "tracked_objects": len(self._previous_positions),
        }


class LineCrossingService:
    """
    Servico principal de deteccao de cruzamento de linhas.
    Gerencia detectores para multiplas cameras.
    """

    def __init__(self) -> None:
        self._detectors: dict[int, LineCrossingDetector] = {}
        self._event_handlers: List[Callable[[LineCrossingEvent], None]] = []

    def add_event_handler(self, handler: Callable[[LineCrossingEvent], None]) -> None:
        self._event_handlers.append(handler)

    async def start_detection(
        self,
        camera_id: int,
        rtsp_url: str,
        lines: List[VirtualLine] = None,
        **kwargs,
    ) -> bool:
        if camera_id in self._detectors and self._detectors[camera_id].is_running:
            return False

        detector = LineCrossingDetector(camera_id, rtsp_url, lines, **kwargs)

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

    def add_line(self, camera_id: int, line: VirtualLine) -> bool:
        if camera_id in self._detectors:
            self._detectors[camera_id].add_line(line)
            return True
        return False

    def remove_line(self, camera_id: int, line_id: str) -> bool:
        if camera_id in self._detectors:
            self._detectors[camera_id].remove_line(line_id)
            return True
        return False

    def get_counts(self, camera_id: int) -> Optional[dict]:
        if camera_id in self._detectors:
            return self._detectors[camera_id].get_counts()
        return None

    def reset_counts(self, camera_id: int) -> bool:
        if camera_id in self._detectors:
            self._detectors[camera_id].reset_counts()
            return True
        return False

    def get_detector_stats(self, camera_id: int) -> Optional[dict]:
        if camera_id in self._detectors:
            return self._detectors[camera_id].get_stats()
        return None


# Instancia global do servico
line_crossing_service = LineCrossingService()
