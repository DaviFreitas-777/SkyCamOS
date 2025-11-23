"""
Rotas de Storage do SkyCamOS.

Endpoints para gerenciar pools de armazenamento e
configurar onde cada camera grava.
"""

import logging
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.models.storage_pool import StoragePool, StoragePoolStatus
from app.services.storage_pool_service import storage_pool_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ==========================================
# Schemas
# ==========================================

class StoragePoolCreate(BaseModel):
    """Schema para criar um storage pool."""
    name: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., min_length=1, max_length=500)
    max_size_gb: int = Field(default=0, ge=0)
    min_free_gb: int = Field(default=10, ge=1)
    retention_days: int = Field(default=30, ge=1)
    priority: int = Field(default=100, ge=1)
    is_default: bool = False


class StoragePoolUpdate(BaseModel):
    """Schema para atualizar um storage pool."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    max_size_gb: Optional[int] = Field(None, ge=0)
    min_free_gb: Optional[int] = Field(None, ge=1)
    retention_days: Optional[int] = Field(None, ge=1)
    priority: Optional[int] = Field(None, ge=1)
    is_default: Optional[bool] = None
    is_enabled: Optional[bool] = None


class StoragePoolResponse(BaseModel):
    """Schema de resposta de storage pool."""
    id: int
    name: str
    path: str
    max_size_gb: int
    min_free_gb: int
    retention_days: int
    priority: int
    is_default: bool
    is_enabled: bool
    status: str
    total_size_bytes: int
    used_size_bytes: int
    free_size_bytes: int
    recording_count: int
    usage_percent: float
    free_gb: float
    is_available: bool

    class Config:
        from_attributes = True


class CameraAssignmentRequest(BaseModel):
    """Schema para associar camera a pool."""
    camera_id: int
    storage_pool_id: int
    is_primary: bool = True


# ==========================================
# Endpoints
# ==========================================

@router.get(
    "/pools",
    response_model=List[StoragePoolResponse],
    summary="Listar pools",
    description="Lista todos os pools de armazenamento.",
)
async def list_pools(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[StoragePoolResponse]:
    """Lista todos os storage pools."""
    pools = await storage_pool_service.get_all_pools(db)

    return [
        StoragePoolResponse(
            id=p.id,
            name=p.name,
            path=p.path,
            max_size_gb=p.max_size_gb,
            min_free_gb=p.min_free_gb,
            retention_days=p.retention_days,
            priority=p.priority,
            is_default=p.is_default,
            is_enabled=p.is_enabled,
            status=p.status,
            total_size_bytes=p.total_size_bytes,
            used_size_bytes=p.used_size_bytes,
            free_size_bytes=p.free_size_bytes,
            recording_count=p.recording_count,
            usage_percent=p.usage_percent,
            free_gb=p.free_gb,
            is_available=p.is_available,
        )
        for p in pools
    ]


@router.post(
    "/pools",
    response_model=StoragePoolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar pool",
    description="Cria um novo pool de armazenamento.",
)
async def create_pool(
    data: StoragePoolCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StoragePoolResponse:
    """Cria um novo storage pool."""
    # Verifica permissao (apenas admin)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem criar pools",
        )

    pool = await storage_pool_service.create_pool(
        db=db,
        name=data.name,
        path=data.path,
        max_size_gb=data.max_size_gb,
        min_free_gb=data.min_free_gb,
        retention_days=data.retention_days,
        priority=data.priority,
        is_default=data.is_default,
    )

    if not pool:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao criar pool. Verifique se o caminho e valido e unico.",
        )

    return StoragePoolResponse(
        id=pool.id,
        name=pool.name,
        path=pool.path,
        max_size_gb=pool.max_size_gb,
        min_free_gb=pool.min_free_gb,
        retention_days=pool.retention_days,
        priority=pool.priority,
        is_default=pool.is_default,
        is_enabled=pool.is_enabled,
        status=pool.status,
        total_size_bytes=pool.total_size_bytes,
        used_size_bytes=pool.used_size_bytes,
        free_size_bytes=pool.free_size_bytes,
        recording_count=pool.recording_count,
        usage_percent=pool.usage_percent,
        free_gb=pool.free_gb,
        is_available=pool.is_available,
    )


@router.get(
    "/pools/{pool_id}",
    response_model=StoragePoolResponse,
    summary="Obter pool",
    description="Obtem detalhes de um pool.",
)
async def get_pool(
    pool_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StoragePoolResponse:
    """Obtem um storage pool por ID."""
    pool = await storage_pool_service.get_pool(db, pool_id)

    if not pool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pool nao encontrado",
        )

    return StoragePoolResponse(
        id=pool.id,
        name=pool.name,
        path=pool.path,
        max_size_gb=pool.max_size_gb,
        min_free_gb=pool.min_free_gb,
        retention_days=pool.retention_days,
        priority=pool.priority,
        is_default=pool.is_default,
        is_enabled=pool.is_enabled,
        status=pool.status,
        total_size_bytes=pool.total_size_bytes,
        used_size_bytes=pool.used_size_bytes,
        free_size_bytes=pool.free_size_bytes,
        recording_count=pool.recording_count,
        usage_percent=pool.usage_percent,
        free_gb=pool.free_gb,
        is_available=pool.is_available,
    )


@router.patch(
    "/pools/{pool_id}",
    response_model=StoragePoolResponse,
    summary="Atualizar pool",
    description="Atualiza configuracoes de um pool.",
)
async def update_pool(
    pool_id: int,
    data: StoragePoolUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StoragePoolResponse:
    """Atualiza um storage pool."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem atualizar pools",
        )

    update_data = data.model_dump(exclude_unset=True)
    pool = await storage_pool_service.update_pool(db, pool_id, **update_data)

    if not pool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pool nao encontrado",
        )

    return StoragePoolResponse(
        id=pool.id,
        name=pool.name,
        path=pool.path,
        max_size_gb=pool.max_size_gb,
        min_free_gb=pool.min_free_gb,
        retention_days=pool.retention_days,
        priority=pool.priority,
        is_default=pool.is_default,
        is_enabled=pool.is_enabled,
        status=pool.status,
        total_size_bytes=pool.total_size_bytes,
        used_size_bytes=pool.used_size_bytes,
        free_size_bytes=pool.free_size_bytes,
        recording_count=pool.recording_count,
        usage_percent=pool.usage_percent,
        free_gb=pool.free_gb,
        is_available=pool.is_available,
    )


