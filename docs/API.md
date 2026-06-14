# SESIS-FEDERATION API

Base URL: `/api/v1`

## Endpoints

| Prefix | Module | Description |
|--------|--------|-------------|
| /health | core | Health check |
| /auth | core | Authentication + MFA |
| /c2 | sesis-c2 | Command & Control |
| /satellite | aegis | Satellite IMINT |
| /osint | atalaya | Multi-INT OSINT |
| /intel | global-intel | Intelligence analysis |
| /agents | spymanager | Agent management |
| /tactical/opord | tactical | OPORD generation |
| /tactical/wargaming | tactical | COA simulation |
| /tactical/fires | tactical | Joint fires coordination |
| /tactical/bda | tactical | Battle damage assessment |
| /tactical/psyops | tactical | Psychological operations |
| /agents/sensors | sensors | IoT sensor mesh |
| /messaging | messaging | Tactical messaging QoS (6 endpoints) |
| /fusion | fusion | JDL Level 2 fusion engine (4 endpoints) |
| /terrain | terrain | Advanced terrain analysis (5 endpoints) |
| /logistics | logistics | Military logistics (7 endpoints) |
| /aar | aar | After Action Review (6 endpoints) |
| /reports | reports | Automated NATO reporting (6 endpoints) |
| /prediction | prediction | ML threat prediction (4 endpoints) |
| /map | mapping | Tactical multi-layer map (9 endpoints) |
| /voice | voice | Voice command integration (3 endpoints) |
| /planning | planning | NATO OPORD enhanced planning (11 endpoints) |

---

## Authentication

All endpoints require JWT Bearer token except `/health`.

```bash
# Obtain token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# Use token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/health
```

---

## Tactical Messaging (`/api/v1/messaging`)

Military-grade messaging with QoS priorities: FLASH > IMMEDIATE > PRIORITY > ROUTINE.

### POST /messaging/send

Send a tactical message with priority and classification.

```bash
curl -X POST http://localhost:8000/api/v1/messaging/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_ids": ["UNIT-ALPHA", "UNIT-BRAVO"],
    "message_type": "ORDER",
    "priority": "FLASH",
    "content": "Mover a posicion defensiva en grid 42N23E",
    "subject": "Orden de movimiento inmediato",
    "classification": "SECRET",
    "thread_id": "THREAD-001",
    "ttl_minutes": 30
  }'
```

**Response:**
```json
{
  "message_id": "MSG-a1b2c3d4",
  "status": "sent",
  "recipients": ["UNIT-ALPHA", "UNIT-BRAVO"],
  "priority": "FLASH",
  "delivered_at": "2026-06-14T10:30:00Z"
}
```

### GET /messaging/inbox

Retrieve inbox messages with optional filters.

```bash
curl -X GET "http://localhost:8000/api/v1/messaging/inbox?user_id=OPERATOR&limit=50&priority=FLASH" \
  -H "Authorization: Bearer $TOKEN"
```

### POST /messaging/broadcast

Broadcast message to multiple recipients simultaneously.

```bash
curl -X POST http://localhost:8000/api/v1/messaging/broadcast \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_ids": ["ALL-UNITS"],
    "message_type": "ALERT",
    "priority": "IMMEDIATE",
    "content": "Alerta de contacto hostil en sector 7",
    "classification": "CONFIDENTIAL"
  }'
```

### GET /messaging/history

```bash
curl -X GET "http://localhost:8000/api/v1/messaging/history?user_id=OPERATOR&limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

### PUT /messaging/{message_id}/ack

```bash
curl -X PUT http://localhost:8000/api/v1/messaging/MSG-a1b2c3d4/ack?user_id=OPERATOR \
  -H "Authorization: Bearer $TOKEN"
```

### DELETE /messaging/{message_id}

```bash
curl -X DELETE http://localhost:8000/api/v1/messaging/MSG-a1b2c3d4 \
  -H "Authorization: Bearer $TOKEN"
