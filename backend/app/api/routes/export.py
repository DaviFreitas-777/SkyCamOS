"""
Rotas de Exportacao do SkyCamOS.

Endpoints para exportar gravacoes com preview e selecao de periodo.
"""

import logging
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.services.export_service import export_service, EXPORT_FORMATS

logger = logging.getLogger(__name__)

router = APIRouter()


# ==========================================
# Schemas
# ==========================================

class ExportRequest(BaseModel):
    """Schema para solicitar exportacao."""
    camera_id: int
    start_time: datetime
    end_time: datetime
    format: str = Field(default="mp4", pattern="^(mp4|mkv|avi|webm)$")
    add_watermark: bool = False
    watermark_text: Optional[str] = None


class PreviewRequest(BaseModel):
    """Schema para solicitar preview."""
    camera_id: int
    start_time: datetime
    end_time: datetime


class ExportResponse(BaseModel):
    """Schema de resposta de exportacao."""
    success: bool
    camera_id: int
    start_time: str
    end_time: str
    format: str
    filename: str
    filepath: str
    file_size_bytes: int
    file_size_mb: float
    md5_hash: str
    watermark: bool
    created_at: str


class PreviewResponse(BaseModel):
    """Schema de resposta de preview."""
    camera_id: int
    start_time: str
    end_time: str
    duration_seconds: float
    segment_count: int
    total_size_bytes: int
    total_size_mb: float
    segments: List[str]
    thumbnail: Optional[str]
    available_formats: List[str]


class ExportListItem(BaseModel):
    """Item da lista de exportacoes."""
    filename: str
    filepath: str
    size_bytes: int
    size_mb: float
    created_at: str


# ==========================================
# Endpoints
# ==========================================

@router.get(
    "/formats",
    summary="Formatos disponiveis",
    description="Lista formatos de exportacao suportados.",
)
async def list_formats(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Lista formatos de exportacao disponiveis."""
    return {
        "formats": [
            {
                "id": key,
                "extension": fmt.extension,
                "description": f"Video {key.upper()}"
            }
            for key, fmt in EXPORT_FORMATS.items()
        ]
    }


@router.post(
    "/preview",
    response_model=PreviewResponse,
    summary="Preview de exportacao",
    description="Gera preview de um periodo para verificar antes de exportar.",
)
async def generate_preview(
    data: PreviewRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PreviewResponse:
    """
    Gera preview de exportacao.

    Permite ao usuario verificar se o periodo esta correto
    antes de iniciar a exportacao.
    """
    # Valida periodo
    if data.end_time <= data.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data final deve ser maior que data inicial",
        )

    # Limite de 24 horas por exportacao
    duration = (data.end_time - data.start_time).total_seconds()
    if duration > 86400:  # 24 horas
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Periodo maximo de 24 horas por exportacao",
        )

    preview = await export_service.generate_preview(
        camera_id=data.camera_id,
        start_time=data.start_time,
        end_time=data.end_time,
    )

    if not preview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma gravacao encontrada no periodo especificado",
        )

    return PreviewResponse(**preview)


@router.post(
    "/",
    response_model=ExportResponse,
    summary="Exportar gravacao",
    description="Exporta gravacoes de um periodo em formato especificado.",
)
async def export_recording(
    data: ExportRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ExportResponse:
    """
    Exporta gravacoes de um periodo.

    Concatena segmentos e converte para o formato especificado.
    Opcionalmente adiciona watermark e calcula hash de integridade.
    """
    # Valida periodo
    if data.end_time <= data.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data final deve ser maior que data inicial",
        )

    # Limite de 24 horas
    duration = (data.end_time - data.start_time).total_seconds()
    if duration > 86400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Periodo maximo de 24 horas por exportacao",
        )

    # Valida formato
    if data.format not in EXPORT_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato invalido. Use: {', '.join(EXPORT_FORMATS.keys())}",
        )

    result = await export_service.export_video(
        camera_id=data.camera_id,
        start_time=data.start_time,
        end_time=data.end_time,
        format=data.format,
        add_watermark=data.add_watermark,
        watermark_text=data.watermark_text,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao exportar gravacao. Verifique se ha gravacoes no periodo.",
        )

    return ExportResponse(**result)


@router.get(
    "/",
    response_model=List[ExportListItem],
    summary="Listar exportacoes",
    description="Lista arquivos exportados disponiveis para download.",
)
async def list_exports(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[ExportListItem]:
    """Lista arquivos exportados."""
    exports = await export_service.list_exports()
    return [ExportListItem(**e) for e in exports]


@router.get(
    "/download/{filename}",
    summary="Download de exportacao",
    description="Faz download de um arquivo exportado.",
)
async def download_export(
    filename: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FileResponse:
    """Faz download de um arquivo exportado."""
    file_path = await export_service.get_export_file(filename)

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo nao encontrado",
        )

    # Determina media type baseado na extensao
    media_types = {
        ".mp4": "video/mp4",
        ".mkv": "video/x-matroska",
        ".avi": "video/x-msvideo",
        ".webm": "video/webm",
    }
    media_type = media_types.get(file_path.suffix, "application/octet-stream")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )


@router.delete(
    "/{filename}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover exportacao",
    description="Remove um arquivo exportado.",
)
async def delete_export(
    filename: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """Remove um arquivo exportado."""
    success = await export_service.delete_export(filename)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo nao encontrado",
        )


@router.post(
    "/cleanup",
    summary="Limpar exportacoes antigas",
    description="Remove arquivos de exportacao mais antigos que o especificado.",
)
async def cleanup_exports(
    max_age_hours: int = Query(default=24, ge=1, le=168),
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Remove exportacoes antigas."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem limpar exportacoes",
        )

    count = await export_service.cleanup_old_exports(max_age_hours)

    return {
        "message": f"Removidos {count} arquivos",
        "max_age_hours": max_age_hours,
    }
