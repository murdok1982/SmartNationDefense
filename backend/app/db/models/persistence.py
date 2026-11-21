# -*- coding: utf-8 -*-
import datetime
import hashlib
import json
import logging
import uuid
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Integer, Boolean, Text, func
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)
Base = declarative_base()


def _get_cipher():
    try:
        from app.core.crypto import AESCipher
        return AESCipher.from_hex(settings.AES_KEY)
    except Exception:
        return None


class EncryptedField:
    def __init__(self, column_name: str):
        self.column_name = column_name
        self._cache = {}
        self._weak_refs = {}

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        encrypted = getattr(obj, self.column_name, None)
        if not encrypted:
            return {}
        cache_key = self._make_cache_key(obj, encrypted)
        if cache_key not in self._cache:
            cipher = _get_cipher()
            if cipher is None:
                raise ValueError("AES_KEY no configurado: EncryptedField refuse a devolver datos en texto plano — fail-closed")
            try:
                self._cache[cache_key] = cipher.decrypt(encrypted)
            except Exception:
                raise
        return self._cache[cache_key]

    def __set__(self, obj, value: dict):
        if not isinstance(value, dict):
            raise ValueError("EncryptedField solo acepta dict/JSON")
        cipher = _get_cipher()
        if cipher is None:
            raise ValueError("AES_KEY no configurado: EncryptedField refuse a escribir — fail-closed")
        encrypted = cipher.encrypt(value)
        setattr(obj, self.column_name, encrypted)
        cache_key = self._make_cache_key(obj, getattr(obj, self.column_name, ""))
        if cache_key in self._cache:
            del self._cache[cache_key]

    @staticmethod
    def _make_cache_key(obj, encrypted_value: str) -> int:
        return hash((id(obj), hashlib.sha256(encrypted_value.encode()).hexdigest()[:16]))


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True)
    kind = Column(String, nullable=False)
    current_status = Column(String)
    last_heartbeat = Column(DateTime(timezone=True), default=func.now())
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    classification_level = Column(String, nullable=False)
    metadata_json = Column(JSON, name="metadata", default={})


class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    ts = Column(DateTime(timezone=True), nullable=False)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    classification_level = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    payload = Column(JSON, nullable=False)
    signature = Column(JSON, nullable=False)


class Telemetry(Base):
    __tablename__ = "telemetry"

    ts = Column(DateTime(timezone=True), primary_key=True)
    asset_id = Column(String, primary_key=True)
    parameter = Column(String, primary_key=True)
    value = Column(Float, nullable=False)
    unit = Column(String)
    metadata_json = Column(JSON, name="metadata", default={})


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, ForeignKey("events.event_id"))
    rule_id = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    description = Column(String)
    is_anomaly = Column(Boolean, default=False)
    human_validated = Column(Boolean, default=False)
    validated_by = Column(String)
    _sensitive = Column("sensitive", Text, nullable=True)

    sensitive = EncryptedField("_sensitive")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime(timezone=True), default=func.now())
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    context = Column(JSON, default={})
    prev_hash = Column(String(64), nullable=False, default="0" * 64)
    row_hash = Column(String(64), nullable=False, default="")


class IntelligenceProduct(Base):
    __tablename__ = "intelligence_products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    classification_level = Column(String, nullable=False, default="CONFIDENTIAL")
    source_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_by = Column(String, nullable=False, default="SYSTEM")


class PriorityIntelligenceRequirement(Base):
    __tablename__ = "priority_intelligence_requirements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False)
    collection_methods = Column(JSON, default=[])
    due_date = Column(DateTime(timezone=True), nullable=True)
    classification_level = Column(String, nullable=False, default="CONFIDENTIAL")
    created_by = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())


class SensorSource(Base):
    __tablename__ = "sensor_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sensor_id = Column(String, nullable=False, unique=True)
    sensor_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")
    classification_level = Column(String, nullable=False, default="CONFIDENTIAL")
    first_seen = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_seen = Column(DateTime(timezone=True), nullable=False, default=func.now())
    metadata_json = Column(JSON, name="metadata", default={})