```

---

## JDL Level 2 Fusion (`/api/v1/fusion`)

Situation assessment engine following the JDL (Joint Directors of Laboratories) Level 2 model.

### POST /fusion/assess-threats

Classify entities and assess overall threat level from multi-source events.

```bash
curl -X POST http://localhost:8000/api/v1/fusion/assess-threats \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"source": "SAT", "type": "detection", "lat": 42.5, "lon": 2.3, "entity_type": "armor", "confidence": 0.9},
      {"source": "SENSOR", "type": "acoustic", "lat": 42.51, "lon": 2.31, "entity_type": "vehicle", "confidence": 0.7}
    ]
  }'
```

**Response:**
```json
{
  "threat_level": "HIGH",
  "hostile_units": [
    {"id": "H-001", "unit_type": "armor", "location": {"lat": 42.5, "lon": 2.3}, "strength": "COMPANY", "threat_level": "HIGH", "capability": "ANTI-ARMOR", "intention": "ADVANCE"}
  ],
  "friendly_units": [
    {"id": "F-001", "unit_type": "infantry", "location": {"lat": 42.4, "lon": 2.2}, "status": "ACTIVE", "strength": "PLATOON"}
  ],
  "neutral_entities": [],
  "threat_zones": [
    {"zone_id": "TZ-001", "center": {"lat": 42.5, "lon": 2.3}, "radius_km": 5.0, "threat_level": "HIGH", "zone_type": "ARMOR_CONCENTRATION", "description": "Concentracion blindada hostil"}
  ],
  "recommended_actions": [
    {"action_type": "REINFORCE", "priority": "HIGH", "description": "Reforzar sector con unidades antitanque"}
  ],
  "assessment_id": "ASM-20260614-001"
}
```

### POST /fusion/relationships

Identify relationships between entities (command, support, subordination).

```bash
curl -X POST http://localhost:8000/api/v1/fusion/relationships \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {"id": "E-001", "entity_type": "armor", "lat": 42.5, "lon": 2.3, "source": "SAT"},
      {"id": "E-002", "entity_type": "armor", "lat": 42.51, "lon": 2.31, "source": "SAT"},
      {"id": "E-003", "entity_type": "command", "lat": 42.52, "lon": 2.32, "source": "SIGINT"}
    ]
  }'
```

### POST /fusion/intentions

Predict enemy intentions based on unit positions and behavior.

```bash
curl -X POST http://localhost:8000/api/v1/fusion/intentions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enemy_units": [
      {"unit_id": "H-001", "unit_type": "armor", "lat": 42.5, "lon": 2.3, "speed": 25.0, "heading": 180.0}
    ]
  }'
```

### POST /fusion/ctp

Generate consolidated Common Tactical Picture.

```bash
curl -X POST http://localhost:8000/api/v1/fusion/ctp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"source": "SAT", "type": "detection", "lat": 42.5, "lon": 2.3},
      {"source": "OSINT", "type": "report", "lat": 42.6, "lon": 2.4}
    ]
  }'
```

---

## Terrain Analysis (`/api/v1/terrain`)

Advanced terrain analysis including Line of Sight, route planning, and obstacle detection.

### POST /terrain/line-of-sight

Calculate line of sight between observer and target with elevation profile.

```bash
curl -X POST http://localhost:8000/api/v1/terrain/line-of-sight \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "observer": {"lat": 42.5, "lon": 2.3},
    "target": {"lat": 42.6, "lon": 2.4},
    "observer_height_m": 10.0,
    "target_height_m": 2.0
  }'
```

**Response:**
```json
{
  "has_los": true,
  "distance_km": 13.2,
  "elevation_profile": [
    {"distance_km": 0, "elevation_m": 450},
    {"distance_km": 3.3, "elevation_m": 520},
    {"distance_km": 6.6, "elevation_m": 480},
    {"distance_km": 13.2, "elevation_m": 410}
  ],
  "max_terrain_height_m": 520,
  "clearance_m": 45.0
}
```

### POST /terrain/route-analysis

Plan optimal route by vehicle type avoiding obstacles.

```bash
curl -X POST http://localhost:8000/api/v1/terrain/route-analysis \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start": {"lat": 42.4, "lon": 2.2},
    "end": {"lat": 42.6, "lon": 2.4},
    "vehicle_type": "ARMORED",
    "avoid_obstacles": true
  }'
