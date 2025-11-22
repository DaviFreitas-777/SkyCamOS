"""
Servico de Gerenciamento de Armazenamento do SkyCamOS.

Este modulo implementa o gerenciamento de espaco em disco,
politica de retencao FIFO e limpeza automatica de gravacoes.
"""

import asyncio
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class StorageInfo:
    """
    Informacoes de armazenamento.

    Attributes:
        total_bytes: Total de espaco em disco.
        used_bytes: Espaco utilizado.
        free_bytes: Espaco livre.
        recordings_bytes: Espaco usado por gravacoes.
        recordings_count: Numero de arquivos de gravacao.
    """

    total_bytes: int
    used_bytes: int
    free_bytes: int
    recordings_bytes: int = 0
    recordings_count: int = 0

    @property
    def used_percent(self) -> float:
        """Retorna porcentagem de uso."""
        if self.total_bytes == 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100

    @property
    def free_percent(self) -> float:
        """Retorna porcentagem livre."""
        return 100.0 - self.used_percent

    @property
    def total_gb(self) -> float:
        """Retorna total em GB."""
        return self.total_bytes / (1024 ** 3)

    @property
    def used_gb(self) -> float:
        """Retorna usado em GB."""
        return self.used_bytes / (1024 ** 3)

    @property
    def free_gb(self) -> float:
        """Retorna livre em GB."""
        return self.free_bytes / (1024 ** 3)

    @property
    def recordings_gb(self) -> float:
        """Retorna tamanho das gravacoes em GB."""
        return self.recordings_bytes / (1024 ** 3)

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            "total_bytes": self.total_bytes,
            "used_bytes": self.used_bytes,
            "free_bytes": self.free_bytes,
            "recordings_bytes": self.recordings_bytes,
            "recordings_count": self.recordings_count,
            "used_percent": round(self.used_percent, 2),
            "free_percent": round(self.free_percent, 2),
            "total_gb": round(self.total_gb, 2),
            "used_gb": round(self.used_gb, 2),
            "free_gb": round(self.free_gb, 2),
            "recordings_gb": round(self.recordings_gb, 2),
        }


@dataclass
class RecordingFile:
    """
    Representa um arquivo de gravacao.

    Attributes:
        path: Caminho do arquivo.
        size_bytes: Tamanho em bytes.
        created_at: Data de criacao.
        camera_id: ID da camera (extraido do nome).
        is_locked: Se esta protegido contra exclusao.
    """

    path: Path
    size_bytes: int
    created_at: datetime
    camera_id: Optional[int] = None
    is_locked: bool = False

    @classmethod
    def from_path(cls, path: Path) -> "RecordingFile":
        """
        Cria instancia a partir de um Path.

        Args:
            path: Caminho do arquivo.

        Returns:
            RecordingFile: Instancia criada.
        """
        stat = path.stat()

        # Tenta extrair camera_id do nome
        camera_id = None
        try:
            name = path.stem
            if name.startswith("camera_"):
                parts = name.split("_")
                if len(parts) >= 2:
                    camera_id = int(parts[1])
        except (ValueError, IndexError):
            pass

        return cls(
            path=path,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            camera_id=camera_id,
        )