class IntelFusionRecord(Base):
    __tablename__ = "intel_fusion_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, nullable=True)
    fusion_score = Column(Float, nullable=False)
    source_count = Column(Integer, nullable=False, default=0)
    correlated_count = Column(Integer, nullable=False, default=0)
    assessment = Column(JSON, default={})
    classification_level = Column(String, nullable=False, default="CONFIDENTIAL")
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())


class ORBATUnit(Base):
    __tablename__ = "orbat_units"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String, ForeignKey("orbat_units.id"), nullable=True)
    name = Column(String, nullable=False)
    unit_type = Column(String, nullable=False)
    classification_level = Column(String, nullable=False, default="CONFIDENTIAL")
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    commander_id = Column(String, nullable=True)
    status = Column(String, default="ACTIVE")
    metadata_json = Column(JSON, name="metadata", default={})


class Mission(Base):
    __tablename__ = "missions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    mission_type = Column(String, nullable=False)
    status = Column(String, default="PLANNED")
    classification_level = Column(String, nullable=False, default="SECRET")
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    commander_id = Column(String, nullable=True)
    orbat_unit_id = Column(String, ForeignKey("orbat_units.id"), nullable=True)
    _sensitive = Column("sensitive", Text, nullable=True)
    sensitive = EncryptedField("_sensitive")
    created_at = Column(DateTime(timezone=True), default=func.now())
    created_by = Column(String, nullable=False)


class BlueForceTracking(Base):
    __tablename__ = "blue_force_tracking"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    unit_id = Column(String, ForeignKey("orbat_units.id"), nullable=False)
    asset_id = Column(String, ForeignKey("assets.id"), nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    status = Column(String, default="ACTIVE")
    timestamp = Column(DateTime(timezone=True), default=func.now())


class ElectronicWarfareEvent(Base):
    __tablename__ = "ew_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String, nullable=False)
    frequency_mhz = Column(Float, nullable=True)
    bandwidth_mhz = Column(Float, nullable=True)
    signal_strength = Column(Float, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    classification_level = Column(String, nullable=False, default="SECRET")
    _analysis = Column("analysis", Text, nullable=True)
    analysis = EncryptedField("_analysis")
    timestamp = Column(DateTime(timezone=True), default=func.now())


class CyberIncident(Base):
    __tablename__ = "cyber_incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    source_ip = Column(String, nullable=True)
    target_system = Column(String, nullable=False)
    kill_chain_stage = Column(String, nullable=True)
    classification_level = Column(String, nullable=False, default="SECRET")
    _forensics = Column("forensics", Text, nullable=True)
    forensics = EncryptedField("_forensics")
    status = Column(String, default="OPEN")
    created_at = Column(DateTime(timezone=True), default=func.now())
    created_by = Column(String, nullable=False)


class LogisticsSupply(Base):
    __tablename__ = "logistics_supplies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_type = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    location_id = Column(String, ForeignKey("orbat_units.id"), nullable=True)
    min_threshold = Column(Float, nullable=True)
    classification_level = Column(String, nullable=False, default="CONFIDENTIAL")
    last_updated = Column(DateTime(timezone=True), default=func.now())


class EventStore(Base):
    __tablename__ = "event_store"

    event_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    aggregate_id = Column(String, nullable=False, index=True)
    aggregate_type = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    metadata_json = Column("metadata", JSON, default={})
    occurred_at = Column(DateTime(timezone=True), default=func.now())
    actor = Column(String, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="operator")
    classification_level = Column(String, nullable=False, default="RESTRICTED")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sensor_type = Column(String, nullable=False)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    status = Column(String, default="ACTIVE")
    metadata_json = Column(JSON, name="metadata", default={})


class IntelReport(Base):
    __tablename__ = "intel_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    classification = Column(String, nullable=False, default="CONFIDENTIAL")
    source = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    author_id = Column(String, ForeignKey("users.id"), nullable=True)
