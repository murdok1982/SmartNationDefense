# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from app.services.messaging.service import messaging_service

router = APIRouter()


class SendMessageRequest(BaseModel):
    recipient_ids: List[str]
    message_type: str
    priority: str
    content: str
    subject: Optional[str] = None
    classification: str = "CONFIDENTIAL"
    thread_id: Optional[str] = None
    parent_id: Optional[str] = None
    ttl_minutes: Optional[int] = None


class BroadcastRequest(BaseModel):
    recipient_ids: List[str]
    message_type: str
    priority: str
    content: str
    subject: Optional[str] = None
    classification: str = "CONFIDENTIAL"


@router.post("/send")
async def send_message(request: SendMessageRequest, sender_id: str = "OPERATOR"):
    try:
        return await messaging_service.send_message(
            sender_id=sender_id,
            recipient_ids=request.recipient_ids,
            message_type=request.message_type,
            priority=request.priority,
            content=request.content,
            subject=request.subject,
            classification=request.classification,
            thread_id=request.thread_id,
            parent_id=request.parent_id,
            ttl_minutes=request.ttl_minutes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/inbox")
async def get_inbox(
    user_id: str = "OPERATOR",
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    message_type: Optional[str] = None,
    priority: Optional[str] = None,
):
    return await messaging_service.get_inbox(
        user_id=user_id,
        limit=limit,
        offset=offset,
        message_type=message_type,
        priority=priority,
    )


@router.post("/broadcast")
async def broadcast_message(request: BroadcastRequest, sender_id: str = "OPERATOR"):
    try:
        return await messaging_service.broadcast(
            sender_id=sender_id,
            recipient_ids=request.recipient_ids,
            message_type=request.message_type,
            priority=request.priority,
            content=request.content,
            subject=request.subject,
            classification=request.classification,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_history(
    user_id: str = "OPERATOR",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return await messaging_service.get_history(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.put("/{message_id}/ack")
async def acknowledge_message(message_id: str, user_id: str = "OPERATOR"):
    try:
        return await messaging_service.acknowledge(message_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{message_id}")
async def delete_message(message_id: str):
    success = await messaging_service.delete_message(message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    return {"status": "deleted", "message_id": message_id}