```

### POST /terrain/terrain-analysis

Comprehensive terrain analysis for an area of operations.

```bash
curl -X POST http://localhost:8000/api/v1/terrain/terrain-analysis \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"center_lat": 42.5, "center_lon": 2.3, "radius_km": 10.0}'
```

### GET /terrain/elevation

Get elevation at specific coordinates.

```bash
curl -X GET "http://localhost:8000/api/v1/terrain/elevation?lat=42.5&lon=2.3" \
  -H "Authorization: Bearer $TOKEN"
```

### POST /terrain/obstacle-detection

Detect natural and man-made obstacles in area.

```bash
curl -X POST http://localhost:8000/api/v1/terrain/obstacle-detection \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"center_lat": 42.5, "center_lon": 2.3, "radius_km": 5.0}'
```

---

## Military Logistics (`/api/v1/logistics`)

Supply management, personnel tracking, MEDEVAC 9-line, and equipment maintenance.

### GET /logistics/supplies

```bash
curl -X GET "http://localhost:8000/api/v1/logistics/supplies?supply_type=AMMUNITION&status=AVAILABLE" \
  -H "Authorization: Bearer $TOKEN"
```

### POST /logistics/request

Request supply delivery with priority.

```bash
curl -X POST http://localhost:8000/api/v1/logistics/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "supply_type": "AMMUNITION",
    "quantity": 500,
    "unit": "rounds",
    "delivery_location": {"lat": 42.5, "lon": 2.3},
    "priority": "HIGH",
    "justification": "Contacto hostil en sector 7",
    "requested_by": "UNIT-ALPHA"
  }'
```

### POST /logistics/delivery

Register supply delivery.

```bash
curl -X POST http://localhost:8000/api/v1/logistics/delivery \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ-001",
    "supply_type": "AMMUNITION",
    "quantity_delivered": 500,
    "delivered_by": "LOG-UNIT-1",
    "delivered_to": "UNIT-ALPHA",
    "location": {"lat": 42.5, "lon": 2.3}
  }'
```

### GET /logistics/status

```bash
curl -X GET http://localhost:8000/api/v1/logistics/status \
  -H "Authorization: Bearer $TOKEN"
```

### POST /logistics/medevac

Create MEDEVAC 9-line request.

```bash
curl -X POST http://localhost:8000/api/v1/logistics/medevac \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "casualty_id": "CAS-001",
    "casualty_name": "Sgt. Garcia",
    "location": {"lat": 42.5, "lon": 2.3},
    "urgency": "URGENT",
    "type": "MEDEVAC",
    "equipment": ["BACKPACK", "HOIST"],
    "security": "N",
    "marked": true,
    "casualty_count": 2,
    "special_equipment": "Extraction board",
    "casualty_status": "WIA",
    "terrain_description": "Zona arbolada, claro para heli",
    "radio_freq": "121.5"
  }'
```

### GET /logistics/personnel

```bash
curl -X GET "http://localhost:8000/api/v1/logistics/personnel?unit_id=UNIT-ALPHA&status=ACTIVE" \
  -H "Authorization: Bearer $TOKEN"
```

### POST /logistics/maintenance

Report equipment maintenance issue.

```bash
curl -X POST http://localhost:8000/api/v1/logistics/maintenance \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "VEH-001",
    "equipment_type": "ARMORED_CAR",
    "issue_type": "ENGINE",
    "severity": "HIGH",
    "description": "Motor sobrecalentamiento tras 200km",
    "reported_by": "MECH-01",
    "priority": "HIGH",
    "parts_needed": ["RADIATOR", "COOLANT"]
  }'
```

---

## After Action Review (`/api/v1/aar`)

Structured AAR system with timeline, lessons learned, and operation replay.

### POST /aar/create

```bash
curl -X POST http://localhost:8000/api/v1/aar/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_id": "OP-ALPHA",
    "operation_name": "Operacion Amanecer",
    "start_time": "2026-06-14T06:00:00Z",
    "end_time": "2026-06-14T18:00:00Z",
    "participants": ["UNIT-ALPHA", "UNIT-BRAVO", "CAS-TEAM-1"],
    "objectives": [{"id": "OBJ-1", "description": "Asegurar puente", "status": "ACHIEVED"}],
    "classification": "CONFIDENTIAL",
    "created_by": "C2-SYSTEM"
  }'
