# -*- coding: utf-8 -*-
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.persistence import Base


class MilitaryReport(Base):
    __tablename__ = "military_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    classification = Column(String, nullable=False, default="CONFIDENTIAL")
    distribution_list = Column(JSON, default=[])
    digital_signature = Column(String, nullable=True)
    auto_generated = Column(Boolean, default=False)
    source_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(String, nullable=False)
    operation_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="DRAFT")
