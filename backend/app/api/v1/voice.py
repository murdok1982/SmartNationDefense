# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from pydantic import BaseModel

from app.services.voice.service import voice_command_service
from app.core.security import require_clearance

router = APIRouter()


class VoiceCommandRequest(BaseModel):
    audio_data: str = None
    text_command: str = None
    language: str = "es"
    user_id: str = "OPERATOR"


class VoiceTrainRequest(BaseModel):
    language: str = "es"
    samples: List[Dict[str, Any]] = []


@router.post("/command")
async def process_voice_command(
    request: VoiceCommandRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    if not request.audio_data and not request.text_command:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Se requiere audio_data o text_command")
    return await voice_command_service.process_command(
        audio_data=request.audio_data,
        text_command=request.text_command,
        language=request.language,
        user_id=request.user_id,
    )


@router.get("/status")
async def get_voice_status(principal: dict = Depends(require_clearance("RESTRICTED"))):
    return await voice_command_service.get_status()


@router.post("/train")
async def train_voice_model(
    request: VoiceTrainRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    return await voice_command_service.train_model(request.model_dump())
