"""
Servico de Notificacoes do SkyCamOS.

Este modulo implementa o envio de notificacoes push,
email e WebSocket para alertar usuarios sobre eventos.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Tipos de notificacao."""

    MOTION = "motion"
    ALERT = "alert"
    SYSTEM = "system"
    RECORDING = "recording"
    CONNECTION = "connection"
    STORAGE = "storage"


class NotificationPriority(str, Enum):
    """Prioridade da notificacao."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Notification:
    """
    Representa uma notificacao.

    Attributes:
        id: ID unico da notificacao.
        type: Tipo da notificacao.
        priority: Prioridade.
        title: Titulo.
        message: Mensagem.
        camera_id: ID da camera (se aplicavel).
        event_id: ID do evento (se aplicavel).
        data: Dados adicionais.
        created_at: Data de criacao.
        sent_at: Data de envio.
        read_at: Data de leitura.
    """

    id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    camera_id: Optional[int] = None
    event_id: Optional[int] = None
    data: Optional[dict] = None
    created_at: datetime = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Inicializa campos padrao."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "priority": self.priority.value if isinstance(self.priority, Enum) else self.priority,
            "title": self.title,
            "message": self.message,
            "camera_id": self.camera_id,
            "event_id": self.event_id,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }

    def to_json(self) -> str:
        """Converte para JSON."""
        return json.dumps(self.to_dict())


class WebSocketManager:
    """
    Gerenciador de conexoes WebSocket.

    Mantém registro de conexoes ativas e permite
    envio de notificacoes em tempo real.
    """

    def __init__(self) -> None:
        """Inicializa o gerenciador."""
        self._connections: dict[str, set] = {}  # user_id -> websockets
        self._all_connections: set = set()

    async def connect(self, websocket: Any, user_id: Optional[str] = None) -> None:
        """
        Registra uma nova conexao WebSocket.

        Args:
            websocket: Objeto WebSocket.
            user_id: ID do usuario (opcional).
        """
        self._all_connections.add(websocket)

        if user_id:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(websocket)

        logger.info(f"WebSocket conectado. Total: {len(self._all_connections)}")

    async def disconnect(self, websocket: Any, user_id: Optional[str] = None) -> None:
        """
        Remove uma conexao WebSocket.

        Args:
            websocket: Objeto WebSocket.
            user_id: ID do usuario (opcional).
        """
        self._all_connections.discard(websocket)

        if user_id and user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]

        logger.info(f"WebSocket desconectado. Total: {len(self._all_connections)}")

    async def send_to_user(self, user_id: str, message: dict) -> int:
        """
        Envia mensagem para um usuario especifico.

        Args:
            user_id: ID do usuario.
            message: Mensagem a enviar.

        Returns:
            int: Numero de conexoes que receberam.
        """
        if user_id not in self._connections:
            return 0

        sent = 0
        json_message = json.dumps(message)

        for ws in list(self._connections[user_id]):
            try:
                await ws.send_text(json_message)
                sent += 1
            except Exception as e:
                logger.error(f"Erro ao enviar WebSocket: {e}")
                await self.disconnect(ws, user_id)

        return sent

    async def broadcast(self, message: dict) -> int:
        """
        Envia mensagem para todas as conexoes.

        Args:
            message: Mensagem a enviar.

        Returns:
            int: Numero de conexoes que receberam.
        """
        sent = 0
        json_message = json.dumps(message)

        for ws in list(self._all_connections):
            try:
                await ws.send_text(json_message)
                sent += 1
            except Exception as e:
                logger.error(f"Erro ao enviar broadcast: {e}")
                self._all_connections.discard(ws)

        return sent

    @property
    def connection_count(self) -> int:
        """Retorna numero total de conexoes."""
        return len(self._all_connections)


class NotificationService:
    """
    Servico principal de notificacoes.

    Gerencia envio de notificacoes por diferentes canais.
    """

    def __init__(self) -> None:
        """Inicializa o servico de notificacoes."""
        self._websocket_manager = WebSocketManager()
        self._notification_history: list[Notification] = []
        self._max_history = 1000
        self._handlers: list[Callable[[Notification], None]] = []

        # Contadores
        self._sent_count = 0
        self._failed_count = 0

    @property
    def websocket_manager(self) -> WebSocketManager:
        """Retorna o gerenciador WebSocket."""
        return self._websocket_manager

    def add_handler(self, handler: Callable[[Notification], None]) -> None:
        """
        Adiciona handler para notificacoes.

        Args:
            handler: Funcao a ser chamada para cada notificacao.
        """
        self._handlers.append(handler)

    async def send(self, notification: Notification) -> bool:
        """
        Envia uma notificacao.

        Args:
            notification: Notificacao a enviar.

        Returns:
            bool: True se enviou com sucesso.
        """
        try:
            # Adiciona ao historico
            self._notification_history.append(notification)
            if len(self._notification_history) > self._max_history:
                self._notification_history = self._notification_history[-self._max_history:]

            # Envia via WebSocket
            sent = await self._websocket_manager.broadcast(notification.to_dict())

            notification.sent_at = datetime.utcnow()
            self._sent_count += 1

            # Notifica handlers
            for handler in self._handlers:
                try:
                    handler(notification)
                except Exception as e:
                    logger.error(f"Erro em handler de notificacao: {e}")

            logger.info(
                f"Notificacao enviada: {notification.title} "
                f"({sent} conexoes)"
            )

            return True

        except Exception as e:
            logger.error(f"Erro ao enviar notificacao: {e}")
            self._failed_count += 1
            return False

    async def send_motion_alert(
        self,
        camera_id: int,
        camera_name: str,
        confidence: float,
        event_id: Optional[int] = None,
        snapshot_url: Optional[str] = None,
    ) -> bool:
        """
        Envia alerta de movimento.

        Args:
            camera_id: ID da camera.
            camera_name: Nome da camera.
            confidence: Nivel de confianca.
            event_id: ID do evento.
            snapshot_url: URL do snapshot.

        Returns:
            bool: True se enviou com sucesso.
        """
        import uuid

        notification = Notification(
            id=str(uuid.uuid4()),
            type=NotificationType.MOTION,
            priority=NotificationPriority.HIGH if confidence > 70 else NotificationPriority.NORMAL,
            title=f"Movimento detectado - {camera_name}",
            message=f"Movimento detectado com {confidence:.1f}% de confianca",
            camera_id=camera_id,
            event_id=event_id,
            data={
                "confidence": confidence,
                "snapshot_url": snapshot_url,
            },
        )

        return await self.send(notification)

    async def send_connection_alert(
        self,
        camera_id: int,
        camera_name: str,
        is_connected: bool,
    ) -> bool:
        """
        Envia alerta de conexao.

        Args:
            camera_id: ID da camera.
            camera_name: Nome da camera.
            is_connected: True se conectou, False se desconectou.

        Returns:
            bool: True se enviou com sucesso.
        """
        import uuid

        status = "conectada" if is_connected else "desconectada"

        notification = Notification(
            id=str(uuid.uuid4()),
            type=NotificationType.CONNECTION,
            priority=NotificationPriority.HIGH if not is_connected else NotificationPriority.NORMAL,
            title=f"Camera {status} - {camera_name}",
            message=f"A camera {camera_name} foi {status}",
            camera_id=camera_id,
            data={
                "is_connected": is_connected,
            },
        )

        return await self.send(notification)

    async def send_storage_alert(
        self,
        used_percent: float,
        available_gb: float,
    ) -> bool:
        """
        Envia alerta de armazenamento.

        Args:
            used_percent: Porcentagem de uso.
            available_gb: GB disponiveis.

        Returns:
            bool: True se enviou com sucesso.
        """
        import uuid

        priority = NotificationPriority.CRITICAL if used_percent > 95 else (
            NotificationPriority.HIGH if used_percent > 90 else NotificationPriority.NORMAL
        )

        notification = Notification(
            id=str(uuid.uuid4()),
            type=NotificationType.STORAGE,
            priority=priority,
            title="Alerta de armazenamento",
            message=f"Armazenamento em {used_percent:.1f}% ({available_gb:.1f}GB disponiveis)",
            data={
                "used_percent": used_percent,
                "available_gb": available_gb,
            },
        )

        return await self.send(notification)

    async def send_system_notification(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[dict] = None,
    ) -> bool:
        """
        Envia notificacao de sistema.

        Args:
            title: Titulo.
            message: Mensagem.
            priority: Prioridade.
            data: Dados adicionais.

        Returns:
            bool: True se enviou com sucesso.
        """
        import uuid

        notification = Notification(
            id=str(uuid.uuid4()),
            type=NotificationType.SYSTEM,
            priority=priority,
            title=title,
            message=message,
            data=data,
        )

        return await self.send(notification)

    def get_recent_notifications(
        self,
        limit: int = 50,
        type_filter: Optional[NotificationType] = None,
    ) -> list[dict]:
        """
        Retorna notificacoes recentes.

        Args:
            limit: Numero maximo de notificacoes.
            type_filter: Filtrar por tipo.

        Returns:
            list[dict]: Lista de notificacoes.
        """
        notifications = self._notification_history

        if type_filter:
            notifications = [n for n in notifications if n.type == type_filter]

        return [n.to_dict() for n in notifications[-limit:]]

    def get_stats(self) -> dict:
        """
        Retorna estatisticas do servico.

        Returns:
            dict: Estatisticas.
        """
        return {
            "total_sent": self._sent_count,
            "total_failed": self._failed_count,
            "history_size": len(self._notification_history),
            "websocket_connections": self._websocket_manager.connection_count,
        }


# Instancia global do servico
notification_service = NotificationService()
