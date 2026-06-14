# -*- coding: utf-8 -*-
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.persistence import Base


class AfterActionReview(Base):
    __tablename__ = "after_action_reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_id = Column(String, nullable=False)
    operation_name = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    participants = Column(JSON, default=[])
    timeline = Column(JSON, default=[])
    objectives = Column(JSON, default=[])
    outcomes = Column(JSON, default=[])
    lessons_learned = Column(JSON, default=[])
    recommendations = Column(JSON, default=[])
    performance_metrics = Column(JSON, default={})
    status = Column(String, nullable=False, default="IN_PROGRESS")
    classification = Column(String, nullable=False, default="CONFIDENTIAL")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(String, nullable=False)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