```

### GET /aar/{aar_id}

```bash
curl -X GET http://localhost:8000/api/v1/aar/AAR-20260614-001 \
  -H "Authorization: Bearer $TOKEN"
```

### POST /aar/{aar_id}/timeline

Add event to AAR timeline.

```bash
curl -X POST http://localhost:8000/api/v1/aar/AAR-20260614-001/timeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-06-14T08:30:00Z",
    "event_type": "CONTACT",
    "description": "Contacto con fuerzas hostiles en punto 42.5N 2.3E",
    "actor": "UNIT-ALPHA",
    "location": {"lat": 42.5, "lon": 2.3},
    "outcome": "Hostiles neutralizados",
    "significance": "CRITICAL"
  }'
```

### POST /aar/{aar_id}/lessons

Add lesson learned.

```bash
curl -X POST http://localhost:8000/api/v1/aar/AAR-20260614-001/lessons \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "TACTICAL",
    "observation": "Comunicaciones degradadas en zona montanosa",
    "discussion": "Las frecuencias VHF no alcanzaban cobertura en valles",
    "recommendation": "Incluir retransmisiones de comunicaciones en plan",
    "priority": "HIGH",
    "sustains": false,
    "improves": true
  }'
```

### GET /aar/{aar_id}/replay

Get operation replay data.

```bash
curl -X GET http://localhost:8000/api/v1/aar/AAR-20260614-001/replay \
  -H "Authorization: Bearer $TOKEN"
```

### POST /aar/{aar_id}/finalize

Finalize AAR with outcomes and metrics.

```bash
curl -X POST http://localhost:8000/api/v1/aar/AAR-20260614-001/finalize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "outcomes": [{"objective": "Asegurar puente", "result": "ACHIEVED"}],
    "recommendations": [{"text": "Mejorar cobertura de comunicaciones", "priority": "HIGH"}],
    "performance_metrics": {"mission_success_rate": 0.95, "casualties": 2, "duration_hours": 12}
  }'
```

---

## Automated Reporting (`/api/v1/reports`)

Generate NATO-standard military reports: SITREP, SPOTREP, SALUTE, MEDEVAC.

### POST /reports/sitrep

Generate Situation Report (SITREP).

```bash
curl -X POST http://localhost:8000/api/v1/reports/sitrep \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "classification": "SECRET",
    "from_unit": "BN-1",
    "to_unit": "BDE-HQ",
    "reference": "OP-ALPHA",
    "enemy_forces": "2 companias mecanizadas a 15km al NE, equipadas con T-72",
    "friendly_forces": "Batallon de infanteria reforzado en posiciones defensivas",
    "weather_current": "Despejado, visibilidad 10km, viento 15km/h NW",
    "operations_ongoing": ["Patrullaje sector 7", "Reconocimiento puente"],
    "supply_status": "Clase V al 60%, Clase III al 80%",
    "personnel_strength": "95% efectivo",
    "casualties": "2 WIA, 0 KIA"
  }'
```

### POST /reports/spotrep

Generate Spot Report (SPOTREP) — SALUTE format.

```bash
curl -X POST http://localhost:8000/api/v1/reports/spotrep \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "classification": "CONFIDENTIAL",
    "size": "Company (-)",
    "activity": "Movimiento hacia el sur por ruta principal",
    "location": {"lat": 42.5, "lon": 2.3},
    "unit_identified": "2/5 MRB",
    "time_observed": "2026-06-14T10:30:00Z",
    "equipment": "6x T-72, 4x BMP-2, 2x 2S19",
    "narrative": "Columna blindada en movimiento hacia el sur",
    "assessment": "Probable ataque en las proximas 6 horas"
  }'
```

### POST /reports/salute

Generate SALUTE report (Size, Activity, Location, Unit, Time, Equipment).

```bash
curl -X POST http://localhost:8000/api/v1/reports/salute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "classification": "CONFIDENTIAL",
    "size": "Platoon",
    "activity": "Estableciendo posiciones defensivas",
    "location": {"lat": 42.55, "lon": 2.35},
    "unit": "3/7 IBCT",
    "time": "2026-06-14T11:00:00Z",
    "equipment": "3x BMP-2, 12x infantry, ATGM launcher",
    "assessment": "Bloqueo de ruta principal",
    "source_reliability": "A",
    "info_credibility": "1"
  }'
