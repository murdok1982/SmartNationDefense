import json
import logging
import math
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from app.services.fusion.jdl_fusion import (
    jdl_fusion_engine,
    Location,
    SituationAssessment,
)

logger = logging.getLogger(__name__)

_REDIS_AVAILABLE = False
try:
    import redis.asyncio as aioredis
    _REDIS_AVAILABLE = True
except ImportError:
    pass


class SensorEvent(BaseModel):
    source_type: str
    source_id: str
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    raw_data: dict = Field(default_factory=dict)


class COPSnapshot(BaseModel):
    units: List[dict] = Field(default_factory=list)
    threats: List[dict] = Field(default_factory=list)
    tracks: List[dict] = Field(default_factory=list)
    sensors: List[dict] = Field(default_factory=list)
    last_update: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CorrelatedTrack(BaseModel):
    track_id: str
    events: List[SensorEvent] = Field(default_factory=list)
    centroid_lat: float = 0.0
    centroid_lon: float = 0.0
    first_seen: str = ""
    last_seen: str = ""
    classification: str = "UNKNOWN"
    confidence: float = 0.0


class FusionEngine:
    _instance: Optional["FusionEngine"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        spatial_window_km: float = 1.0,
        temporal_window_min: int = 5,
        redis_url: Optional[str] = None,
    ):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.spatial_window_km = spatial_window_km
        self.temporal_window_min = temporal_window_min
        self.redis_url = redis_url
        self._events: List[SensorEvent] = []
        self._tracks: Dict[str, CorrelatedTrack] = {}
        self._redis = None

    async def _ensure_redis(self):
        if self._redis is None and self.redis_url and _REDIS_AVAILABLE:
            try:
                self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
            except Exception as e:
                logger.warning("Redis no disponible: %s", e)

    async def ingest(self, event: SensorEvent) -> CorrelatedTrack:
        self._events.append(event)
        await self._ensure_redis()
        if self._redis:
            try:
                key = f"fusion:events:{event.source_id}"
                val = event.model_dump_json()
                await self._redis.rpush(key, val)
                await self._redis.expire(key, 86400)
            except Exception as e:
                logger.warning("Redis persist error: %s", e)
        matches = self._correlate_single(event)
        if matches:
            track = matches[0]
            track.events.append(event)
            track.last_seen = event.ts
            self._update_centroid(track)
            self._tracks[track.track_id] = track
        else:
            track = CorrelatedTrack(
                track_id=f"T{uuid.uuid4().hex[:8].upper()}",
                events=[event],
                centroid_lat=event.lat,
                centroid_lon=event.lon,
                first_seen=event.ts,
                last_seen=event.ts,
                classification="PENDING",
                confidence=event.confidence,
            )
            self._tracks[track.track_id] = track
        return track

    def _correlate_single(self, event: SensorEvent) -> List[CorrelatedTrack]:
        event_ts = datetime.fromisoformat(event.ts)
        matches: List[CorrelatedTrack] = []
        for track in self._tracks.values():
            last_ts = datetime.fromisoformat(track.last_seen)
            dt_min = abs((event_ts - last_ts).total_seconds()) / 60.0
            if dt_min > self.temporal_window_min:
                continue
            d_km = self._haversine(event.lat, event.lon, track.centroid_lat, track.centroid_lon)
            if d_km <= self.spatial_window_km:
                matches.append(track)
        return matches

    async def correlate_events(
        self, events: List[SensorEvent]
    ) -> List[CorrelatedTrack]:
        for ev in events:
            await self.ingest(ev)
        return list(self._tracks.values())

    def get_cop_snapshot(self) -> COPSnapshot:
        units = []
        threats = []
        tracks_data = []
        sensors_set: Dict[str, dict] = {}
        for track in self._tracks.values():
            tdict = track.model_dump()
            tracks_data.append(tdict)
            last = track.events[-1] if track.events else None
            if last:
                sensors_set[last.source_id] = {
                    "id": last.source_id,
                    "type": last.source_type,
                    "last_seen": last.ts,
                    "lat": last.lat,
                    "lon": last.lon,
                }
            threat_conf = track.confidence * 100
            if threat_conf >= 50:
                threats.append({
                    "track_id": track.track_id,
                    "type": track.classification,
                    "confidence": track.confidence,
                    "lat": track.centroid_lat,
                    "lon": track.centroid_lon,
                    "last_seen": track.last_seen,
                })
            else:
                units.append({
                    "track_id": track.track_id,
                    "type": track.classification,
                    "lat": track.centroid_lat,
                    "lon": track.centroid_lon,
                })
        return COPSnapshot(
            units=units,
            threats=threats,
            tracks=tracks_data,
            sensors=list(sensors_set.values()),
            last_update=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def _update_centroid(track: CorrelatedTrack) -> None:
        if not track.events:
            return
        avg_lat = sum(e.lat for e in track.events) / len(track.events)
        avg_lon = sum(e.lon for e in track.events) / len(track.events)
        track.centroid_lat = round(avg_lat, 6)
        track.centroid_lon = round(avg_lon, 6)


fusion_engine = FusionEngine()
