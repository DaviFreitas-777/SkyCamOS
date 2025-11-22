# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Disk Manager
Gerenciador de espaco em disco e politica FIFO para gravacoes
"""

import os
import asyncio
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any, Tuple
import threading

try:
    import psutil
except ImportError:
    psutil = None

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileDeletedEvent
except ImportError:
    Observer = None
    FileSystemEventHandler = object

from ..utils.logger import get_logger, LoggerMixin

logger = get_logger("disk_manager")


class StoragePolicy(Enum):
    """Politicas de gerenciamento de armazenamento."""
    FIFO = "fifo"           # First In, First Out - remove mais antigos
    SIZE = "size"           # Remove maiores primeiro
    MANUAL = "manual"       # Nao remove automaticamente
    HYBRID = "hybrid"       # Combina FIFO com limite de tamanho


class AlertLevel(Enum):
    """Niveis de alerta de espaco em disco."""
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    FULL = "full"


@dataclass
class DiskUsage:
    """Informacoes de uso de disco."""
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent_used: float
    mount_point: str = ""

    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024 ** 3)

    @property
    def used_gb(self) -> float:
        return self.used_bytes / (1024 ** 3)

    @property
    def free_gb(self) -> float:
        return self.free_bytes / (1024 ** 3)

    @property
    def alert_level(self) -> AlertLevel:
        if self.percent_used >= 99:
            return AlertLevel.FULL
        elif self.percent_used >= 95:
            return AlertLevel.CRITICAL
        elif self.percent_used >= 80:
            return AlertLevel.WARNING
        return AlertLevel.OK


@dataclass
class RecordingFile:
    """Representa um arquivo de gravacao."""
    path: Path
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    camera_id: str = ""
    duration_seconds: float = 0.0

    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 ** 2)

    @property
    def age_days(self) -> float:
        delta = datetime.now() - self.created_at
        return delta.total_seconds() / 86400


class RecordingWatcher(FileSystemEventHandler if FileSystemEventHandler else object):
    """
    Observador de arquivos de gravacao.
    Monitora mudancas no diretorio de gravacoes.
    """

    def __init__(self, callback: Callable[[str, Path], None]):
        """
        Inicializa o observador.

        Args:
            callback: Funcao a chamar quando arquivo mudar (evento, path)
        """
        super().__init__()
        self.callback = callback

    def on_created(self, event):
        """Arquivo criado."""
        if not event.is_directory:
            self.callback("created", Path(event.src_path))

    def on_deleted(self, event):
        """Arquivo deletado."""
        if not event.is_directory:
            self.callback("deleted", Path(event.src_path))

    def on_modified(self, event):
        """Arquivo modificado."""
        if not event.is_directory:
            self.callback("modified", Path(event.src_path))


class DiskManager(LoggerMixin):
    """
    Gerenciador de espaco em disco.
    Monitora espaco e implementa politica FIFO para gravacoes antigas.
    """

    # Extensoes de arquivo de video
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.ts', '.m4v'}

    def __init__(
        self,
        recordings_dir: Path,
        max_storage_gb: float = 100.0,
        min_free_space_gb: float = 10.0,
        policy: StoragePolicy = StoragePolicy.FIFO,
        check_interval: float = 60.0,
        warning_threshold: float = 80.0,
        critical_threshold: float = 95.0
    ):
        """
        Inicializa o gerenciador de disco.

        Args:
            recordings_dir: Diretorio de gravacoes
            max_storage_gb: Espaco maximo para gravacoes em GB
            min_free_space_gb: Espaco minimo livre em disco em GB
            policy: Politica de remocao de arquivos
            check_interval: Intervalo de verificacao em segundos
            warning_threshold: Limiar para alerta de warning (%)
            critical_threshold: Limiar para alerta critico (%)
        """
        self.recordings_dir = Path(recordings_dir)
        self.max_storage_gb = max_storage_gb
        self.min_free_space_gb = min_free_space_gb
        self.policy = policy
        self.check_interval = check_interval
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._observer: Optional[Any] = None
        self._callbacks: List[Callable[[AlertLevel, DiskUsage], None]] = []
        self._files_cache: Dict[str, RecordingFile] = {}
        self._last_alert: Optional[AlertLevel] = None

        # Garante que o diretorio existe
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

    def add_alert_callback(self, callback: Callable[[AlertLevel, DiskUsage], None]) -> None:
        """Adiciona callback para alertas de disco."""
        self._callbacks.append(callback)

    def _notify_alert(self, level: AlertLevel, usage: DiskUsage) -> None:
        """Notifica callbacks sobre alerta de disco."""
        # Evita notificacoes repetidas do mesmo nivel
        if level == self._last_alert:
            return

        self._last_alert = level

        for callback in self._callbacks:
            try:
                callback(level, usage)
            except Exception as e:
                self.logger.error(f"Erro em callback de alerta: {e}")

    def get_disk_usage(self, path: Optional[Path] = None) -> DiskUsage:
        """
        Obtem uso de disco para um caminho.

        Args:
            path: Caminho a verificar (padrao: recordings_dir)

        Returns:
            Informacoes de uso de disco
        """
        target_path = path or self.recordings_dir

        if psutil:
            try:
                usage = psutil.disk_usage(str(target_path))
                return DiskUsage(
                    total_bytes=usage.total,
                    used_bytes=usage.used,
                    free_bytes=usage.free,
                    percent_used=usage.percent,
                    mount_point=str(target_path)
                )
            except Exception as e:
                self.logger.error(f"Erro ao obter uso de disco (psutil): {e}")

        # Fallback usando shutil
        try:
            total, used, free = shutil.disk_usage(target_path)
            return DiskUsage(
                total_bytes=total,
                used_bytes=used,
                free_bytes=free,
                percent_used=(used / total) * 100 if total > 0 else 0,
                mount_point=str(target_path)
            )
        except Exception as e:
            self.logger.error(f"Erro ao obter uso de disco: {e}")
            return DiskUsage(
                total_bytes=0,
                used_bytes=0,
                free_bytes=0,
                percent_used=0
            )

    def get_recordings_size(self) -> Tuple[int, int]:
        """
        Calcula tamanho total das gravacoes.

        Returns:
            Tupla (total_bytes, num_arquivos)
        """
        total_size = 0
        file_count = 0

        try:
            for file_path in self.recordings_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.VIDEO_EXTENSIONS:
                    total_size += file_path.stat().st_size
                    file_count += 1
        except Exception as e:
            self.logger.error(f"Erro ao calcular tamanho das gravacoes: {e}")

        return total_size, file_count

    def scan_recordings(self) -> List[RecordingFile]:
        """
        Escaneia todos os arquivos de gravacao.

        Returns:
            Lista de arquivos de gravacao
        """
        recordings = []

        try:
            for file_path in self.recordings_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.VIDEO_EXTENSIONS:
                    try:
                        stat = file_path.stat()
                        recording = RecordingFile(
                            path=file_path,
                            size_bytes=stat.st_size,
                            created_at=datetime.fromtimestamp(stat.st_ctime),
                            modified_at=datetime.fromtimestamp(stat.st_mtime)
                        )

                        # Tenta extrair camera_id do nome do arquivo ou diretorio
                        parts = file_path.relative_to(self.recordings_dir).parts
                        if len(parts) > 1:
                            recording.camera_id = parts[0]

                        recordings.append(recording)
                        self._files_cache[str(file_path)] = recording

                    except Exception as e:
                        self.logger.debug(f"Erro ao processar arquivo {file_path}: {e}")

            # Ordena por data de criacao (mais antigos primeiro)
            recordings.sort(key=lambda r: r.created_at)

        except Exception as e:
            self.logger.error(f"Erro ao escanear gravacoes: {e}")

        self.logger.info(f"Scan concluido: {len(recordings)} arquivos encontrados")
        return recordings

    def get_files_to_delete(self, target_free_bytes: int) -> List[RecordingFile]:
        """
        Determina quais arquivos devem ser deletados para liberar espaco.

        Args:
            target_free_bytes: Bytes a liberar

        Returns:
            Lista de arquivos a deletar
        """
        recordings = self.scan_recordings()
        to_delete = []
        bytes_to_free = 0

        if self.policy == StoragePolicy.FIFO:
            # Remove mais antigos primeiro
            for recording in recordings:
                if bytes_to_free >= target_free_bytes:
                    break
                to_delete.append(recording)
                bytes_to_free += recording.size_bytes

        elif self.policy == StoragePolicy.SIZE:
            # Remove maiores primeiro
            recordings.sort(key=lambda r: r.size_bytes, reverse=True)
            for recording in recordings:
                if bytes_to_free >= target_free_bytes:
                    break
                to_delete.append(recording)
                bytes_to_free += recording.size_bytes

        elif self.policy == StoragePolicy.HYBRID:
            # Primeiro remove arquivos mais antigos que 30 dias
            old_threshold = datetime.now() - timedelta(days=30)
            old_files = [r for r in recordings if r.created_at < old_threshold]

            for recording in old_files:
                if bytes_to_free >= target_free_bytes:
                    break
                to_delete.append(recording)
                bytes_to_free += recording.size_bytes

            # Se ainda precisar, continua com FIFO
            if bytes_to_free < target_free_bytes:
                remaining = [r for r in recordings if r not in to_delete]
                for recording in remaining:
                    if bytes_to_free >= target_free_bytes:
                        break
                    to_delete.append(recording)
                    bytes_to_free += recording.size_bytes

        return to_delete

    async def cleanup(self, force: bool = False) -> int:
        """
        Executa limpeza de arquivos antigos.

        Args:
            force: Se True, ignora politica MANUAL

        Returns:
            Numero de arquivos removidos
        """
        if self.policy == StoragePolicy.MANUAL and not force:
            self.logger.debug("Politica MANUAL ativa, limpeza ignorada")
            return 0

        # Verifica espaco atual
        disk_usage = self.get_disk_usage()
        recordings_size, _ = self.get_recordings_size()
        recordings_gb = recordings_size / (1024 ** 3)

        files_deleted = 0
        bytes_freed = 0

        # Verifica se precisa liberar espaco
        need_cleanup = False
        target_bytes = 0

        # Limite de espaco para gravacoes
        if recordings_gb > self.max_storage_gb:
            target_bytes = int((recordings_gb - self.max_storage_gb) * (1024 ** 3))
            need_cleanup = True
            self.logger.info(f"Gravacoes ({recordings_gb:.1f}GB) excedem limite ({self.max_storage_gb}GB)")

        # Limite de espaco livre em disco
        if disk_usage.free_gb < self.min_free_space_gb:
            free_needed = int((self.min_free_space_gb - disk_usage.free_gb) * (1024 ** 3))
            target_bytes = max(target_bytes, free_needed)
            need_cleanup = True
            self.logger.info(f"Espaco livre ({disk_usage.free_gb:.1f}GB) abaixo do minimo ({self.min_free_space_gb}GB)")

        if not need_cleanup:
            self.logger.debug("Limpeza nao necessaria")
            return 0

        # Obtem arquivos a deletar
        files_to_delete = self.get_files_to_delete(target_bytes)

        if not files_to_delete:
            self.logger.warning("Nenhum arquivo para deletar")
            return 0

        self.logger.info(f"Deletando {len(files_to_delete)} arquivos para liberar espaco...")

        for recording in files_to_delete:
            try:
                recording.path.unlink()
                files_deleted += 1
                bytes_freed += recording.size_bytes

                # Remove do cache
                cache_key = str(recording.path)
                if cache_key in self._files_cache:
                    del self._files_cache[cache_key]

                self.logger.debug(f"Arquivo deletado: {recording.path.name}")

                # Remove diretorio vazio
                try:
                    parent = recording.path.parent
                    if parent != self.recordings_dir and not any(parent.iterdir()):
                        parent.rmdir()
                except Exception:
                    pass

            except Exception as e:
                self.logger.error(f"Erro ao deletar {recording.path}: {e}")

        freed_mb = bytes_freed / (1024 ** 2)
        self.logger.info(f"Limpeza concluida: {files_deleted} arquivos, {freed_mb:.1f}MB liberados")

        return files_deleted

    async def start_monitoring(self) -> None:
        """Inicia monitoramento de disco."""
        if self._running:
            self.logger.warning("Monitoramento ja esta ativo")
            return

        self._running = True
        self.logger.info("Iniciando monitoramento de disco...")

        # Inicia observer de arquivos
        self._start_file_observer()

        # Inicia task de verificacao periodica
        async def monitor_loop():
            while self._running:
                try:
                    await self._check_disk_space()
                except Exception as e:
                    self.logger.error(f"Erro no monitoramento: {e}")

                await asyncio.sleep(self.check_interval)

        self._monitor_task = asyncio.create_task(monitor_loop())

    async def stop_monitoring(self) -> None:
        """Para monitoramento de disco."""
        self._running = False

        # Para observer
        self._stop_file_observer()

        # Para task
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        self.logger.info("Monitoramento de disco parado")

    def _start_file_observer(self) -> None:
        """Inicia observer de arquivos."""
        if not Observer:
            self.logger.warning("Watchdog nao disponivel, observer desabilitado")
            return

        try:
            self._observer = Observer()
            handler = RecordingWatcher(self._on_file_change)
            self._observer.schedule(handler, str(self.recordings_dir), recursive=True)
            self._observer.start()
            self.logger.debug("File observer iniciado")
        except Exception as e:
            self.logger.error(f"Erro ao iniciar file observer: {e}")

    def _stop_file_observer(self) -> None:
        """Para observer de arquivos."""
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join(timeout=5)
            except Exception as e:
                self.logger.debug(f"Erro ao parar observer: {e}")
            self._observer = None

    def _on_file_change(self, event: str, path: Path) -> None:
        """
        Callback para mudancas em arquivos.

        Args:
            event: Tipo de evento (created, deleted, modified)
            path: Caminho do arquivo
        """
        if path.suffix.lower() not in self.VIDEO_EXTENSIONS:
            return

        self.logger.debug(f"Arquivo {event}: {path.name}")

        if event == "deleted" and str(path) in self._files_cache:
            del self._files_cache[str(path)]

    async def _check_disk_space(self) -> None:
        """Verifica espaco em disco e executa acoes necessarias."""
        disk_usage = self.get_disk_usage()

        # Verifica nivel de alerta
        if disk_usage.percent_used >= self.critical_threshold:
            self._notify_alert(AlertLevel.CRITICAL, disk_usage)
            # Executa limpeza automatica
            await self.cleanup()

        elif disk_usage.percent_used >= self.warning_threshold:
            self._notify_alert(AlertLevel.WARNING, disk_usage)

        else:
            self._notify_alert(AlertLevel.OK, disk_usage)

        # Log de status
        recordings_size, file_count = self.get_recordings_size()
        recordings_gb = recordings_size / (1024 ** 3)

        self.logger.debug(
            f"Disco: {disk_usage.used_gb:.1f}/{disk_usage.total_gb:.1f}GB "
            f"({disk_usage.percent_used:.1f}%), "
            f"Gravacoes: {recordings_gb:.1f}GB ({file_count} arquivos)"
        )

    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status do gerenciador de disco.

        Returns:
            Dicionario com status
        """
        disk_usage = self.get_disk_usage()
        recordings_size, file_count = self.get_recordings_size()

        return {
            "disk": {
                "total_gb": round(disk_usage.total_gb, 2),
                "used_gb": round(disk_usage.used_gb, 2),
                "free_gb": round(disk_usage.free_gb, 2),
                "percent_used": round(disk_usage.percent_used, 1),
                "alert_level": disk_usage.alert_level.value
            },
            "recordings": {
                "directory": str(self.recordings_dir),
                "size_gb": round(recordings_size / (1024 ** 3), 2),
                "file_count": file_count,
                "max_storage_gb": self.max_storage_gb
            },
            "policy": self.policy.value,
            "monitoring_active": self._running,
            "thresholds": {
                "warning": self.warning_threshold,
                "critical": self.critical_threshold,
                "min_free_gb": self.min_free_space_gb
            }
        }

    async def get_storage_report(self) -> Dict[str, Any]:
        """
        Gera relatorio detalhado de armazenamento.

        Returns:
            Relatorio detalhado
        """
        recordings = self.scan_recordings()

        # Agrupa por camera
        by_camera: Dict[str, List[RecordingFile]] = {}
        for rec in recordings:
            camera_id = rec.camera_id or "unknown"
            if camera_id not in by_camera:
                by_camera[camera_id] = []
            by_camera[camera_id].append(rec)

        # Agrupa por data
        by_date: Dict[str, int] = {}
        for rec in recordings:
            date_key = rec.created_at.strftime("%Y-%m-%d")
            by_date[date_key] = by_date.get(date_key, 0) + rec.size_bytes

        # Estatisticas
        total_size = sum(r.size_bytes for r in recordings)
        avg_size = total_size / len(recordings) if recordings else 0

        oldest = min(recordings, key=lambda r: r.created_at) if recordings else None
        newest = max(recordings, key=lambda r: r.created_at) if recordings else None

        return {
            "total_files": len(recordings),
            "total_size_gb": round(total_size / (1024 ** 3), 2),
            "average_file_size_mb": round(avg_size / (1024 ** 2), 2),
            "oldest_file": {
                "path": str(oldest.path) if oldest else None,
                "created_at": oldest.created_at.isoformat() if oldest else None,
                "age_days": round(oldest.age_days, 1) if oldest else None
            },
            "newest_file": {
                "path": str(newest.path) if newest else None,
                "created_at": newest.created_at.isoformat() if newest else None
            },
            "by_camera": {
                camera: {
                    "files": len(files),
                    "size_gb": round(sum(f.size_bytes for f in files) / (1024 ** 3), 2)
                }
                for camera, files in by_camera.items()
            },
            "by_date": {
                date: round(size / (1024 ** 3), 2)
                for date, size in sorted(by_date.items())[-30:]  # Ultimos 30 dias
            }
        }