```

### POST /reports/medevac

Generate MEDEVAC report.

```bash
curl -X POST http://localhost:8000/api/v1/reports/medevac \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "urgency": "URGENT",
    "pickup_location": {"lat": 42.5, "lon": 2.3},
    "radio_freq": "121.5",
    "casualty_count": 3,
    "urgent_count": 1,
    "priority_count": 1,
    "routine_count": 1,
    "security": "N",
    "evac_type": "MEDEVAC",
    "equipment": ["BACKPACK", "HOIST", "EXTRACTION"],
    "requesting_unit": "UNIT-ALPHA",
    "commander_name": "Cpt. Martinez"
  }'
```

### GET /reports/{report_id}

```bash
curl -X GET http://localhost:8000/api/v1/reports/RPT-20260614-001 \
  -H "Authorization: Bearer $TOKEN"
```

### GET /reports

List reports with optional type filter.

```bash
curl -X GET "http://localhost:8000/api/v1/reports?report_type=SITREP&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Threat Prediction (`/api/v1/prediction`)

ML-powered threat prediction, anomaly detection, and early warning.

### POST /prediction/predict-movement

Predict future position of a hostile unit.

```bash
curl -X POST http://localhost:8000/api/v1/prediction/predict-movement \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "HOSTILE-001",
    "lat": 42.5,
    "lon": 2.3,
    "speed": 30.0,
    "heading": 180.0,
    "threat_level": 75.0,
    "time_horizon_min": 120
  }'
```

**Response:**
```json
{
  "unit_id": "HOSTILE-001",
  "current_position": {"lat": 42.5, "lon": 2.3},
  "predicted_positions": [
    {"time_min": 30, "lat": 42.475, "lon": 2.3, "confidence": 0.92},
    {"time_min": 60, "lat": 42.45, "lon": 2.3, "confidence": 0.85},
    {"time_min": 120, "lat": 42.4, "lon": 2.3, "confidence": 0.72}
  ],
  "predicted_intention": "ADVANCE_SOUTH",
  "threat_at_horizon": "HIGH"
}
```

### POST /prediction/detect-anomalies

Detect anomalies in event streams.

```bash
curl -X POST http://localhost:8000/api/v1/prediction/detect-anomalies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"timestamp": "2026-06-14T10:00:00Z", "type": "movement", "location": {"lat": 42.5, "lon": 2.3}},
      {"timestamp": "2026-06-14T10:05:00Z", "type": "communication", "location": {"lat": 42.51, "lon": 2.31}},
      {"timestamp": "2026-06-14T10:10:00Z", "type": "movement", "location": {"lat": 42.8, "lon": 2.8}}
    ]
  }'
```

### POST /prediction/pattern-of-life

Analyze pattern of life for a specific unit.

```bash
curl -X POST http://localhost:8000/api/v1/prediction/pattern-of-life \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"unit_id": "HOSTILE-001"}'
```

### POST /prediction/early-warning

Generate early warning based on friendly locations and threat radius.

```bash
curl -X POST http://localhost:8000/api/v1/prediction/early-warning \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "friendly_locations": [
      {"lat": 42.4, "lon": 2.2, "unit_id": "UNIT-ALPHA"},
      {"lat": 42.45, "lon": 2.25, "unit_id": "UNIT-BRAVO"}
    ],
    "threat_radius_km": 50.0
  }'
```

---

## Tactical Map (`/api/v1/map`)

Multi-layer tactical map with overlays, unit tracking, engagement zones, and communication ranges.

### GET /map/layers

```bash
curl -X GET http://localhost:8000/api/v1/map/layers \
  -H "Authorization: Bearer $TOKEN"
```

### POST /map/overlay

Add a GeoJSON overlay to the tactical map.

```bash
curl -X POST http://localhost:8000/api/v1/map/overlay \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Zona de Amenaza Alpha",
    "layer_type": "THREAT",
    "geojson": {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[42.5,2.3],[42.6,2.3],[42.6,2.4],[42.5,2.4],[42.5,2.3]]]
      }
    },
    "style": {"color": "#ff0000", "fillOpacity": 0.3},
    "visible": true
  }'
```

