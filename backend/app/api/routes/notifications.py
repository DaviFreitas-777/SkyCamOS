"""
Rotas de Notificacoes do SkyCamOS.

Endpoints para gerenciamento de notificacoes do sistema e push notifications.
"""

import logging
import json
import os
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models import User
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class NotificationResponse(BaseModel):
    """Schema de resposta para notificacao."""
    id: str
    title: str
    message: str
    type: str = "info"
    read: bool = False
    timestamp: str
    url: Optional[str] = None


class NotificationListResponse(BaseModel):
    """Schema de resposta para lista de notificacoes."""
    notifications: List[NotificationResponse]
    unreadCount: int
    total: int


class VapidKeyResponse(BaseModel):
    """Schema de resposta para VAPID key."""
    publicKey: str


class PushSubscription(BaseModel):
    """Schema para subscription de push."""
    subscription: Dict[str, Any]


# Armazenamento em memoria (em producao usar banco de dados)
notifications_store: dict = {}
push_subscriptions: dict = {}  # user_id -> [subscriptions]

# VAPID keys para push notifications
# Em producao, gerar com: openssl ecparam -genkey -name prime256v1 -out private_key.pem
# Ou usar py_vapid: vapid --gen --applicationServerKey
VAPID_PUBLIC_KEY = os.getenv(
    "VAPID_PUBLIC_KEY",
    "BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U"
)
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_EMAIL = os.getenv("VAPID_EMAIL", "mailto:admin@skycamos.local")


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista notificacoes do usuario.

    - **limit**: Quantidade maxima de notificacoes a retornar
    """
    user_id = str(current_user.id)

    # Buscar notificacoes do usuario (em memoria por enquanto)
    user_notifications = notifications_store.get(user_id, [])

    # Ordenar por timestamp (mais recentes primeiro)
    sorted_notifications = sorted(
        user_notifications,
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:limit]

    unread_count = sum(1 for n in user_notifications if not n.get("read", False))

    return NotificationListResponse(
        notifications=sorted_notifications,
        unreadCount=unread_count,
        total=len(user_notifications)
    )


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marca todas as notificacoes do usuario como lidas.
    """
    user_id = str(current_user.id)

    if user_id in notifications_store:
        for notification in notifications_store[user_id]:
            notification["read"] = True

    logger.info(f"Todas notificacoes marcadas como lidas para usuario {user_id}")

    return {"message": "Todas notificacoes marcadas como lidas"}


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marca uma notificacao especifica como lida.

    - **notification_id**: ID da notificacao
    """
    user_id = str(current_user.id)

    if user_id not in notifications_store:
        raise HTTPException(status_code=404, detail="Notificacao nao encontrada")

    for notification in notifications_store[user_id]:
        if notification.get("id") == notification_id:
            notification["read"] = True
            logger.info(f"Notificacao {notification_id} marcada como lida")
            return {"message": "Notificacao marcada como lida"}

    raise HTTPException(status_code=404, detail="Notificacao nao encontrada")


@router.get("/vapid-key", response_model=VapidKeyResponse)
async def get_vapid_key():
    """
    Retorna a chave publica VAPID para push notifications.
    """
    return VapidKeyResponse(publicKey=VAPID_PUBLIC_KEY)


@router.post("/subscribe")
async def subscribe_to_push(
    data: PushSubscription,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Registra uma subscription para push notifications.

    O frontend envia o objeto de subscription obtido do PushManager.
    """
    user_id = str(current_user.id)
    subscription = data.subscription

    if user_id not in push_subscriptions:
        push_subscriptions[user_id] = []

    # Verificar se subscription ja existe
    endpoint = subscription.get("endpoint", "")
    for existing in push_subscriptions[user_id]:
        if existing.get("endpoint") == endpoint:
            # Atualizar subscription existente
            existing.update(subscription)
            logger.info(f"Push subscription atualizada para usuario {user_id}")
            return {"message": "Subscription atualizada"}

    # Adicionar nova subscription
    push_subscriptions[user_id].append(subscription)
    logger.info(f"Nova push subscription para usuario {user_id}")

    return {"message": "Subscription registrada com sucesso"}


@router.post("/unsubscribe")
async def unsubscribe_from_push(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove todas as subscriptions de push do usuario.
    """
    user_id = str(current_user.id)

    if user_id in push_subscriptions:
        count = len(push_subscriptions[user_id])
        del push_subscriptions[user_id]
        logger.info(f"Removidas {count} subscriptions do usuario {user_id}")

    return {"message": "Subscriptions removidas"}


async def send_push_notification(user_id: str, title: str, body: str, data: dict = None):
    """
    Envia uma push notification para todas as subscriptions de um usuario.

    Args:
        user_id: ID do usuario
        title: Titulo da notificacao
        body: Corpo da notificacao
        data: Dados adicionais opcionais
    """
    if user_id not in push_subscriptions:
        return

    if not VAPID_PRIVATE_KEY:
        logger.warning("VAPID_PRIVATE_KEY nao configurada - push notifications desabilitadas")
        return

    try:
        from pywebpush import webpush, WebPushException

        payload = json.dumps({
            "title": title,
            "body": body,
            "data": data or {},
            "icon": "/icons/icon-192x192.svg",
            "badge": "/icons/icon-96x96.svg"
        })

        vapid_claims = {"sub": VAPID_EMAIL}

        for subscription in push_subscriptions[user_id]:
            try:
                webpush(
                    subscription_info=subscription,
                    data=payload,
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=vapid_claims
                )
                logger.debug(f"Push enviado para usuario {user_id}")
            except WebPushException as e:
                logger.error(f"Erro ao enviar push: {e}")
                # Subscription invalida - remover
                if e.response and e.response.status_code in (404, 410):
                    push_subscriptions[user_id].remove(subscription)
    except ImportError:
        logger.warning("pywebpush nao instalado - push notifications desabilitadas")


def add_notification(user_id: str, notification: dict):
    """
    Adiciona uma notificacao para um usuario.

    Funcao utilitaria para ser chamada por outros modulos.
    """
    import uuid
    from datetime import datetime

    if user_id not in notifications_store:
        notifications_store[user_id] = []

    notification["id"] = str(uuid.uuid4())
    notification["timestamp"] = datetime.utcnow().isoformat()
    notification["read"] = False

    notifications_store[user_id].append(notification)

    # Limitar a 100 notificacoes por usuario
    if len(notifications_store[user_id]) > 100:
        notifications_store[user_id] = notifications_store[user_id][-100:]

    return notification