@router.delete(
    "/pools/{pool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover pool",
    description="Remove um pool (nao deleta gravacoes).",
)
async def delete_pool(
    pool_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """Remove um storage pool."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem remover pools",
        )

    success = await storage_pool_service.delete_pool(db, pool_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pool nao encontrado",
        )


@router.post(
    "/pools/{pool_id}/refresh",
    response_model=StoragePoolResponse,
    summary="Atualizar estatisticas",
    description="Atualiza estatisticas de uso do disco.",
)
async def refresh_pool_stats(
    pool_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StoragePoolResponse:
    """Atualiza estatisticas de um pool."""
    await storage_pool_service.update_pool_stats(db, pool_id)

    pool = await storage_pool_service.get_pool(db, pool_id)

    if not pool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pool nao encontrado",
        )

    return StoragePoolResponse(
        id=pool.id,
        name=pool.name,
        path=pool.path,
        max_size_gb=pool.max_size_gb,
        min_free_gb=pool.min_free_gb,
        retention_days=pool.retention_days,
        priority=pool.priority,
        is_default=pool.is_default,
        is_enabled=pool.is_enabled,
        status=pool.status,
        total_size_bytes=pool.total_size_bytes,
        used_size_bytes=pool.used_size_bytes,
        free_size_bytes=pool.free_size_bytes,
        recording_count=pool.recording_count,
        usage_percent=pool.usage_percent,
        free_gb=pool.free_gb,
        is_available=pool.is_available,
    )


@router.post(
    "/cameras/assign",
    summary="Associar camera a pool",
    description="Define em qual pool uma camera deve gravar.",
)
async def assign_camera_to_pool(
    data: CameraAssignmentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Associa uma camera a um pool de storage."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem configurar storage",
        )

    assignment = await storage_pool_service.assign_camera_to_pool(
        db=db,
        camera_id=data.camera_id,
        pool_id=data.storage_pool_id,
        is_primary=data.is_primary,
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao associar camera ao pool",
        )

    return {
        "message": "Camera associada ao pool com sucesso",
        "camera_id": data.camera_id,
        "storage_pool_id": data.storage_pool_id,
    }


@router.get(
    "/cameras/{camera_id}/pool",
    summary="Pool da camera",
    description="Retorna o pool de storage de uma camera.",
)
async def get_camera_pool(
    camera_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Obtem o pool de uma camera."""
    pool = await storage_pool_service.get_camera_pool(db, camera_id)

    if not pool:
        return {
            "camera_id": camera_id,
            "storage_pool": None,
            "using_default": True,
        }

    return {
        "camera_id": camera_id,
        "storage_pool": {
            "id": pool.id,
            "name": pool.name,
            "path": pool.path,
        },
        "using_default": pool.is_default,
    }
