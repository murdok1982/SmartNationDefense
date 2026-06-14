# -*- coding: utf-8 -*-
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.persistence import Base


class EnhancedOPORD(Base):
    __tablename__ = "enhanced_opords"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_name = Column(String, nullable=False)
    classification = Column(String, nullable=False, default="SECRET")
    paragraph_1_situation = Column(JSON, default={})
    paragraph_2_mission = Column(JSON, default={})
    paragraph_3_execution = Column(JSON, default={})
    paragraph_4_sustainment = Column(JSON, default={})
    paragraph_5_command_signal = Column(JSON, default={})
    annexes = Column(JSON, default=[])
    status = Column(String, nullable=False, default="DRAFT")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(String, nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, nullable=True)
    distributed_at = Column(DateTime(timezone=True), nullable=True)
    parent_opord_id = Column(String, nullable=True)
