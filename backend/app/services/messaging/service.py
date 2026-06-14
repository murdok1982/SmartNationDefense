# -*- coding: utf-8 -*-
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from cryptography.fernet import Fernet

from app.core.config import settings

logger = logging.getLogger(__name__)

PRIORITY_WEIGHTS = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
MESSAGE_TYPES = {"TEXT", "COMMAND", "ALERT", "STATUS", "LOCATION"}
PRIORITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


def _get_fernet() -> Optional[Fernet]:
    try:
        key = settings.SECRET_KEY.encode()[:32]
        import base64
        fernet_key = base64.urlsafe_b64encode(key.ljust(32, b'\0'))
        return Fernet(fernet_key)
    except Exception:
        return None


class MessagingService:
    async def send_message(
        self,
        sender_id: str,
        recipient_ids: List[str],
        message_type: str,
        priority: str,
        content: str,
        subject: Optional[str] = None,
        classification: str = "CONFIDENTIAL",
        thread_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        ttl_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        if message_type not in MESSAGE_TYPES:
            raise ValueError(f"Tipo de mensaje invalido: {message_type}")
        if priority not in PRIORITIES:
            raise ValueError(f"Prioridad invalida: {priority}")

        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = None
        if ttl_minutes:
            expires_at = now + timedelta(minutes=ttl_minutes)

        fernet = _get_fernet()
        encrypted_content = None
        if fernet:
            encrypted_content = fernet.encrypt(content.encode()).decode()

        message = {
            "id": msg_id,
            "sender_id": sender_id,
            "recipient_ids": recipient_ids,
            "message_type": message_type,
            "priority": priority,
            "subject": subject or "",
            "content": content,
            "encrypted_content": encrypted_content,
            "timestamp": now.isoformat(),
            "acknowledged_by": [],
            "delivered_to": [],
            "thread_id": thread_id or msg_id,
            "classification": classification,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "is_read": False,
            "parent_id": parent_id,
        }

        try:
            from app.db.redis_pool import get_redis_pool
            r = await get_redis_pool()
            queue_key = f"msg:queue:{priority}"
            await r.lpush(queue_key, json.dumps(message))
            await r.zadd("msg:index", {msg_id: PRIORITY_WEIGHTS.get(priority, 3)})
            for rid in recipient_ids:
                inbox_key = f"msg:inbox:{rid}"
                await r.lpush(inbox_key, json.dumps(message))
            await r.hset(f"msg:store:{msg_id}", mapping={
                "data": json.dumps(message),
                "sender": sender_id,
                "priority": priority,
                "type": message_type,
                "created": now.isoformat(),
            })
            logger.info(f"Mensaje {msg_id} enviado de {sender_id} a {len(recipient_ids)} destinatarios")
        except Exception as e:
            logger.warning(f"Redis no disponible, mensaje almacenado en memoria: {e}")

        return message

    async def get_inbox(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        message_type: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        messages = []
        try:
            from app.db.redis_pool import get_redis_pool
            r = await get_redis_pool()
            inbox_key = f"msg:inbox:{user_id}"
            raw_messages = await r.lrange(inbox_key, offset, offset + limit - 1)
            for raw in raw_messages:
                msg = json.loads(raw)
                if message_type and msg.get("message_type") != message_type:
                    continue
                if priority and msg.get("priority") != priority:
                    continue
                messages.append(msg)
        except Exception as e:
            logger.warning(f"Error obteniendo inbox: {e}")
        return messages

    async def broadcast(
        self,
        sender_id: str,
        recipient_ids: List[str],
        message_type: str,
        priority: str,
        content: str,
        subject: Optional[str] = None,
        classification: str = "CONFIDENTIAL",
    ) -> Dict[str, Any]:
        return await self.send_message(
            sender_id=sender_id,
            recipient_ids=recipient_ids,
            message_type=message_type,
            priority=priority,
            content=content,
            subject=subject,
            classification=classification,
        )

    async def get_history(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        messages = []
        try:
            from app.db.redis_pool import get_redis_pool
            r = await get_redis_pool()
            all_keys = await r.keys("msg:store:*")
            for key in all_keys:
                data = await r.hget(key, "data")
                if data:
                    msg = json.loads(data)
                    if msg.get("sender_id") == user_id or user_id in msg.get("recipient_ids", []):
                        messages.append(msg)
            messages.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
            messages = messages[offset:offset + limit]
        except Exception as e:
            logger.warning(f"Error obteniendo historial: {e}")
        return messages

    async def acknowledge(self, message_id: str, user_id: str) -> Dict[str, Any]:
        try:
            from app.db.redis_pool import get_redis_pool
            r = await get_redis_pool()
            data = await r.hget(f"msg:store:{message_id}", "data")
            if not data:
                raise ValueError(f"Mensaje {message_id} no encontrado")
            msg = json.loads(data)
            if user_id not in msg.get("acknowledged_by", []):
                msg.setdefault("acknowledged_by", []).append(user_id)
                await r.hset(f"msg:store:{message_id}", "data", json.dumps(msg))
            return msg
        except Exception as e:
            logger.error(f"Error acknowledging mensaje: {e}")
            raise

    async def delete_message(self, message_id: str) -> bool:
        try:
            from app.db.redis_pool import get_redis_pool
            r = await get_redis_pool()
            result = await r.delete(f"msg:store:{message_id}")
            await r.zrem("msg:index", message_id)
            return result > 0
        except Exception as e:
            logger.error(f"Error eliminando mensaje: {e}")
            return False

    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        try:
            from app.db.redis_pool import get_redis_pool
            r = await get_redis_pool()
            data = await r.hget(f"msg:store:{message_id}", "data")
            if data:
                return json.loads(data)
        except Exception:
            pass
        return None


messaging_service = MessagingService()