### GET /map/overlay

```bash
curl -X GET "http://localhost:8000/api/v1/map/overlay?layer_type=THREAT" \
  -H "Authorization: Bearer $TOKEN"
```

### DELETE /map/overlay/{overlay_id}

```bash
curl -X DELETE http://localhost:8000/api/v1/map/overlay/OVL-001 \
  -H "Authorization: Bearer $TOKEN"
```

### POST /map/track

Update unit position on tactical map.

```bash
curl -X POST http://localhost:8000/api/v1/map/track \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "unit_id": "UNIT-ALPHA",
    "lat": 42.45,
    "lon": 2.25,
    "altitude": 450.0,
    "heading": 90.0,
    "speed": 15.0,
    "status": "ACTIVE"
  }'
```

### GET /map/unit/{unit_id}/history

```bash
curl -X GET "http://localhost:8000/api/v1/map/unit/UNIT-ALPHA/history?limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

### POST /map/engagement-zone

Calculate weapon engagement zone.

```bash
curl -X POST http://localhost:8000/api/v1/map/engagement-zone \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"unit_location": {"lat": 42.5, "lon": 2.3}, "weapon_system": "ARTILLERY_155MM"}'
```

### POST /map/comm-range

Calculate communication system range.

```bash
curl -X POST http://localhost:8000/api/v1/map/comm-range \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transmitter_location": {"lat": 42.5, "lon": 2.3},
    "comm_system": "VHF",
    "terrain_factor": 0.7
  }'
```

### GET /map/state

Get consolidated map state with all layers and units.

```bash
curl -X GET http://localhost:8000/api/v1/map/state \
  -H "Authorization: Bearer $TOKEN"
```

---

## Voice Commands (`/api/v1/voice`)

Voice and text command processing with military NLU.

### POST /voice/command

Process a voice or text command.

```bash
curl -X POST http://localhost:8000/api/v1/voice/command \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text_command": "Generar SITREP para batallon 1",
    "language": "es",
    "user_id": "OPERATOR-01"
  }'
```

**Response:**
```json
{
  "command_id": "VCMD-001",
  "intent": "GENERATE_REPORT",
  "parameters": {"report_type": "SITREP", "unit": "BN-1"},
  "executed": true,
  "result": {"report_id": "RPT-20260614-001"},
  "confidence": 0.94
}
```

### GET /voice/status

```bash
curl -X GET http://localhost:8000/api/v1/voice/status \
  -H "Authorization: Bearer $TOKEN"
```

### POST /voice/train

Train voice model with samples.

```bash
curl -X POST http://localhost:8000/api/v1/voice/train \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "es",
    "samples": [
      {"text": "Generar SITREP", "intent": "GENERATE_REPORT"},
      {"text": "Marcar contacto hostil", "intent": "MARK_HOSTILE"}
    ]
  }'
```

---

## NATO OPORD Planning (`/api/v1/planning`)

Enhanced NATO 5-paragraph OPORD with annexes, approval workflow, FRAGORD generation, COA comparison, and risk assessment.

### POST /planning/create

Create a new OPORD with 5 NATO paragraphs.

```bash
curl -X POST http://localhost:8000/api/v1/planning/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_name": "Operacion Trueno",
    "classification": "SECRET",
    "paragraph_1_situation": {
      "enemy": "2 companias mecanizadas enemigas a 15km al NE",
      "friendly": "Batallon de infanteria reforzado en posiciones defensivas",
      "attachments": "Seccion antitanque, equipo EOD"
    },
    "paragraph_2_mission": {
      "task": "Asegurar puente en coordenadas 42.5N 2.3E NLT 1800Z",
      "purpose": "Permitir cruce de fuerzas propias para ofensiva"
    },
    "paragraph_3_execution": {
      "commander_intent": "Capturar puente intacto para uso propio",
      "concept": "Ataque de pinzas con apoyo de fuegos",
      "tasks_to_subordinate_units": {
        "UNIT-ALPHA": "Ataque principal por norte",
        "UNIT-BRAVO": "Ataque secundario por sur"
      }
    },
    "paragraph_4_sustainment": {
      "supply": "Clase V (munición) prioridad al ataque principal",
      "medical": "Punto de recogida de heridos en grid 42.4N 2.2E"
    },
    "paragraph_5_command_signal": {
      "command_post": "CP tactico en BRAVO",
      "successor": "BG XO asume comando si BG Commander incapacitado",
      "signal": "Freq principal 30.0 MHz, alterna 31.5 MHz"
    },
    "created_by": "BG COMMANDER"
  }'
