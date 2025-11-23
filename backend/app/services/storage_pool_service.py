"""
Servico de Storage Pool do SkyCamOS.

Gerencia multiplos pools de armazenamento para distribuir
gravacoes em diferentes discos/diretorios.
"""

import asyncio
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.storage_pool import StoragePool, StoragePoolStatus, CameraStorageAssignment

logger = logging.getLogger(__name__)


class StoragePoolService:
    """
    Servico para gerenciar pools de armazenamento.

    Permite configurar multiplos discos para distribuir gravacoes,
    monitorar espaco e fazer failover automatico.
    """

    def __init__(self) -> None:
        """Inicializa o servico."""
        self._check_interval = 60  # Verificar discos a cada 60 segundos
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Inicia o monitoramento periodico dos pools."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("[StoragePool] Servico iniciado")

    async def stop(self) -> None:
        """Para o monitoramento."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[StoragePool] Servico parado")

    async def _monitor_loop(self) -> None:
        """Loop de monitoramento dos pools."""
        while self._running:
            try:
                from app.core.database import async_session_factory
                async with async_session_factory() as db:
                    await self.update_all_pool_stats(db)
            except Exception as e:
                logger.error(f"[StoragePool] Erro no monitoramento: {e}")

            await asyncio.sleep(self._check_interval)

    # ==========================================
    # CRUD de Storage Pools
    # ==========================================

    async def create_pool(
        self,
        db: AsyncSession,
        name: str,
        path: str,
        max_size_gb: int = 0,
        min_free_gb: int = 10,
        retention_days: int = 30,
        priority: int = 100,
        is_default: bool = False,
    ) -> Optional[StoragePool]:
        """
        Cria um novo pool de armazenamento.

        Args:
            db: Sessao do banco.
            name: Nome do pool.
            path: Caminho absoluto.
            max_size_gb: Limite de tamanho em GB.
            min_free_gb: Espaco minimo livre.
            retention_days: Dias de retencao.
            priority: Prioridade (menor = mais prioritario).
            is_default: Se e o pool padrao.

        Returns:
            StoragePool criado ou None se falhar.
        """
        # Valida se o caminho existe ou pode ser criado
        pool_path = Path(path)
        try:
            pool_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"[StoragePool] Erro ao criar diretorio {path}: {e}")
            return None

        # Verifica se o caminho ja existe
        result = await db.execute(
            select(StoragePool).where(StoragePool.path == path)
        )
        if result.scalar_one_or_none():
            logger.warning(f"[StoragePool] Caminho ja existe: {path}")
            return None

        # Se for default, remove default dos outros
        if is_default:
            await db.execute(
                update(StoragePool).values(is_default=False)
            )

        # Cria pool
        pool = StoragePool(
            name=name,
            path=path,
            max_size_gb=max_size_gb,
            min_free_gb=min_free_gb,
            retention_days=retention_days,
            priority=priority,
            is_default=is_default,
        )

        # Obtem estatisticas do disco
        disk_stats = self._get_disk_stats(path)
        if disk_stats:
            pool.total_size_bytes = disk_stats["total"]
            pool.used_size_bytes = disk_stats["used"]
            pool.free_size_bytes = disk_stats["free"]

        db.add(pool)
        await db.commit()
        await db.refresh(pool)

        logger.info(f"[StoragePool] Pool criado: {name} ({path})")
        return pool

    async def get_pool(self, db: AsyncSession, pool_id: int) -> Optional[StoragePool]:
        """Obtem um pool por ID."""
        result = await db.execute(
            select(StoragePool).where(StoragePool.id == pool_id)
        )
        return result.scalar_one_or_none()

    async def get_all_pools(self, db: AsyncSession) -> List[StoragePool]:
        """Lista todos os pools."""
        result = await db.execute(
            select(StoragePool).order_by(StoragePool.priority)
        )
        return list(result.scalars().all())

    async def get_default_pool(self, db: AsyncSession) -> Optional[StoragePool]:
        """Obtem o pool padrao."""
        result = await db.execute(
            select(StoragePool).where(StoragePool.is_default == True)
        )
        pool = result.scalar_one_or_none()

        # Se nao tem default, retorna o primeiro ativo
        if not pool:
            result = await db.execute(
                select(StoragePool)
                .where(StoragePool.is_enabled == True)
                .order_by(StoragePool.priority)
                .limit(1)
            )
            pool = result.scalar_one_or_none()

        return pool

    async def update_pool(
        self,
        db: AsyncSession,
        pool_id: int,
        **kwargs
    ) -> Optional[StoragePool]:
        """Atualiza um pool."""
        pool = await self.get_pool(db, pool_id)
        if not pool:
            return None

        # Se definindo como default, remove dos outros
        if kwargs.get("is_default"):
            await db.execute(
                update(StoragePool).values(is_default=False)
            )

        for key, value in kwargs.items():
            if hasattr(pool, key):
                setattr(pool, key, value)

        await db.commit()
        await db.refresh(pool)
        return pool

    async def delete_pool(self, db: AsyncSession, pool_id: int) -> bool:
        """Remove um pool (nao deleta arquivos)."""
        pool = await self.get_pool(db, pool_id)
        if not pool:
            return False

        await db.delete(pool)
        await db.commit()

        logger.info(f"[StoragePool] Pool removido: {pool.name}")
        return True

    # ==========================================
    # Gerenciamento de Cameras
    # ==========================================

    async def assign_camera_to_pool(
        self,
        db: AsyncSession,
        camera_id: int,
        pool_id: int,
        is_primary: bool = True,
    ) -> Optional[CameraStorageAssignment]:
        """Associa uma camera a um pool de storage."""
        # Remove associacao anterior se for primario
        if is_primary:
            await db.execute(
                select(CameraStorageAssignment)
                .where(
                    CameraStorageAssignment.camera_id == camera_id,
                    CameraStorageAssignment.is_primary == True
                )
            )
            # Delete existing primary
            result = await db.execute(
                select(CameraStorageAssignment)
                .where(
                    CameraStorageAssignment.camera_id == camera_id,
                    CameraStorageAssignment.is_primary == True
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                await db.delete(existing)

        assignment = CameraStorageAssignment(
            camera_id=camera_id,
            storage_pool_id=pool_id,
            is_primary=is_primary,
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        return assignment

    async def get_camera_pool(
        self,
        db: AsyncSession,
        camera_id: int,
    ) -> Optional[StoragePool]:
        """Obtem o pool de uma camera."""
        result = await db.execute(
            select(CameraStorageAssignment)
            .where(
                CameraStorageAssignment.camera_id == camera_id,
                CameraStorageAssignment.is_primary == True
            )
        )
        assignment = result.scalar_one_or_none()

        if assignment:
            return await self.get_pool(db, assignment.storage_pool_id)

        # Retorna pool padrao se camera nao tem associacao
        return await self.get_default_pool(db)

    async def get_recording_path(
        self,
        db: AsyncSession,
        camera_id: int,
    ) -> Path:
        """
        Obtem o caminho de gravacao para uma camera.

        Retorna caminho no formato: pool_path/camera_{id}/continuous/YYYY/MM/DD/

        Args:
            db: Sessao do banco.
            camera_id: ID da camera.

        Returns:
            Path do diretorio de gravacao.
        """
        pool = await self.get_camera_pool(db, camera_id)

        if pool:
            base_path = Path(pool.path)
        else:
            # Fallback para diretorio padrao
            base_path = settings.recordings_dir

        now = datetime.utcnow()
        recording_path = (
            base_path /
            f"camera_{camera_id}" /
            "continuous" /
            str(now.year) /
            f"{now.month:02d}" /
            f"{now.day:02d}"
        )

        recording_path.mkdir(parents=True, exist_ok=True)
        return recording_path

    # ==========================================
    # Estatisticas e Monitoramento
    # ==========================================

    def _get_disk_stats(self, path: str) -> Optional[dict]:
        """Obtem estatisticas de disco de um caminho."""
        try:
            total, used, free = shutil.disk_usage(path)
            return {
                "total": total,
                "used": used,
                "free": free,
            }
        except Exception as e:
            logger.error(f"[StoragePool] Erro ao obter stats de {path}: {e}")
            return None

    async def update_pool_stats(self, db: AsyncSession, pool_id: int) -> None:
        """Atualiza estatisticas de um pool."""
        pool = await self.get_pool(db, pool_id)
        if not pool:
            return

        stats = self._get_disk_stats(pool.path)
        if stats:
            pool.total_size_bytes = stats["total"]
            pool.used_size_bytes = stats["used"]
            pool.free_size_bytes = stats["free"]
            pool.last_checked_at = datetime.utcnow()

            # Atualiza status
            if pool.free_gb < pool.min_free_gb:
                pool.status = StoragePoolStatus.FULL.value
            elif not os.path.exists(pool.path):
                pool.status = StoragePoolStatus.ERROR.value
            else:
                pool.status = StoragePoolStatus.ACTIVE.value

            await db.commit()

    async def update_all_pool_stats(self, db: AsyncSession) -> None:
        """Atualiza estatisticas de todos os pools."""
        pools = await self.get_all_pools(db)
        for pool in pools:
            await self.update_pool_stats(db, pool.id)

    async def get_best_available_pool(self, db: AsyncSession) -> Optional[StoragePool]:
        """
        Retorna o melhor pool disponivel para gravacao.

        Considera prioridade e espaco livre.
        """
        pools = await self.get_all_pools(db)

        for pool in pools:
            if pool.is_available:
                return pool

        logger.warning("[StoragePool] Nenhum pool disponivel!")
        return None

    def count_recordings_in_pool(self, pool_path: str) -> int:
        """Conta arquivos de gravacao em um pool."""
        path = Path(pool_path)
        if not path.exists():
            return 0

        count = 0
        for ext in [".mkv", ".mp4", ".avi"]:
            count += len(list(path.rglob(f"*{ext}")))

        return count


# Instancia global
storage_pool_service = StoragePoolService()
