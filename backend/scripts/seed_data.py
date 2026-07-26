# -*- coding: utf-8 -*-
"""
Seed de datos realistas para demo del sistema SESIS-FEDERATION.

Ejecutar desde backend/:
    python -m scripts.seed_data

Idempotente: si los usuarios ya existen, no duplica datos.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import engine, async_session

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

NOW = datetime.now(timezone.utc)

# ─── Modelos ──────────────────────────────────────────────────────────────────

from app.db.models.persistence import (
    User, Asset, Event, Alert, ORBATUnit,
    BlueForceTracking, Sensor, LogisticsSupply, IntelReport,
)
from app.db.models.messaging import TacticalMessage
from app.db.models.opord_enhanced import EnhancedOPORD

# ─── Datos de usuario ─────────────────────────────────────────────────────────

USERS = [
    {
        "username": "coronel.garcia",
        "email": "coronel.garcia@sesis.mil",
        "password": "Demo2024!",
        "role": "admin",
        "classification_level": "TOP_SECRET",
    },
    {
        "username": "capitan.lopez",
        "email": "capitan.lopez@sesis.mil",
        "password": "Demo2024!",
        "role": "operator",
        "classification_level": "SECRET",
    },
    {
        "username": "teniente.martin",
        "email": "teniente.martin@sesis.mil",
        "password": "Demo2024!",
        "role": "analyst",
        "classification_level": "RESTRICTED",
    },
]

# ─── Datos de reportes de inteligencia ───────────────────────────────────────

INTEL_REPORTS = [
    {
        "title": "Amenaza híbrida en el Sahel: desestabilización de fronteras meridionales",
        "body": (
            "FUENTE: CESID — Dirección de Inteligencia Exterior\n"
            "CLASIFICACIÓN: SECRET\n\n"
            "1. SITUACIÓN. Durante las últimas 72 horas se ha detectado un incremento\n"
            "significativo de actividad de grupos armados no estatales en la región\n"
            "comprendida entre los 21°N y 26°N, con incursiones tácticas a menos de\n"
            "40 km de la frontera sur de España (Sáhara Occidental).\n\n"
            "2. AMENAZA. Se ha identificado la presencia de células vinculadas a redes\n"
            "de tráfico ilícito que operan bajo cobertura de movimientos migratorios.\n"
            "Tres convoyes detectados por satélite PAZ el 15/07/2026 transportaban\n"
            "material de comunicaciones militarizado.\n\n"
            "3. IMPACTO. Riesgo de desbordamiento de capacidades de vigilancia en\n"
            "sectores no tripulados. Se recomienda refuerzo de patrullas del Servicio\n"
            "Marítimo de la Guardia Civil y activación de protocolo de vigilancia\n"
            "marítima cooperativa OTAN.\n\n"
            "4. CONCLUSIÓN. Nivel de alerta: ALTO. Próxima reevaluación: 72 h."
        ),
        "classification": "SECRET",
        "source": "CESID / DIR. INTELIGENCIA EXTERIOR",
        "author_username": "coronel.garcia",
    },
    {
        "title": "Ciberataque a infraestructura crítica portuaria en Algeciras",
        "body": (
            "FUENTE: Mando Conjunto del Ciberespacio (MCCE)\n"
            "CLASIFICACIÓN: TOP_SECRET\n\n"
            "1. SITUACIÓN. El sistema SCADA del puerto de Algeciras (36°07'N 5°27'W)\n"
            "sufrió un intento de intrusión el 18/07/2026 a las 03:14 UTC. El ataque\n"
            "fue detectado por el sensor de perímetro RAN-3L del sistema de protección\n"
            "crítica.\n\n"
            "2. ANÁLISIS. Traza de atribución parcial apunta a un APT con presunto\n"
            "patrocinio estatal. Se emplearon técnicas de living-off-the-land y\n"
            "túneles DNS para exfiltración de datos.\n\n"
            "3. AFECTACIÓN. Dos nodos del sistema de gestión de contenedores\n"
            "comprometidos. No se detectó impacto en sistemas de navegación.\n\n"
            "4. RECOMENDACIONES. Aislar segmento SCADA, rotar credenciales,\n"
            "notificar al CCN-CERT. Se ha elevado a nivel 3 (NIST SP 800-61)."
        ),
        "classification": "TOP_SECRET",
        "source": "MCCE / CCN-CERT",
        "author_username": "coronel.garcia",
    },
    {
        "title": "Tráfico ilícito en aguas jurisdiccionales del Estrecho de Gibraltar",
        "body": (
            "FUENTE: Armada Española — FLOTELLA DE ESCOLTAS\n"
            "CLASIFICACIÓN: SECRET\n\n"
            "1. SITUACIÓN. En los últimos 14 días se ha observado un incremento del\n"
            "37% en el tráfico marítimo no cooperativo en el área del Estrecho\n"
            "(36°00'N 5°30'W a 35°45'N 5°00'W).\n\n"
            "2. DETECCIÓN. El patrullero P-71 'Audaz' (P-71) interceptó el 20/07/2026\n"
            "una embarcación semirrígida con tres motores fuera-borda de 300 HP cada\n"
            "uno, sin matrícula ni identificación AIS, transportando 48 fardos de\n"
            "productos estupefacientes.\n\n"
            "3. EVALUACIÓN. Se estima que el 60% del tráfico ilícito en la región\n"
            "utiliza embarcaciones no monitorizadas. Se recomienda integración de\n"
            "datos AIS con radar costero LORA para correlación automática.\n\n"
            "4. ESTADO. Operación 'Paso del Estrecho 2026' activa. Refuerzo con\n"
            "unidad aérea no tripulada solicitado."
        ),
        "classification": "SECRET",
        "source": "ARMADA / FLOTELLA DE ESCOLTAS",
        "author_username": "capitan.lopez",
    },
    {
        "title": "Concentración de fuerzas irregulares en Sáhara Occidental",
        "body": (
            "FUENTE: SATÉLITE PAZ — IMINT\n"
            "CLASIFICACIÓN: TOP_SECRET\n\n"
            "1. SITUACIÓN. Imágenes satelitales del 22/07/2026 (órbita 3.452)\n"
            "revelan concentración de aproximadamente 200 efectivos y 40 vehículos\n"
            "tácticos en coordenadas 26°48'N 13°00'W, a 45 km al sureste de El Aaiún.\n\n"
            "2. COMPOSICIÓN. Se identificaron: 12 vehículos tipo pickup con ametralladoras\n"
            "pesadas, 8 lanzaderas múltiples artesanales, 20 camiones logísticos y una\n"
            "unidad de comunicaciones con antenas de media distancia.\n\n"
            "3. VALORACIÓN. La disposición defensiva del campamento sugiere\n"
            "preparación para acción ofensiva limitada o ejercicio de disuasión.\n\n"
            "4. RIESGO. Capacidad de interdicción de la ruta de suministro NC-2 entre\n"
            "Dajla y El Aaiún. Se recomienda seguimiento diario con INGENIO."
        ),
        "classification": "TOP_SECRET",
        "source": "SATÉLITE PAZ / INTA",
        "author_username": "coronel.garcia",
    },
    {
        "title": "Actividad de drones no identificados en perímetro de Melilla",
        "body": (
            "FUENTE: Mando de Artillería Antiaérea (MAAA)\n"
            "CLASIFICACIÓN: SECRET\n\n"
            "1. SITUACIÓN. Desde el 10/07/2026 se han registrado 14 incursiones de\n"
            "sistemas aéreos no tripulados no identificados en el entorno del\n"
            "perímetro fronterizo de Melilla.\n\n"
            "2. CARACTERÍSTICAS. Los drones presentan envergadura estimada de 2-3 m,\n"
            "altitud de vuelo entre 300 y 800 m AGL, velocidad crucero 60-80 km/h.\n"
            "Operan principalmente en horario nocturno (22:00-04:00 UTC).\n\n"
            "3. ORIGEN. Se ha triangulado el origen de las señales de control a una\n"
            "zona al este de Nador (Marruecos), a aproximadamente 12 km de la\n"
            "frontera. No ha sido posible identificar al operador.\n\n"
            "4. RECOMENDACIÓN. Despliegue de sistema contra-UAV RPS-42 en posición\n"
            "avanzada e integración con radar LORA para cobertura de baja cota."
        ),
        "classification": "SECRET",
        "source": "MAAA / EA",
        "author_username": "capitan.lopez",
    },
    {
        "title": "Monitoreo de comunicaciones navales rusas en Atlántico Nororiental",
        "body": (
            "FUENTE: Centro de Vigilancia Marítima (CIVIMAR)\n"
            "CLASIFICACIÓN: TOP_SECRET\n\n"
            "1. SITUACIÓN. El grupo naval ruso compuesto por la fragata 'Almirante\n"
            "Gorshkov' y el buque de aprovisionamiento 'Akademik Pashin' fue\n"
            "detectado el 12/07/2026 a 120 nm al oeste de Cabo Finisterre\n"
            "(42°30'N 12°45'W).\n\n"
            "2. ACTIVIDAD. Se interceptaron comunicaciones en banda X (9,8 GHz)\n"
            "compatibles con radar de seguimiento de superficie. El patrón de\n"
            "navegación sugiere reconocimiento de rutas de comunicaciones\n"
            "submarinas OTAN.\n\n"
            "3. ESTIMACIÓN. La fragata porta misiles hipersónicos Zircón. Se evalúa\n"
            "capacidad de ataque a objetivos en la fachada atlántica peninsular.\n\n"
            "4. ACCIÓN. Se mantiene escolta discreta con patrullera 'Infanta Elena'\n"
            "(P-76). Información compartida con STRIKFORNATO."
        ),
        "classification": "TOP_SECRET",
        "source": "CIVIMAR / ARMADA",
        "author_username": "coronel.garcia",
    },
    {
        "title": "Evaluación de capacidades de defensa aérea en Norte de África",
        "body": (
            "FUENTE: Centro de Inteligencia de las FAS (CIFAS)\n"
            "CLASIFICACIÓN: SECRET\n\n"
            "1. SITUACIÓN. Se ha completado la reevaluación semestral de las\n"
            "capacidades de defensa aérea en el arco norteafricano comprendido\n"
            "entre Túnez y Mauritania.\n\n"
            "2. HALLAZGOS. Se ha detectado la adquisición de sistemas de radar de\n"
            "vigilancia aérea de media altitud en tres países de la región. Dos de\n"
            "ellos cuentan con capacidad de seguimiento hasta 250 km.\n\n"
            "3. IMPLICACIONES. Aumento del riesgo para operaciones aéreas de\n"
            "vigilancia y reconocimiento de la OTAN en el flanco sur. La ventana\n"
            "de detección para aeronaves no furtivas se ha reducido en un 30%.\n\n"
            "4. RIESGO. Las rutas aéreas civiles que cruzan la región (A-16, A-20)\n"
            "no se ven afectadas. Sin embargo, se recomienda revisión de los\n"
            "perfiles de misión de las unidades del Ejército del Aire."
        ),
        "classification": "SECRET",
        "source": "CIFAS / EA",
        "author_username": "teniente.martin",
    },
]

# ─── Datos de alertas ───────────────────────────────────────────────────────

ALERTS = [
    {
        "rule_id": "CYBER-001",
        "severity": "CRITICAL",
        "description": "Intento de intrusión en red táctica ISIS — origen IP 185.xxx.xxx detectado por sensor de perímetro RAN-3L",
        "event_type": "CYBER",
        "lat": 36.1333, "lon": -5.4667,
    },
    {
        "rule_id": "PERIMETER-003",
        "severity": "WARNING",
        "description": "Embarcación no identificada (rumbo 045°, 12 nudos) penetrando ZEE sin emisión AIS en sector Estrecho",
        "event_type": "PERIMETER",
        "lat": 35.9500, "lon": -5.5000,
    },
    {
        "rule_id": "MOVEMENT-007",
        "severity": "WARNING",
        "description": "Columna de 12 vehículos tácticos detectada a 15 km de la frontera de Melilla — posible ejercicio no coordinado",
        "event_type": "MOVEMENT",
        "lat": 35.2667, "lon": -2.9500,
    },
    {
        "rule_id": "DRONE-002",
        "severity": "CRITICAL",
        "description": "Dron no identificado sobrevolando base aérea de Morón a 400 m AGL — no responde a protocolo IFF",
        "event_type": "DRONE",
        "lat": 37.1333, "lon": -5.6333,
    },
    {
        "rule_id": "COMMS-001",
        "severity": "INFO",
        "description": "Señal de radiofrecuencia no autorizada en banda UHF (380-400 MHz) detectada en sector Canarias",
        "event_type": "COMMUNICATION",
        "lat": 28.1167, "lon": -15.4333,
    },
    {
        "rule_id": "CYBER-004",
        "severity": "WARNING",
        "description": "Escaneo de puertos en sistemas C2 del Mando de Operaciones — 42 conexiones SYN desde 5 IPs diferentes",
        "event_type": "CYBER",
        "lat": 40.4167, "lon": -3.7167,
    },
    {
        "rule_id": "PERIMETER-008",
        "severity": "CRITICAL",
        "description": "Sobrevuelo no autorizado en espacio aéreo restringido LE-46 (Campo de maniobras de Chinchilla)",
        "event_type": "PERIMETER",
        "lat": 38.7833, "lon": -1.5167,
    },
    {
        "rule_id": "DRONE-005",
        "severity": "WARNING",
        "description": "Enjambre de 3 drones detectado a 8 nm al sur de La Isla de Alborán — trayectoria NNO",
        "event_type": "DRONE",
        "lat": 35.9000, "lon": -3.0333,
    },
]

# ─── Datos de unidades militares (ORBAT) ─────────────────────────────────────

ORBAT_UNITS = [
    {
        "name": "BRI X 'Extremadura'",
        "unit_type": "INFANTERIA",
        "lat": 38.8793, "lon": -6.9706,
        "status": "ACTIVE",
        "metadata_json": {"fuerza": 3500, "base": "Base General Menacho (Badajoz)", "escudo": "BRI X"},
    },
    {
        "name": "BRI VI 'Almogávares'",
        "unit_type": "INFANTERIA",
        "lat": 40.5017, "lon": -3.5364,
        "status": "DEPLOYED",
        "metadata_json": {"fuerza": 3200, "base": "Base Príncipe (Paracuellos del Jarama)", "escudo": "BRI VI"},
    },
    {
        "name": "MANDO DE OPERACIONES",
        "unit_type": "COMANDO",
        "lat": 40.4167, "lon": -3.7167,
        "status": "ACTIVE",
        "metadata_json": {"fuerza": 500, "base": "Estado Mayor de la Defensa (Madrid)", "nivel": "ESTRATÉGICO"},
    },
    {
        "name": "Flotilla de Escoltas",
        "unit_type": "NAVAL",
        "lat": 36.6167, "lon": -6.3500,
        "status": "DEPLOYED",
        "metadata_json": {"fuerza": 1500, "base": "Base Naval de Rota", "buques": 6},
    },
    {
        "name": "Grupo Aeronaval",
        "unit_type": "NAVAL_AEREO",
        "lat": 36.6167, "lon": -6.3500,
        "status": "STANDBY",
        "metadata_json": {"fuerza": 800, "base": "Base Naval de Rota", "aeronaves": 12},
    },
    {
        "name": "Ala 14",
        "unit_type": "AEREA_CAZA",
        "lat": 38.9500, "lon": -1.8500,
        "status": "ACTIVE",
        "metadata_json": {"fuerza": 900, "base": "Base Aérea de Albacete", "aeronaves": "EF-2000 Typhoon"},
    },
    {
        "name": "Ala 15",
        "unit_type": "AEREA_CAZA",
        "lat": 41.6667, "lon": -1.0333,
        "status": "ACTIVE",
        "metadata_json": {"fuerza": 850, "base": "Base Aérea de Zaragoza", "aeronaves": "F/A-18 Hornet"},
    },
    {
        "name": "Servicio Marítimo de la Guardia Civil",
        "unit_type": "GUARDIA_CIVIL",
        "lat": 37.6000, "lon": -0.9833,
        "status": "DEPLOYED",
        "metadata_json": {"fuerza": 400, "base": "Estación Naval de Cartagena", "embarcaciones": 15},
    },
    {
        "name": "Agrupación de Tráfico de la Guardia Civil",
        "unit_type": "GUARDIA_CIVIL",
        "lat": 40.4833, "lon": -3.6000,
        "status": "ACTIVE",
        "metadata_json": {"fuerza": 2500, "base": "Cuartel de la Guardia Civil (Madrid)", "competencia": "Tráfico interurbano"},
    },
]

# ─── Datos de activos/sensores ───────────────────────────────────────────────

ASSETS = [
    {
        "id": "radar-lora-estrecho-01",
        "kind": "RADAR",
        "current_status": "OPERATIONAL",
        "lat": 36.0000, "lon": -5.6000,
        "classification_level": "SECRET",
        "metadata_json": {"tipo": "LORA", "alcance_km": 200, "banda": "L", "cobertura": "Estrecho de Gibraltar"},
    },
    {
        "id": "radar-ran3l-melilla-01",
        "kind": "RADAR",
        "current_status": "OPERATIONAL",
        "lat": 35.3000, "lon": -2.9500,
        "classification_level": "SECRET",
        "metadata_json": {"tipo": "RAN-3L", "alcance_km": 150, "banda": "S", "cobertura": "Melilla y perímetro"},
    },
    {
        "id": "uav-rq11-moron-01",
        "kind": "UAV",
        "current_status": "DEPLOYED",
        "lat": 37.1333, "lon": -5.6333,
        "classification_level": "CONFIDENTIAL",
        "metadata_json": {"tipo": "RQ-11 Raven", "autonomia_h": 1.5, "techo_m": 4500, "base": "Morón"},
    },
    {
        "id": "uav-siva-canarias-01",
        "kind": "UAV",
        "current_status": "DEPLOYED",
        "lat": 28.1167, "lon": -15.4333,
        "classification_level": "SECRET",
        "metadata_json": {"tipo": "SIVA", "autonomia_h": 8, "techo_m": 6000, "base": "Gando (Canarias)"},
    },
    {
        "id": "sat-paz-01",
        "kind": "SATELLITE",
        "current_status": "OPERATIONAL",
        "lat": 0, "lon": 0,
        "classification_level": "TOP_SECRET",
        "metadata_json": {"tipo": "PAZ (Radar)", "orbita": "LEO 514 km", "resolucion_m": 1, "proposito": "IMINT"},
    },
    {
        "id": "sat-ingenio-01",
        "kind": "SATELLITE",
        "current_status": "OPERATIONAL",
        "lat": 0, "lon": 0,
        "classification_level": "TOP_SECRET",
        "metadata_json": {"tipo": "INGENIO (Óptico)", "orbita": "SSO 670 km", "resolucion_m": 2.5, "proposito": "IMINT"},
    },
    {
        "id": "buque-p71-audaz-01",
        "kind": "NAVAL",
        "current_status": "DEPLOYED",
        "lat": 36.0000, "lon": -5.2000,
        "classification_level": "CONFIDENTIAL",
        "metadata_json": {"tipo": "Buque de Acción Marítima BAM", "nombre": "P-71 Audaz", "base": "Rota"},
    },
    {
        "id": "buque-jci-01",
        "kind": "NAVAL",
        "current_status": "STANDBY",
        "lat": 36.6167, "lon": -6.3500,
        "classification_level": "SECRET",
        "metadata_json": {"tipo": "LHD", "nombre": "Juan Carlos I (L-61)", "base": "Rota", "capacidad_tropas": 1200},
    },
    {
        "id": "sensor-comms-canarias-01",
        "kind": "SIGINT",
        "current_status": "OPERATIONAL",
        "lat": 28.4500, "lon": -16.2833,
        "classification_level": "TOP_SECRET",
        "metadata_json": {"tipo": "Estación de escucha COMINT", "bandas": "VHF/UHF/SATCOM", "ubicacion": "Tenerife"},
    },
    {
        "id": "radar-lora-alboran-01",
        "kind": "RADAR",
        "current_status": "MAINTENANCE",
        "lat": 35.9500, "lon": -3.0333,
        "classification_level": "SECRET",
        "metadata_json": {"tipo": "LORA", "alcance_km": 180, "banda": "L", "ubicacion": "Isla de Alborán"},
    },
]

# ─── Datos de eventos de sensor ─────────────────────────────────────────────

SENSOR_EVENTS = [
    {
        "event_type": "RADAR_DETECTION",
        "asset_id": "radar-lora-estrecho-01",
        "lat": 35.9200, "lon": -5.4500,
        "classification_level": "SECRET",
        "confidence_score": 0.92,
        "payload": {"target_type": "vessel", "speed_kt": 18, "heading": 45, "length_m": 35, "rng_m": 18500},
        "signature": {"hash": "a1b2c3d4e5"},
    },
    {
        "event_type": "RADAR_DETECTION",
        "asset_id": "radar-lora-estrecho-01",
        "lat": 36.0500, "lon": -5.3000,
        "classification_level": "SECRET",
        "confidence_score": 0.88,
        "payload": {"target_type": "vessel", "speed_kt": 22, "heading": 270, "length_m": 90, "rng_m": 32000},
        "signature": {"hash": "f6g7h8i9j0"},
    },
    {
        "event_type": "COMMS_INTERCEPT",
        "asset_id": "sensor-comms-canarias-01",
        "lat": 28.3000, "lon": -15.8000,
        "classification_level": "TOP_SECRET",
        "confidence_score": 0.75,
        "payload": {"frequency_mhz": 156.8, "modulation": "FM", "language": "árabe", "duration_s": 45, "content_summary": "Coordenadas de encuentro transmitidas"},
        "signature": {"hash": "k1l2m3n4o5"},
    },
    {
        "event_type": "RADAR_DETECTION",
        "asset_id": "radar-ran3l-melilla-01",
        "lat": 35.2800, "lon": -2.9300,
        "classification_level": "SECRET",
        "confidence_score": 0.95,
        "payload": {"target_type": "airborne", "speed_kt": 85, "altitude_ft": 1200, "heading": 315, "rng_m": 8500},
        "signature": {"hash": "p6q7r8s9t0"},
    },
    {
        "event_type": "SATELLITE_IMAGE",
        "asset_id": "sat-paz-01",
        "lat": 26.8000, "lon": -13.0000,
        "classification_level": "TOP_SECRET",
        "confidence_score": 0.98,
        "payload": {"resolution_m": 1, "cloud_cover_pct": 0, "detections": 42, "vehicle_count": 40, "personnel_estimate": 200, "timestamp_utc": "2026-07-22T10:30:00Z"},
        "signature": {"hash": "u1v2w3x4y5"},
    },
    {
        "event_type": "RADAR_DETECTION",
        "asset_id": "radar-lora-estrecho-01",
        "lat": 36.0800, "lon": -5.1500,
        "classification_level": "SECRET",
        "confidence_score": 0.85,
        "payload": {"target_type": "vessel", "speed_kt": 5, "heading": 180, "length_m": 150, "rng_m": 42000, "ais_active": False},
        "signature": {"hash": "z1a2b3c4d5"},
    },
    {
        "event_type": "COMMS_INTERCEPT",
        "asset_id": "sensor-comms-canarias-01",
        "lat": 27.9000, "lon": -14.5000,
        "classification_level": "TOP_SECRET",
        "confidence_score": 0.65,
        "payload": {"frequency_mhz": 450.125, "modulation": "QPSK", "encryption": "DES", "duration_s": 120, "content_summary": "Tráfico cifrado no descifrado"},
        "signature": {"hash": "e6f7g8h9i0"},
    },
    {
        "event_type": "SATELLITE_IMAGE",
        "asset_id": "sat-ingenio-01",
        "lat": 35.9500, "lon": -4.5000,
        "classification_level": "TOP_SECRET",
        "confidence_score": 0.90,
        "payload": {"resolution_m": 2.5, "cloud_cover_pct": 10, "detections": 8, "feature": "campamento estacional", "area_m2": 5000, "timestamp_utc": "2026-07-20T11:00:00Z"},
        "signature": {"hash": "j1k2l3m4n5"},
    },
    {
        "event_type": "RADAR_DETECTION",
        "asset_id": "radar-lora-alboran-01",
        "lat": 35.9000, "lon": -3.0500,
        "classification_level": "SECRET",
        "confidence_score": 0.78,
        "payload": {"target_type": "airborne", "speed_kt": 65, "altitude_ft": 800, "heading": 10, "rng_m": 12000, "iff_response": False},
        "signature": {"hash": "o6p7q8r9s0"},
    },
    {
        "event_type": "RADAR_DETECTION",
        "asset_id": "uav-siva-canarias-01",
        "lat": 28.5000, "lon": -14.8000,
        "classification_level": "CONFIDENTIAL",
        "confidence_score": 0.87,
        "payload": {"target_type": "vessel", "speed_kt": 15, "heading": 90, "length_m": 60, "sensor": "EO/IR"},
        "signature": {"hash": "t1u2v3w4x5"},
    },
    {
        "event_type": "SATELLITE_IMAGE",
        "asset_id": "sat-paz-01",
        "lat": 36.1000, "lon": -4.8000,
        "classification_level": "TOP_SECRET",
        "confidence_score": 0.93,
        "payload": {"resolution_m": 1, "cloud_cover_pct": 0, "detections": 15, "feature": "buque mercante en fondeadero no autorizado", "timestamp_utc": "2026-07-18T06:15:00Z"},
        "signature": {"hash": "y6z7a8b9c0"},
    },
    {
        "event_type": "RADAR_DETECTION",
        "asset_id": "radar-ran3l-melilla-01",
        "lat": 35.2500, "lon": -2.9800,
        "classification_level": "SECRET",
        "confidence_score": 0.91,
        "payload": {"target_type": "ground_vehicle", "speed_kmh": 40, "heading": 180, "count": 12, "rng_m": 22000, "formation": "column"},
        "signature": {"hash": "d1e2f3g4h5"},
    },
    {
        "event_type": "SATELLITE_IMAGE",
        "asset_id": "sat-paz-01",
        "lat": 42.5000, "lon": -12.7500,
        "classification_level": "TOP_SECRET",
        "confidence_score": 0.96,
        "payload": {"resolution_m": 1, "cloud_cover_pct": 5, "detections": 2, "feature": "buque de guerra clase Almirante Gorshkov", "timestamp_utc": "2026-07-12T08:00:00Z"},
        "signature": {"hash": "i6j7k8l9m0"},
    },
    {
        "event_type": "COMMS_INTERCEPT",
        "asset_id": "sensor-comms-canarias-01",
        "lat": 28.1167, "lon": -15.4333,
        "classification_level": "SECRET",
        "confidence_score": 0.72,
        "payload": {"frequency_mhz": 2450, "modulation": "DSSS", "protocol": "WiFi", "ssid": "RED_TACTICA_02", "rssi_dbm": -65, "content_summary": "Tráfico de datos no clasificado"},
        "signature": {"hash": "n1o2p3q4r5"},
    },
    {
        "event_type": "RADAR_DETECTION",
        "asset_id": "uav-rq11-moron-01",
        "lat": 37.2000, "lon": -5.7000,
        "classification_level": "CONFIDENTIAL",
        "confidence_score": 0.82,
        "payload": {"target_type": "personnel", "count": 6, "heading": 45, "speed_kmh": 5, "sensor": "EO"},
        "signature": {"hash": "s6t7u8v9w0"},
    },
]

# ─── Datos de mensajes tácticos ─────────────────────────────────────────────

MESSAGES = [
    {
        "message_type": "SITREP",
        "priority": "HIGH",
        "subject": "Reporte de situación — Estrecho D+1",
        "content": "SITREP 001/2026\n\n1. SITUACIÓN GENERAL: Sin novedades significativas en el sector Estrecho durante las últimas 24h.\n2. TRÁFICO MARTÍMO: 127 buques detectados (112 cooperativos AIS, 15 no cooperativos).\n3. INCIDENCIAS: 1 embarcación sospechosa interceptada por P-71. Trasladada a puerto de Algeciras.\n4. ESTADO DE FUERZAS: Patrullera P-71 Audaz continúa patrulla. Relevo previsto D+2.\n\nRODRÍGUEZ\nCapitán de Corbeta\nCOMFLOES",
        "classification": "SECRET",
        "sender_username": "capitan.lopez",
        "recipient_usernames": ["coronel.garcia"],
    },
    {
        "message_type": "REQUEST",
        "priority": "URGENT",
        "subject": "Solicitud de apoyo UAV para vigilancia Melilla",
        "content": "SOLICITO: Apoyo de sistema aéreo no tripulado para vigilancia continuada del perímetro este de Melilla durante las próximas 72h.\n\nFUNDAMENTO: 14 incursiones de drones no identificados detectadas en los últimos 15 días. Capacidad actual insuficiente para cobertura 24/7.\n\nEFECTOS: Refuerzo de vigilancia y capacidad de interdicción electrónica.\n\nMARTÍN\nTeniente\nAnalista de Inteligencia",
        "classification": "CONFIDENTIAL",
        "sender_username": "teniente.martin",
        "recipient_usernames": ["capitan.lopez"],
    },
    {
        "message_type": "ORDER",
        "priority": "HIGH",
        "subject": "Orden de activación — Protocolo Ciberdefensa Algeciras",
        "content": "ORDEN N.º 2026/07\n\n1. Se activa el protocolo de ciberdefensa nivel 3 en el puerto de Algeciras.\n2. Todo el tráfico SCADA será monitorizado en tiempo real por el MCCE.\n3. Se suspenden accesos remotos a sistemas de gestión portuaria hasta nueva orden.\n4. El Oficial de Seguridad rendirá informe cada 6h.\n\nGARCÍA\nCoronel\nEstado Mayor",
        "classification": "TOP_SECRET",
        "sender_username": "coronel.garcia",
        "recipient_usernames": ["capitan.lopez", "teniente.martin"],
    },
    {
        "message_type": "INFO",
        "priority": "ROUTINE",
        "subject": "Novedades de inteligencia — Sahel",
        "content": "NOTA DE INTELIGENCIA N.º 2026/07/22\n\nLas imágenes satelitales del PAZ confirman concentración de fuerzas irregulares en Sáhara Occidental. Se estima capacidad de interdicción de la ruta NC-2.\n\nSe recomienda:\n- Incrementar vigilancia satelital diaria\n- Alertar a la Agrupación de Tráfico para posibles desvíos de convoyes logísticos\n\nPróxima actualización: 24/07/2026.\n\nMARTÍN\nTeniente\nAnalista de Inteligencia",
        "classification": "SECRET",
        "sender_username": "teniente.martin",
        "recipient_usernames": ["coronel.garcia", "capitan.lopez"],
    },
    {
        "message_type": "SITREP",
        "priority": "HIGH",
        "subject": "Incursión de dron en Melilla — Reporte inmediato",
        "content": "REPORTE INMEDIATO IR-2026/07/23\n\nA las 23:47 UTC, radar RAN-3L detectó incursión de dron no identificado en sector este de Melilla.\n- Altitud: 600 m AGL\n- Velocidad: 70 km/h\n- Rumbo: 280° (penetrando hacia el oeste)\n- Duración: 8 minutos dentro del perímetro\n- Medidas tomadas: Contramedidas electrónicas activadas. Dron se retiró.\n\nSe solicita refuerzo de sistema C-UAV.\n\nLÓPEZ\nCapitán\nOficial de Guardia",
        "classification": "SECRET",
        "sender_username": "capitan.lopez",
        "recipient_usernames": ["coronel.garcia"],
    },
    {
        "message_type": "ORDER",
        "priority": "HIGH",
        "subject": "Directiva de seguridad — Ejercicio conjunto OTAN",
        "content": "DIRECTIVA CONJUNTA 2026/04\n\nPara: BRI VI Almogávares, Ala 14, Flotilla de Escoltas\n\n1. Ejercicio conjunto OTAN 'LOYAL LEDA 26' programado del 01/08 al 15/08.\n2. Fase de preparación comienza el 25/07.\n3. Clasificación general: SECRET\n4. Los planes de ejercicio serán distribuidos por canal STANAG 4406.\n5. Designar oficial de enlace antes del 28/07.\n\nGARCÍA\nCoronel\nEMAD",
        "classification": "SECRET",
        "sender_username": "coronel.garcia",
        "recipient_usernames": ["capitan.lopez", "teniente.martin"],
    },
    {
        "message_type": "REPLY",
        "priority": "HIGH",
        "subject": "RE: Solicitud de apoyo UAV para vigilancia Melilla",
        "content": "RESPONDIDO.\n\n1. Se aprueba despliegue de unidad SIVA desde Gando.\n2. ETA estimada: 24/07/2026 08:00 UTC.\n3. Enlace designado: Teniente Martín.\n4. Se adjunta plan de misión en anexo.\n\nLÓPEZ\nCapitán\nOficial de Operaciones",
        "classification": "CONFIDENTIAL",
        "sender_username": "capitan.lopez",
        "recipient_usernames": ["teniente.martin"],
    },
    {
        "message_type": "INFO",
        "priority": "ROUTINE",
        "subject": "Parte de comunicaciones — Buque ruso",
        "content": "COMUNICACIONES NAVALES — PARTE DIARIO\n\nEl grupo naval ruso Almirante Gorshkov continúa tránsito hacia el norte. Última posición conocida: 44°30'N 11°00'W.\n\nEscolta de la Armada: Patrullera Infanta Elena (P-76) mantiene seguimiento discreto a 15 nm.\n\nSin novedades adicionales.\n\nLÓPEZ\nCapitán\nCIVIMAR",
        "classification": "SECRET",
        "sender_username": "capitan.lopez",
        "recipient_usernames": ["coronel.garcia"],
    },
]

# ─── Datos de OPORDs ────────────────────────────────────────────────────────

OPORDS = [
    {
        "operation_name": "OPERACIÓN CENTINELA — RECON",
        "classification": "SECRET",
        "paragraph_1_situation": {
            "enemy": "Fuerzas irregulares detectadas en Sáhara Occidental (26°48'N 13°00'W). Capacidad de interdicción de rutas logísticas NC-2 estimada en 48h.",
            "friendly": "BRI X Extremadura en Badajoz. Mando de Operaciones en Madrid. Apoyo satelital PAZ/INGENIO disponible.",
            "attachments": "1x sección de reconocimiento (16 pax), 2x VAMTAC S3, 1x UAV RQ-11 Raven.",
        },
        "paragraph_2_mission": {
            "task": "BRI X realiza reconocimiento armado del sector Sáhara Occidental D+3 para verificar capacidad de interdicción de fuerzas irregulares sobre ruta NC-2.",
            "purpose": "Garantizar libertad de movimiento de convoyes logísticos y proporcionar inteligencia para planes de contingencia.",
        },
        "paragraph_3_execution": {
            "concept": "FASE 1 (D+1): Despliegue de sección de reconocimiento a base avanzada en Dajla. FASE 2 (D+2): Penetración y observación del área objetivo. FASE 3 (D+3): Extracción y reporte.",
            "scheme_of_maneuver": "Eje de avance: Dajla → 26°48'N 13°00'W. Zona de reunión inicial: 26°30'N 14°00'W.",
            "tasks": "1. Establecer OP en cota 220. 2. Observar y reportar movimientos. 3. No entablar combate. 4. Extracción por helitransporte.",
            "coord_instructions": "Coordenadas de extracción: 26°35'N 13°30'W. Señal de extracción: dos bengalas verdes. Frecuencia: 47.250 MHz.",
        },
        "paragraph_4_sustainment": {
            "supply": "Agua: 10L/pax/día. Raciones: 3/día. Munición: 5.56 mm 600 rds/pax.",
            "transportation": "2x VAMTAC S3. Apoyo helitransporte NH90 para extracción.",
            "medical": "1x enfermero de combate. Punto de evacuación: Dajla. MEDEVAC primario: helicóptero UH-60.",
        },
        "paragraph_5_command_signal": {
            "comm_plan": "PRC-152 en frecuencia principal 47.250 MHz. SATCOM respaldo. Señal de verificación horaria: cada 4h.",
            "chain_of_command": "Comandante: Cte. Sánchez (BRI X). 2º Comandante: Tte. Navarro. Enlace EMAD: Cap. López.",
        },
        "status": "APPROVED",
        "author_username": "coronel.garcia",
    },
    {
        "operation_name": "OPERACIÓN ESCUDO — SEGURIDAD",
        "classification": "SECRET",
        "paragraph_1_situation": {
            "enemy": "Amenaza de incursiones de drones no identificados en Melilla. Tráfico ilícito marítimo activo en el Estrecho.",
            "friendly": "Servicio Marítimo GC en Cartagena. Ala 14 en Albacete. Radar LORA y RAN-3L operativos.",
            "attachments": "1x patrullera P-71, 1x unidad SIVA, 2x equipo C-UAV RPS-42.",
        },
        "paragraph_2_mission": {
            "task": "Flotilla de Escoltas y Guardia Civil establecen perímetro de seguridad marítimo-aéreo en sector Estrecho-Melilla D+5 para neutralizar amenazas híbridas.",
            "purpose": "Proteger infraestructura crítica portuaria y garantizar seguridad del tráfico marítimo en aguas jurisdiccionales.",
        },
        "paragraph_3_execution": {
            "concept": "FASE 1 (D+1-D+2): Establecer barrera radar en el Estrecho. FASE 2 (D+3-D+4): Patrullaje activo y vigilancia UAV en Melilla. FASE 3 (D+5): Evaluación de efectividad.",
            "scheme_of_maneuver": "Sectorización: Zona A (Estrecho Oeste), Zona B (Estrecho Este), Zona C (Mar de Alborán), Zona D (Melilla).",
            "tasks": "1. P-71 patrulla Zona A y B. 2. SIVA realiza vigilancia Zona D. 3. RPS-42 cubre perímetro terrestre Melilla. 4. LORA y RAN-3L proporcionan cobertura radar continua.",
            "coord_instructions": "Zonas de exclusión: 36°05'N 5°25'W a 36°00'N 5°35'W. Cambio de guardia cada 12h. Señal de emergencia: 243.0 MHz.",
        },
        "paragraph_4_sustainment": {
            "supply": "Combustible naval: 20,000L. Repostaje en Rota cada 48h. UAV SIVA: recarga cada 8h.",
            "transportation": "P-71 Audaz. Unidad SIVA. Vehículos terrestres para equipos C-UAV.",
            "medical": "COMED en cada unidad. MEDEVAC coordinado con Ala 14 (HH-60).",
        },
        "paragraph_5_command_signal": {
            "comm_plan": "Red táctica en UHF 380-400 MHz. Enlace satelital cada 6h. Código de autenticación: ALFA-BRAVO-7.",
            "chain_of_command": "Comandante táctico: Cap. de Fragata Muñoz. 2º Comandante: Tte. Coronel Romero (GC). Enlace EMAD: Cor. García.",
        },
        "status": "DRAFT",
        "author_username": "capitan.lopez",
    },
    {
        "operation_name": "OPERACIÓN VIGÍA — DRONE",
        "classification": "CONFIDENTIAL",
        "paragraph_1_situation": {
            "enemy": "Actividad persistente de drones no identificados en perímetro de Melilla. 14 incursiones confirmadas en 15 días. Origen triangulado desde zona este de Nador.",
            "friendly": "MAAA con sistema RPS-42. RAN-3L cubriendo baja cota. SIVA en comisión desde Gando.",
            "attachments": "1x RPS-42, 1x SIVA, 1x equipo EW portátil.",
        },
        "paragraph_2_mission": {
            "task": "MAAA despliega sistema C-UAV en Melilla D+2 para neutralizar amenaza de drones no identificados en el perímetro fronterizo.",
            "purpose": "Garantizar la seguridad del espacio aéreo sobre Melilla y proteger las fuerzas desplegadas.",
        },
        "paragraph_3_execution": {
            "concept": "FASE 1 (D+0): Reconocimiento y selección de posiciones. FASE 2 (D+1): Despliegue de RPS-42 y equipo EW. FASE 3 (D+2): Activación y operación continuada.",
            "scheme_of_maneuver": "Posición principal: 35°17'N 2°56'W. Posición secundaria: 35°18'N 2°55'W.",
            "tasks": "1. Desplegar RPS-42 en posición principal. 2. Establecer circuito de alerta con RAN-3L. 3. Activar contramedidas ante incursión. 4. Reportar resultados cada 12h.",
            "coord_instructions": "Zona de responsabilidad: 5 km alrededor del perímetro. Altitud de vigilancia: 0-1000 m AGL. Frecuencia de coordinación: 47.300 MHz.",
        },
        "paragraph_4_sustainment": {
            "supply": "Grupo electrógeno: combustible para 72h. Repuestos RPS-42 en depósito.",
            "transportation": "2x VAMTAC S3 para despliegue.",
            "medical": "Botiquín de campaña. Evacuación a Hospital de Melilla.",
        },
        "paragraph_5_command_signal": {
            "comm_plan": "PRC-152. Enlace satélite cada 4h. Autenticación: CHARLIE-DELTA-3.",
            "chain_of_command": "Comandante: Cap. García (MAAA). Enlace: Teniente Martín (Intel).",
        },
        "status": "APPROVED",
        "author_username": "teniente.martin",
    },
]

# ─── Datos de logística ─────────────────────────────────────────────────────

LOGISTICS = [
    {
        "item_type": "COMBUSTIBLE_NAVAL",
        "quantity": 50000.0,
        "unit": "L",
        "min_threshold": 10000.0,
        "classification_level": "CONFIDENTIAL",
    },
    {
        "item_type": "MUNICION_5_56",
        "quantity": 250000.0,
        "unit": "rds",
        "min_threshold": 50000.0,
        "classification_level": "SECRET",
    },
    {
        "item_type": "RACIONES_CAMPAÑA",
        "quantity": 5000.0,
        "unit": "uds",
        "min_threshold": 1000.0,
        "classification_level": "UNCLASSIFIED",
    },
    {
        "item_type": "MEDEVAC_KIT",
        "quantity": 50.0,
        "unit": "kit",
        "min_threshold": 10.0,
        "classification_level": "CONFIDENTIAL",
    },
    {
        "item_type": "REPUESTOS_UAV",
        "quantity": 12.0,
        "unit": "uds",
        "min_threshold": 4.0,
        "classification_level": "SECRET",
    },
]

# ─── Datos de tracks (Blue Force / AIS) ─────────────────────────────────────

AIS_TRACKS = [
    {
        "unit_id": None,
        "asset_id": "buque-p71-audaz-01",
        "lat": 36.0200, "lon": -5.3800,
        "altitude": 0, "heading": 225.0, "speed": 12.5,
        "status": "ACTIVE",
    },
    {
        "unit_id": None,
        "asset_id": "buque-jci-01",
        "lat": 36.6100, "lon": -6.3400,
        "altitude": 0, "heading": 0.0, "speed": 0.0,
        "status": "STANDBY",
    },
    {
        "unit_id": None,
        "asset_id": None,
        "lat": 35.9800, "lon": -5.4500,
        "altitude": 0, "heading": 78.0, "speed": 16.8,
        "status": "ACTIVE",
    },
    {
        "unit_id": None,
        "asset_id": None,
        "lat": 36.1000, "lon": -5.1500,
        "altitude": 0, "heading": 310.0, "speed": 20.2,
        "status": "ACTIVE",
    },
    {
        "unit_id": None,
        "asset_id": None,
        "lat": 35.9200, "lon": -5.5200,
        "altitude": 0, "heading": 180.0, "speed": 8.2,
        "status": "ACTIVE",
    },
    {
        "unit_id": None,
        "asset_id": None,
        "lat": 36.1500, "lon": -4.8500,
        "altitude": 0, "heading": 45.0, "speed": 0.5,
        "status": "ACTIVE",
    },
    {
        "unit_id": None,
        "asset_id": None,
        "lat": 36.0500, "lon": -5.6000,
        "altitude": 0, "heading": 270.0, "speed": 24.5,
        "status": "ACTIVE",
    },
    {
        "unit_id": None,
        "asset_id": None,
        "lat": 35.8000, "lon": -4.2000,
        "altitude": 0, "heading": 135.0, "speed": 10.0,
        "status": "ACTIVE",
    },
]

# ─── Datos de sensores (tabla sensors) ──────────────────────────────────────

SENSORS = [
    {
        "sensor_type": "RADAR_LORA",
        "lat": 36.0000, "lon": -5.6000,
        "status": "ACTIVE",
        "metadata_json": {"designacion": "LORA-Estrecho", "alcance_km": 200, "banda": "L"},
    },
    {
        "sensor_type": "RADAR_RAN3L",
        "lat": 35.3000, "lon": -2.9500,
        "status": "ACTIVE",
        "metadata_json": {"designacion": "RAN-3L-Melilla", "alcance_km": 150, "banda": "S"},
    },
    {
        "sensor_type": "COMINT",
        "lat": 28.4500, "lon": -16.2833,
        "status": "ACTIVE",
        "metadata_json": {"designacion": "COMINT-Canarias", "bandas": "VHF/UHF/SATCOM"},
    },
    {
        "sensor_type": "RADAR_LORA",
        "lat": 35.9500, "lon": -3.0333,
        "status": "MAINTENANCE",
        "metadata_json": {"designacion": "LORA-Alboran", "alcance_km": 180, "banda": "L"},
    },
    {
        "sensor_type": "UAV_RQ11",
        "lat": 37.1333, "lon": -5.6333,
        "status": "DEPLOYED",
        "metadata_json": {"designacion": "RQ11-Moron", "base": "Morón"},
    },
    {
        "sensor_type": "UAV_SIVA",
        "lat": 28.1167, "lon": -15.4333,
        "status": "DEPLOYED",
        "metadata_json": {"designacion": "SIVA-Canarias", "base": "Gando"},
    },
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _user_id_by_username(users_map: dict, username: str) -> str:
    return users_map[username]


async def _user_exists(session, username: str) -> bool:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalars().first() is not None


# ─── Main seed logic ─────────────────────────────────────────────────────────

async def main():
    settings = get_settings()
    logger.info("🌱 Iniciando seed de datos demo para SESIS-FEDERATION...")
    logger.info(f"   Base de datos: {settings.DATABASE_URL}")

    counts = {
        "usuarios": 0,
        "reportes": 0,
        "alertas": 0,
        "unidades": 0,
        "activos": 0,
        "eventos": 0,
        "mensajes": 0,
        "opords": 0,
        "logistica": 0,
        "tracks": 0,
        "sensores": 0,
    }

    async with async_session() as session:
        # ── 1. USUARIOS ──────────────────────────────────────────────────────
        users_map = {}  # username -> id
        for u in USERS:
            exists = await _user_exists(session, u["username"])
            if exists:
                result = await session.execute(
                    select(User).where(User.username == u["username"])
                )
                user = result.scalars().first()
                users_map[u["username"]] = user.id
                logger.info(f"   ⏩ Usuario '{u['username']}' ya existe, ID: {user.id}")
                continue

            user_id = str(uuid.uuid4())
            user = User(
                id=user_id,
                username=u["username"],
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
                classification_level=u["classification_level"],
                is_active=True,
            )
            session.add(user)
            users_map[u["username"]] = user_id
            counts["usuarios"] += 1

        await session.commit()
        logger.info(f"   ✓ {counts['usuarios']} usuarios nuevos creados")

        # ── 2. REPORTES DE INTELIGENCIA ──────────────────────────────────────
        for r in INTEL_REPORTS:
            exists = False
            result = await session.execute(
                select(IntelReport).where(IntelReport.title == r["title"])
            )
            if result.scalars().first():
                exists = True

            if not exists:
                author_id = users_map.get(r["author_username"])
                report = IntelReport(
                    id=str(uuid.uuid4()),
                    title=r["title"],
                    body=r["body"],
                    classification=r["classification"],
                    source=r["source"],
                    author_id=author_id,
                    created_at=NOW - timedelta(days=len(INTEL_REPORTS) - INTEL_REPORTS.index(r)),
                )
                session.add(report)
                counts["reportes"] += 1

        await session.commit()
        logger.info(f"   ✓ {counts['reportes']} reportes nuevos creados")

        # ── 3. ALERTAS ───────────────────────────────────────────────────────
        for i, a in enumerate(ALERTS):
            result = await session.execute(
                select(Alert).where(
                    Alert.rule_id == a["rule_id"],
                    Alert.severity == a["severity"],
                )
            )
            if result.scalars().first():
                continue

            alert = Alert(
                id=str(uuid.uuid4()),
                rule_id=a["rule_id"],
                severity=a["severity"],
                description=a["description"],
                is_anomaly=(a["severity"] == "CRITICAL"),
                human_validated=False,
                validated_by=None,
                event_id=None,
            )
            session.add(alert)
            counts["alertas"] += 1

        await session.commit()
        logger.info(f"   ✓ {counts['alertas']} alertas nuevas creadas")

        # ── 4. UNIDADES (ORBAT) ──────────────────────────────────────────────
        orbat_map = {}  # name -> id
        for u in ORBAT_UNITS:
            result = await session.execute(
                select(ORBATUnit).where(ORBATUnit.name == u["name"])
            )
            existing = result.scalars().first()
            if existing:
                orbat_map[u["name"]] = existing.id
                continue

            unit_id = str(uuid.uuid4())
            unit = ORBATUnit(
                id=unit_id,
                name=u["name"],
                unit_type=u["unit_type"],
                classification_level="SECRET",
                lat=u["lat"],
                lon=u["lon"],
                status=u["status"],
                metadata_json=u["metadata_json"],
            )
            session.add(unit)
            orbat_map[u["name"]] = unit_id
            counts["unidades"] += 1

        await session.commit()
        logger.info(f"   ✓ {counts['unidades']} unidades nuevas creadas")

        # ── 5. ACTIVOS ──────────────────────────────────────────────────────
        for a in ASSETS:
            result = await session.execute(
                select(Asset).where(Asset.id == a["id"])
            )
            if result.scalars().first():
                continue

            asset = Asset(
                id=a["id"],
                kind=a["kind"],
                current_status=a["current_status"],
                last_heartbeat=NOW,
                lat=a["lat"],
                lon=a["lon"],
                classification_level=a["classification_level"],
                metadata_json=a["metadata_json"],
            )
            session.add(asset)
            counts["activos"] += 1

        await session.commit()
        logger.info(f"   ✓ {counts['activos']} activos nuevos creados")

        # ── 6. EVENTOS DE SENSOR ─────────────────────────────────────────────
        for i, e in enumerate(SENSOR_EVENTS):
            asset_exists = await session.execute(
                select(Asset).where(Asset.id == e["asset_id"])
            )
            if not asset_exists.scalars().first():
                continue

            event = Event(
                event_id=str(uuid.uuid4()),
                event_type=e["event_type"],
                asset_id=e["asset_id"],
                ts=NOW - timedelta(hours=i * 6, minutes=(len(SENSOR_EVENTS) - i) * 15),
                lat=e["lat"],
                lon=e["lon"],
                classification_level=e["classification_level"],
                confidence_score=e["confidence_score"],
                payload=e["payload"],
                signature=e["signature"],
            )
            session.add(event)
            counts["eventos"] += 1

        await session.commit()
        logger.info(f"   ✓ {counts['eventos']} eventos nuevos creados")

        # ── 7. MENSAJES TÁCTICOS ─────────────────────────────────────────────
        for m in MESSAGES:
            sender_id = users_map.get(m["sender_username"])
            if not sender_id:
                continue
            recipient_ids = [
                users_map[r]
                for r in m["recipient_usernames"]
                if r in users_map
            ]
            if not recipient_ids:
                continue

            msg = TacticalMessage(
                id=str(uuid.uuid4()),
                sender_id=sender_id,
                recipient_ids=recipient_ids,
                message_type=m["message_type"],
                priority=m["priority"],
                subject=m["subject"],
                content=m["content"],
                timestamp=NOW - timedelta(hours=MESSAGES.index(m) * 8),
                classification=m["classification"],
                is_read=False,
            )
            session.add(msg)
            counts["mensajes"] += 1

        await session.commit()
        logger.info(f"   ✓ {counts['mensajes']} mensajes nuevos creados")

        # ── 8. OPORDs ────────────────────────────────────────────────────────
        for o in OPORDS:
            author_id = users_map.get(o["author_username"])
            if not author_id:
                continue

            result = await session.execute(
                select(EnhancedOPORD).where(
                    EnhancedOPORD.operation_name == o["operation_name"]
                )
            )
            if result.scalars().first():
                continue

            opord = EnhancedOPORD(
                id=str(uuid.uuid4()),
                operation_name=o["operation_name"],
                classification=o["classification"],
                paragraph_1_situation=o["paragraph_1_situation"],
                paragraph_2_mission=o["paragraph_2_mission"],
                paragraph_3_execution=o["paragraph_3_execution"],
                paragraph_4_sustainment=o["paragraph_4_sustainment"],
                paragraph_5_command_signal=o["paragraph_5_command_signal"],
                status=o["status"],
                created_by=author_id,
                created_at=NOW - timedelta(days=len(OPORDS) - OPORDS.index(o)),
            )
            session.add(opord)
            counts["opords"] += 1

        await session.commit()
        logger.info(f"   ✓ {counts['opords']} OPORDs nuevos creados")

        # ── 9. LOGÍSTICA ─────────────────────────────────────────────────────
        for log_item in LOGISTICS:
            result = await session.execute(
                select(LogisticsSupply).where(
                    LogisticsSupply.item_type == log_item["item_type"],
                )
            )
            if result.scalars().first():
                continue

            supply = LogisticsSupply(
                id=str(uuid.uuid4()),
                item_type=log_item["item_type"],
                quantity=log_item["quantity"],
                unit=log_item["unit"],
                min_threshold=log_item["min_threshold"],
                classification_level=log_item["classification_level"],
            )
            session.add(supply)
            counts["logistica"] += 1

        await session.commit()
        logger.info(f"   ✓ {counts['logistica']} registros logísticos nuevos creados")

        # ── 10. TRACKS (Blue Force / AIS) ────────────────────────────────────
        for t in AIS_TRACKS:
            track = BlueForceTracking(
                id=str(uuid.uuid4()),
                unit_id=None,
                asset_id=t["asset_id"],
                lat=t["lat"],
                lon=t["lon"],
                altitude=t["altitude"],
                heading=t["heading"],
                speed=t["speed"],
                status=t["status"],
                timestamp=NOW - timedelta(hours=AIS_TRACKS.index(t) * 2),
            )
            session.add(track)
            counts["tracks"] += 1

        await session.commit()
        logger.info(f"   ✓ {counts['tracks']} tracks AIS nuevos creados")

        # ── 11. SENSORES ─────────────────────────────────────────────────────
        for s in SENSORS:
            result = await session.execute(
                select(Sensor).where(
                    Sensor.sensor_type == s["sensor_type"],
                    Sensor.lat == s["lat"],
                    Sensor.lon == s["lon"],
                )
            )
            if result.scalars().first():
                continue

            sensor = Sensor(
                id=str(uuid.uuid4()),
                sensor_type=s["sensor_type"],
                lat=s["lat"],
                lon=s["lon"],
                status=s["status"],
                metadata_json=s["metadata_json"],
            )
            session.add(sensor)
            counts["sensores"] += 1

        await session.commit()
        logger.info(f"   ✓ {counts['sensores']} sensores nuevos creados")

    # ── Resumen final ────────────────────────────────────────────────────────
    total = sum(counts.values())
    parts = ", ".join(
        f"{v} {k}" for k, v in counts.items() if v > 0
    )
    logger.info("")
    logger.info(f"✅ Seed completado: {parts}")
    logger.info(f"   Total de registros insertados: {total}")


if __name__ == "__main__":
    asyncio.run(main())
