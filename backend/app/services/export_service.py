"""
Servico de Exportacao do SkyCamOS.

Permite exportar gravacoes em diferentes formatos,
com selecao de periodo e preview.
"""

import asyncio
import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExportFormat:
    """Configuracao de formato de exportacao."""
    extension: str
    video_codec: str
    audio_codec: str
    container: str


# Formatos suportados
EXPORT_FORMATS = {
    "mp4": ExportFormat(".mp4", "copy", "aac", "mp4"),
    "mkv": ExportFormat(".mkv", "copy", "copy", "matroska"),
    "avi": ExportFormat(".avi", "libx264", "mp3", "avi"),
    "webm": ExportFormat(".webm", "libvpx-vp9", "libopus", "webm"),
}


class ExportService:
    """
    Servico para exportar gravacoes.

    Funcionalidades:
    - Buscar segmentos por periodo
    - Gerar preview de intervalo
    - Concatenar e exportar em diferentes formatos
    - Adicionar watermark (opcional)
    - Calcular hash de integridade
    """

    def __init__(self) -> None:
        """Inicializa o servico."""
        self._exports_dir = Path(settings.recordings_path) / "exports"
        self._exports_dir.mkdir(parents=True, exist_ok=True)
        self._ffmpeg_path = self._get_ffmpeg_path()

    def _get_ffmpeg_path(self) -> str:
        """Retorna o caminho do FFmpeg."""
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            return ffmpeg
        common_paths = [
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
            "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        return "ffmpeg"

    def find_segments(
        self,
        camera_id: int,
        start_time: datetime,
        end_time: datetime,
        base_path: Optional[Path] = None,
    ) -> List[Path]:
        """
        Encontra segmentos de gravacao em um periodo.

        Args:
            camera_id: ID da camera.
            start_time: Inicio do periodo.
            end_time: Fim do periodo.
            base_path: Caminho base (usa padrao se None).

        Returns:
            Lista de arquivos de gravacao no periodo.
        """
        if base_path is None:
            base_path = settings.recordings_dir

        camera_path = base_path / f"camera_{camera_id}"

        if not camera_path.exists():
            logger.warning(f"[Export] Diretorio nao existe: {camera_path}")
            return []

        segments = []

        # Busca arquivos MKV e MP4
        for ext in [".mkv", ".mp4"]:
            for file_path in camera_path.rglob(f"*{ext}"):
                # Extrai timestamp do nome do arquivo
                # Formato: cam{id}_{YYYYMMDD}_{HHMMSS}.mkv
                filename = file_path.stem
                try:
                    # Tenta extrair timestamp
                    parts = filename.split("_")
                    if len(parts) >= 3:
                        date_str = parts[-2]  # YYYYMMDD
                        time_str = parts[-1]  # HHMMSS

                        file_datetime = datetime.strptime(
                            f"{date_str}_{time_str}",
                            "%Y%m%d_%H%M%S"
                        )

                        # Verifica se esta no periodo
                        # Considera segmentos de 5 minutos
                        segment_end = file_datetime.replace(
                            minute=file_datetime.minute + 5
                        )

                        if file_datetime <= end_time and segment_end >= start_time:
                            segments.append(file_path)

                except (ValueError, IndexError) as e:
                    logger.debug(f"[Export] Ignorando arquivo: {filename} - {e}")
                    continue

        # Ordena por data
        segments.sort(key=lambda x: x.name)

        logger.info(f"[Export] Encontrados {len(segments)} segmentos para camera {camera_id}")
        return segments

    async def generate_preview(
        self,
        camera_id: int,
        start_time: datetime,
        end_time: datetime,
        base_path: Optional[Path] = None,
    ) -> Optional[dict]:
        """
        Gera informacoes de preview para um periodo.

        Args:
            camera_id: ID da camera.
            start_time: Inicio do periodo.
            end_time: Fim do periodo.
            base_path: Caminho base.

        Returns:
            Dict com informacoes do preview ou None.
        """
        segments = self.find_segments(camera_id, start_time, end_time, base_path)

        if not segments:
            return None

        total_size = sum(s.stat().st_size for s in segments)
        total_duration = (end_time - start_time).total_seconds()

        # Gera thumbnail do primeiro frame
        thumbnail_path = await self._generate_thumbnail(segments[0])

        return {
            "camera_id": camera_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": total_duration,
            "segment_count": len(segments),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "segments": [str(s) for s in segments],
            "thumbnail": str(thumbnail_path) if thumbnail_path else None,
            "available_formats": list(EXPORT_FORMATS.keys()),
        }

    async def _generate_thumbnail(self, video_path: Path) -> Optional[Path]:
        """Gera thumbnail de um video."""
        thumbnail_path = self._exports_dir / f"thumb_{video_path.stem}.jpg"

        if thumbnail_path.exists():
            return thumbnail_path

        cmd = [
            self._ffmpeg_path,
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(video_path),
            "-ss", "00:00:01",
            "-frames:v", "1",
            "-vf", "scale=320:-1",
            "-y",
            str(thumbnail_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0 and thumbnail_path.exists():
                return thumbnail_path
        except Exception as e:
            logger.error(f"[Export] Erro ao gerar thumbnail: {e}")

        return None

    async def export_video(
        self,
        camera_id: int,
        start_time: datetime,
        end_time: datetime,
        format: str = "mp4",
        add_watermark: bool = False,
        watermark_text: Optional[str] = None,
        base_path: Optional[Path] = None,
    ) -> Optional[dict]:
        """
        Exporta gravacoes de um periodo.

        Args:
            camera_id: ID da camera.
            start_time: Inicio do periodo.
            end_time: Fim do periodo.
            format: Formato de saida (mp4, mkv, avi, webm).
            add_watermark: Adicionar watermark.
            watermark_text: Texto do watermark.
            base_path: Caminho base.

        Returns:
            Dict com informacoes do arquivo exportado.
        """
        if format not in EXPORT_FORMATS:
            logger.error(f"[Export] Formato nao suportado: {format}")
            return None

        fmt = EXPORT_FORMATS[format]
        segments = self.find_segments(camera_id, start_time, end_time, base_path)

        if not segments:
            logger.warning(f"[Export] Nenhum segmento encontrado para exportacao")
            return None

        # Nome do arquivo de saida
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_filename = f"export_cam{camera_id}_{timestamp}{fmt.extension}"
        output_path = self._exports_dir / output_filename

        try:
            if len(segments) == 1:
                # Apenas um segmento - conversao simples
                success = await self._convert_single(
                    segments[0], output_path, fmt, add_watermark, watermark_text
                )
            else:
                # Multiplos segmentos - concatenar
                success = await self._concatenate_and_convert(
                    segments, output_path, fmt, start_time, end_time,
                    add_watermark, watermark_text
                )

            if not success or not output_path.exists():
                return None

            # Calcula hash de integridade
            file_hash = self._calculate_hash(output_path)

            return {
                "success": True,
                "camera_id": camera_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "format": format,
                "filename": output_filename,
                "filepath": str(output_path),
                "file_size_bytes": output_path.stat().st_size,
                "file_size_mb": round(output_path.stat().st_size / (1024 * 1024), 2),
                "md5_hash": file_hash,
                "watermark": add_watermark,
                "created_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"[Export] Erro na exportacao: {e}")
            return None

    async def _convert_single(
        self,
        input_path: Path,
        output_path: Path,
        fmt: ExportFormat,
        add_watermark: bool,
        watermark_text: Optional[str],
    ) -> bool:
        """Converte um unico arquivo."""
        cmd = [
            self._ffmpeg_path,
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(input_path),
        ]

        # Filtros de video (watermark)
        vf_filters = []
        if add_watermark:
            text = watermark_text or f"SkyCamOS - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            vf_filters.append(
                f"drawtext=text='{text}':fontsize=16:fontcolor=white:x=10:y=10"
            )

        if vf_filters:
            cmd.extend(["-vf", ",".join(vf_filters)])
            cmd.extend(["-c:v", "libx264"])  # Precisa re-encodar se tem filtro
        else:
            cmd.extend(["-c:v", fmt.video_codec])

        cmd.extend(["-c:a", fmt.audio_codec])
        cmd.extend(["-y", str(output_path)])

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=600)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"[Export] Erro na conversao: {e}")
            return False

    async def _concatenate_and_convert(
        self,
        segments: List[Path],
        output_path: Path,
        fmt: ExportFormat,
        start_time: datetime,
        end_time: datetime,
        add_watermark: bool,
        watermark_text: Optional[str],
    ) -> bool:
        """Concatena multiplos segmentos e converte."""
        # Cria arquivo de lista para concat
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for segment in segments:
                f.write(f"file '{segment}'\n")
            list_file = f.name

        try:
            cmd = [
                self._ffmpeg_path,
                "-hide_banner",
                "-loglevel", "error",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
            ]

            # Filtros de video
            vf_filters = []
            if add_watermark:
                text = watermark_text or f"SkyCamOS - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
                vf_filters.append(
                    f"drawtext=text='{text}':fontsize=16:fontcolor=white:x=10:y=10"
                )

            if vf_filters:
                cmd.extend(["-vf", ",".join(vf_filters)])
                cmd.extend(["-c:v", "libx264"])
            else:
                cmd.extend(["-c:v", fmt.video_codec])

            cmd.extend(["-c:a", fmt.audio_codec])
            cmd.extend(["-y", str(output_path)])

            result = subprocess.run(cmd, capture_output=True, timeout=1800)  # 30 min timeout
            return result.returncode == 0

        except Exception as e:
            logger.error(f"[Export] Erro na concatenacao: {e}")
            return False
        finally:
            # Remove arquivo temporario
            try:
                os.unlink(list_file)
            except Exception:
                pass

    def _calculate_hash(self, file_path: Path) -> str:
        """Calcula hash MD5 do arquivo."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def get_export_file(self, filename: str) -> Optional[Path]:
        """Obtem caminho de um arquivo exportado."""
        file_path = self._exports_dir / filename
        if file_path.exists():
            return file_path
        return None

    async def list_exports(self) -> List[dict]:
        """Lista arquivos exportados."""
        exports = []
        for ext in [".mp4", ".mkv", ".avi", ".webm"]:
            for file_path in self._exports_dir.glob(f"*{ext}"):
                exports.append({
                    "filename": file_path.name,
                    "filepath": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                    "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat(),
                })

        exports.sort(key=lambda x: x["created_at"], reverse=True)
        return exports

    async def delete_export(self, filename: str) -> bool:
        """Remove um arquivo exportado."""
        file_path = self._exports_dir / filename
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"[Export] Arquivo removido: {filename}")
                return True
            except Exception as e:
                logger.error(f"[Export] Erro ao remover arquivo: {e}")
        return False

    async def cleanup_old_exports(self, max_age_hours: int = 24) -> int:
        """Remove exportacoes antigas."""
        count = 0
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)

        for file_path in self._exports_dir.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                try:
                    file_path.unlink()
                    count += 1
                except Exception:
                    pass

        logger.info(f"[Export] Removidos {count} arquivos antigos")
        return count


# Instancia global
export_service = ExportService()