class StorageManager:
    """
    Gerenciador de armazenamento.

    Implementa politica FIFO para gerenciamento de espaco
    e limpeza automatica de gravacoes antigas.
    """

    def __init__(
        self,
        recordings_path: Optional[Path] = None,
        max_storage_gb: Optional[int] = None,
        retention_days: Optional[int] = None,
    ) -> None:
        """
        Inicializa o gerenciador de armazenamento.

        Args:
            recordings_path: Diretorio de gravacoes.
            max_storage_gb: Limite de armazenamento em GB.
            retention_days: Dias de retencao.
        """
        self.recordings_path = recordings_path or settings.recordings_dir
        self.max_storage_gb = max_storage_gb or settings.max_storage_gb
        self.retention_days = retention_days or settings.retention_days
        self.max_storage_bytes = self.max_storage_gb * (1024 ** 3)

        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._last_cleanup: Optional[datetime] = None

        # Estatisticas
        self._files_deleted = 0
        self._bytes_freed = 0

    async def start(self, cleanup_interval_hours: int = 1) -> None:
        """
        Inicia o gerenciador com limpeza automatica.

        Args:
            cleanup_interval_hours: Intervalo de limpeza em horas.
        """
        if self._is_running:
            return

        self._is_running = True
        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop(cleanup_interval_hours)
        )

        logger.info(
            f"Gerenciador de armazenamento iniciado. "
            f"Limite: {self.max_storage_gb}GB, Retencao: {self.retention_days} dias"
        )

    async def stop(self) -> None:
        """Para o gerenciador."""
        self._is_running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Gerenciador de armazenamento parado")

    async def _cleanup_loop(self, interval_hours: int) -> None:
        """
        Loop de limpeza automatica.

        Args:
            interval_hours: Intervalo entre limpezas.
        """
        while self._is_running:
            try:
                await self.cleanup()
                self._last_cleanup = datetime.utcnow()
            except Exception as e:
                logger.error(f"Erro na limpeza automatica: {e}")

            await asyncio.sleep(interval_hours * 3600)

    def get_storage_info(self) -> StorageInfo:
        """
        Obtem informacoes de armazenamento.

        Returns:
            StorageInfo: Informacoes de armazenamento.
        """
        # Informacoes do disco
        try:
            disk_usage = shutil.disk_usage(self.recordings_path)
            total_bytes = disk_usage.total
            free_bytes = disk_usage.free
            used_bytes = disk_usage.used
        except Exception as e:
            logger.error(f"Erro ao obter info do disco: {e}")
            total_bytes = 0
            free_bytes = 0
            used_bytes = 0

        # Informacoes das gravacoes
        recordings_bytes = 0
        recordings_count = 0

        try:
            for file in self._get_recording_files():
                recordings_bytes += file.size_bytes
                recordings_count += 1
        except Exception as e:
            logger.error(f"Erro ao calcular tamanho das gravacoes: {e}")

        return StorageInfo(
            total_bytes=total_bytes,
            used_bytes=used_bytes,
            free_bytes=free_bytes,
            recordings_bytes=recordings_bytes,
            recordings_count=recordings_count,
        )

    def _get_recording_files(self) -> list[RecordingFile]:
        """
        Lista todos os arquivos de gravacao.

        Returns:
            list[RecordingFile]: Lista de arquivos.
        """
        files = []
        extensions = {".mp4", ".avi", ".mkv", ".webm"}

        try:
            for path in self.recordings_path.rglob("*"):
                if path.is_file() and path.suffix.lower() in extensions:
                    try:
                        files.append(RecordingFile.from_path(path))
                    except Exception as e:
                        logger.debug(f"Erro ao processar arquivo {path}: {e}")
        except Exception as e:
            logger.error(f"Erro ao listar arquivos: {e}")

        return files

    async def cleanup(self) -> dict:
        """
        Executa limpeza de arquivos antigos e excesso de espaco.

        Returns:
            dict: Resultado da limpeza.
        """
        logger.info("Iniciando limpeza de armazenamento...")

        deleted_count = 0
        freed_bytes = 0

        files = self._get_recording_files()

        # Ordena por data (mais antigos primeiro)
        files.sort(key=lambda f: f.created_at)

        # 1. Remove arquivos alem do periodo de retencao
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)

        for file in files[:]:
            if file.created_at < cutoff_date and not file.is_locked:
                try:
                    size = file.size_bytes
                    file.path.unlink()
                    deleted_count += 1
                    freed_bytes += size
                    files.remove(file)
                    logger.debug(f"Removido (retencao): {file.path.name}")
                except Exception as e:
                    logger.error(f"Erro ao remover {file.path}: {e}")

        # 2. Remove arquivos se exceder limite de armazenamento
        total_size = sum(f.size_bytes for f in files)

        while total_size > self.max_storage_bytes and files:
            # Remove o mais antigo que nao esta protegido
            for file in files:
                if not file.is_locked:
                    try:
                        size = file.size_bytes
                        file.path.unlink()
                        deleted_count += 1
                        freed_bytes += size
                        total_size -= size
                        files.remove(file)
                        logger.debug(f"Removido (espaco): {file.path.name}")
                    except Exception as e:
                        logger.error(f"Erro ao remover {file.path}: {e}")
                    break
            else:
                # Todos os arquivos restantes estao protegidos
                break

        # Atualiza estatisticas
        self._files_deleted += deleted_count
        self._bytes_freed += freed_bytes

        result = {
            "deleted_count": deleted_count,
            "freed_bytes": freed_bytes,
            "freed_mb": round(freed_bytes / (1024 ** 2), 2),
            "remaining_files": len(files),
            "remaining_bytes": sum(f.size_bytes for f in files),
        }

        logger.info(
            f"Limpeza concluida: {deleted_count} arquivos removidos, "
            f"{result['freed_mb']}MB liberados"
        )

        return result

    async def cleanup_camera(self, camera_id: int) -> dict:
        """
        Remove todas as gravacoes de uma camera.

        Args:
            camera_id: ID da camera.

        Returns:
            dict: Resultado da limpeza.
        """
        logger.info(f"Removendo gravacoes da camera {camera_id}...")

        deleted_count = 0
        freed_bytes = 0

        files = self._get_recording_files()

        for file in files:
            if file.camera_id == camera_id and not file.is_locked:
                try:
                    size = file.size_bytes
                    file.path.unlink()
                    deleted_count += 1
                    freed_bytes += size
                except Exception as e:
                    logger.error(f"Erro ao remover {file.path}: {e}")

        return {
            "camera_id": camera_id,
            "deleted_count": deleted_count,
            "freed_bytes": freed_bytes,
            "freed_mb": round(freed_bytes / (1024 ** 2), 2),
        }

    async def get_camera_storage(self, camera_id: int) -> dict:
        """
        Obtem uso de armazenamento por camera.

        Args:
            camera_id: ID da camera.

        Returns:
            dict: Informacoes de uso.
        """
        files = [f for f in self._get_recording_files() if f.camera_id == camera_id]

        total_bytes = sum(f.size_bytes for f in files)

        oldest = min(files, key=lambda f: f.created_at).created_at if files else None
        newest = max(files, key=lambda f: f.created_at).created_at if files else None

        return {
            "camera_id": camera_id,
            "files_count": len(files),
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 ** 2), 2),
            "total_gb": round(total_bytes / (1024 ** 3), 2),
            "oldest_recording": oldest.isoformat() if oldest else None,
            "newest_recording": newest.isoformat() if newest else None,
        }

    def get_stats(self) -> dict:
        """
        Retorna estatisticas do gerenciador.

        Returns:
            dict: Estatisticas.
        """
        return {
            "recordings_path": str(self.recordings_path),
            "max_storage_gb": self.max_storage_gb,
            "retention_days": self.retention_days,
            "is_running": self._is_running,
            "last_cleanup": self._last_cleanup.isoformat() if self._last_cleanup else None,
            "total_files_deleted": self._files_deleted,
            "total_bytes_freed": self._bytes_freed,
            "total_mb_freed": round(self._bytes_freed / (1024 ** 2), 2),
        }

    async def ensure_space(self, required_bytes: int) -> bool:
        """
        Garante que existe espaco suficiente.

        Remove arquivos antigos se necessario para liberar espaco.

        Args:
            required_bytes: Bytes necessarios.

        Returns:
            bool: True se conseguiu liberar espaco.
        """
        info = self.get_storage_info()

        if info.free_bytes >= required_bytes:
            return True

        # Precisa liberar espaco
        needed = required_bytes - info.free_bytes
        logger.info(f"Liberando {needed / (1024**2):.2f}MB para nova gravacao")

        files = self._get_recording_files()
        files.sort(key=lambda f: f.created_at)

        freed = 0
        for file in files:
            if file.is_locked:
                continue

            try:
                size = file.size_bytes
                file.path.unlink()
                freed += size

                if freed >= needed:
                    break
            except Exception as e:
                logger.error(f"Erro ao liberar espaco: {e}")

        return freed >= needed


# Instancia global do servico
storage_manager = StorageManager()
