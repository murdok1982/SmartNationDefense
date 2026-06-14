# -*- coding: utf-8 -*-
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.persistence import Base
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID


class TacticalMessage(Base):
    __tablename__ = "tactical_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String, nullable=False)
    recipient_ids = Column(JSON, nullable=False, default=[])
    message_type = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    encrypted_content = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    acknowledged_by = Column(JSON, default=[])
    delivered_to = Column(JSON, default=[])
    thread_id = Column(String, nullable=True)
    classification = Column(String, nullable=False, default="CONFIDENTIAL")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_read = Column(Boolean, default=False)
    parent_id = Column(String, nullable=True)