```

### GET /planning/{opord_id}

```bash
curl -X GET http://localhost:8000/api/v1/planning/OPORD-20260614-001 \
  -H "Authorization: Bearer $TOKEN"
```

### PUT /planning/{opord_id}/paragraph/{paragraph}

Update a specific paragraph.

```bash
curl -X PUT http://localhost:8000/api/v1/planning/OPORD-20260614-001/paragraph/3 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": {"concept": "Ataque frontal con apoyo de fuegos pesado"}}'
```

### POST /planning/{opord_id}/annex

Add an annex to the OPORD.

```bash
curl -X POST http://localhost:8000/api/v1/planning/OPORD-20260614-001/annex \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "annex_type": "LOGISTICS",
    "title": "Anexo Logistico A",
    "content": {"supply_plan": "Clase V desde BPA", "transport": "3x camiones 5T"},
    "classification": "SECRET"
  }'
```

### POST /planning/{opord_id}/approve

Approve OPORD (commander action).

```bash
curl -X POST "http://localhost:8000/api/v1/planning/OPORD-20260614-001/approve?approver=BG_COMMANDER" \
  -H "Authorization: Bearer $TOKEN"
```

### POST /planning/{opord_id}/distribute

Distribute OPORD to units.

```bash
curl -X POST http://localhost:8000/api/v1/planning/OPORD-20260614-001/distribute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '["UNIT-ALPHA", "UNIT-BRAVO", "CAS-TEAM-1", "ARTY-BN"]'
```

### POST /planning/{opord_id}/fragord

Generate a Fragmentary Order (FRAGORD) for changes.

```bash
curl -X POST http://localhost:8000/api/v1/planning/OPORD-20260614-001/fragord \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "changes": {
      "paragraph_3_execution": {"concept": "Cambio: ataque principal ahora por sur"},
      "reason": "Inteligencia indica defensas mas fuertes al norte"
    }
  }'
```

### POST /planning/coa-compare

Compare multiple Courses of Action.

```bash
curl -X POST http://localhost:8000/api/v1/planning/coa-compare \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "coa_list": [
      {"name": "COA-Alpha", "attack": "frontal", "forces": ["infantry", "armor"], "risk": "HIGH"},
      {"name": "COA-Bravo", "attack": "flanking", "forces": ["infantry", "helicopter"], "risk": "MEDIUM"},
      {"name": "COA-Charlie", "attack": "infiltration", "forces": ["special_forces"], "risk": "LOW"}
    ]
  }'
```

### GET /planning/{opord_id}/risk-assessment

```bash
curl -X GET http://localhost:8000/api/v1/planning/OPORD-20260614-001/risk-assessment \
  -H "Authorization: Bearer $TOKEN"
```

### GET /planning/{opord_id}/sync-matrix

```bash
curl -X GET http://localhost:8000/api/v1/planning/OPORD-20260614-001/sync-matrix \
  -H "Authorization: Bearer $TOKEN"
```

### GET /planning/{opord_id}/validate

Validate OPORD completeness.

```bash
curl -X GET http://localhost:8000/api/v1/planning/OPORD-20260614-001/validate \
  -H "Authorization: Bearer $TOKEN"
```

---

## Error Responses

All endpoints return standard HTTP error codes:

| Code | Description |
|------|-------------|
| 400 | Bad Request — invalid parameters |
| 401 | Unauthorized — missing or invalid token |
| 403 | Forbidden — insufficient classification level |
| 404 | Not Found — resource does not exist |
| 429 | Too Many Requests — rate limit exceeded |
| 500 | Internal Server Error |

Error response format:
```json
{
  "detail": "Mensaje de error descriptivo"
}
```

