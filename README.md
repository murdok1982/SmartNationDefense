# 🛡️ SmartNationDefense / SESIS-FEDERATION

<h3 align="center">
  ────────── Plataforma Experimental de Inteligencia y Fusión Multisensor ──────────
  <br>
  <sub>Fusión multisensor · Computer Vision · Soporte a decisión algorítmico · Common Operating Picture</sub>
  <br>
  <sub><i>Prototipo de investigación y arquitectura de referencia para C4ISR defensivo</i></sub>
</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Versión-2.1_Hardened-1a5276?style=for-the-badge&logo=codefactor" alt="Version">
  <img src="https://img.shields.io/badge/Estado-Reference_Implementation-27ae60?style=for-the-badge&logo=checkmarx" alt="Status">
  <img src="https://img.shields.io/badge/Arquitectura-Modular_C4ISR-8e44ad?style=for-the-badge&logo=databricks" alt="Architecture">
  <img src="https://img.shields.io/badge/Stack-FastAPI_+_Next.js_+_Flutter-61dafb?style=for-the-badge&logo=react" alt="Stack">
  <img src="https://img.shields.io/badge/IA-YOLOv8_+_LLM_+_Heurísticas-f39c12?style=for-the-badge&logo=tensorflow" alt="AI">
  <img src="https://img.shields.io/badge/Licencia-MIT-2c3e50?style=for-the-badge&logo=opensourceinitiative" alt="License">
</p>

> [!IMPORTANT]
> **AVISO DE RESPONSABILIDAD TÉCNICA Y OPERATIVA:**
> SmartNationDefense es un **prototipo de ingeniería de software, arquitectura de referencia e investigación tecnológica**.
> **NO ES UN SISTEMA DE COMBATE MILITAR EN PRODUCCIÓN ("Military-Grade Production")**.
> Todas las recomendaciones generadas por IA/LLM, simulaciones de wargaming y cursos de acción (COA) tienen carácter **ESTRICTAMENTE NO OPERATIVO / ASISTENCIA A LA DECISIÓN** y requieren **AUTORIZACIÓN HUMANA OBLIGATORIA (Human-in-the-Loop)** antes de cualquier ejecución en el mundo real.

---

```ascii
═══════════════════════════════════════════════════════════════════════════════════
                        ███████  ███████ ███████ ██ ███████
                        ██      ██      ██      ██ ██
                        ███████ ███████ ███████ ██ ███████
                             ██      ██      ██ ██      ██
                        ███████ ███████ ███████ ██ ███████

                   ┌──────────────────────────────────────────┐
                   │   SISTEMA DE DEFENSA NACIONAL INTEGRADA  │
                   │   National Integrated Defense System      │
                   └──────────────────────────────────────────┘
═══════════════════════════════════════════════════════════════════════════════════
```

---

## 🎯 ¿Qué es esto? (Resumen Ejecutivo)

**SmartNationDefense** es una plataforma de software modular diseñada para la ingesta, normalización, correlación y visualización unificada de datos multisensor:

- 🛰️ **Análisis de imágenes (Satélite / Dron)**: Detección y bounding boxes mediante modelos YOLOv8 y algoritmos de visión por computador.
- 🎯 **Soporte de Cursos de Acción (COA)**: Generación algorítmica y heurística de opciones tácticas para evaluación y filtro humano.
- 🔗 **Fusión de Datos Multisensor**: Correlación temporal y espacial de trazas de radar, telemetría y fuentes de datos abiertas (OSINT).
- 🖥️ **Common Operating Picture (COP)**: Interfaz unificada en Web (Next.js) y cliente de campo móvil (Flutter) para monitoreo de alertas y eventos.

---

## 🏗️ Arquitectura del Sistema

```ascii
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SMARTNATIONDEFENSE                               │
│                                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   🛰️ SATÉLITE  │  │   📡 RADAR   │  │   ✈️ DRON    │  │   🌐 OSINT      │ │
│  │  Imágenes    │  │  Telemetría  │  │  Video feed  │  │  Noticias / Web │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └───────┬──────────┘ │
│         │                │                  │                  │            │
│         ▼                ▼                  ▼                  ▼            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    🧬 MOTOR DE FUSIÓN (JDL Niveles 0–4)              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │ Nivel 0  │→│ Nivel 1  │→│ Nivel 2  │→│ Nivel 3  │→│ Nivel 4  │  │   │
│  │  │  Señal   │ │  Objeto  │ │Situación │ │ Impacto  │ │ Proceso  │  │   │
│  │  │(Filtro)  │ │(Correlac)│ │(Táctico) │ │ (Riesgo) │ │ (Sensores│  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  👁️ VISIÓN POR COMPUTADORA   │  │  🧠 COA ENGINE   │  │  🤖 LLM AGENT │  │
│  │  YOLOv8 Inferencia          │  │  Plantillas táct.│  │  Generación   │  │
│  │  Detección cambios          │  │  Evaluación ries.│  │  estructurada │  │
│  └─────────────────────────────┘  └──────────────────┘  └───────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │               🖥️ COP UNIFICADO (Common Operating Picture)            │   │
│  │   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │   │
│  │   │  Mapa  │ │ Intel  │ │Alertas │ │  COA   │ │Logíst. │ │  Mando │ │   │
│  │   │táctico │ │feed    │ │tiempo  │ │Planner │ │Panel   │ │Voz     │ │   │
│  │   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────────────────────┐  │
│  │  🌐 Web      │  │  📱 Móvil      │  │  🛡️ Seguridad Hardened        │  │
│  │  Next.js    │  │  Flutter       │  │  Auth · SSRF Safe · Rate Limit │  │
│  │  COP UI     │  │  Offline-first │  │  JWT · MFA (GCM) · Audit SHA256│  │
│  └──────────────┘  └────────────────┘  └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Capacidades y Estado de Implementación

### 🛰️ 1. VISIÓN POR COMPUTADORA
| Capacidad | Estado | Funcionamiento Técnico |
|---|:---:|---|
| **Detección de objetos** | `VALIDADO` | Inferencia YOLOv8 sobre clases de transporte e infraestructura. |
| **Detección de cambios** | `EXPERIMENTAL` | Comparación temporal de fotogramas satelitales vía Sentinel-2 / Landsat. |
| **Flujo de dron** | `EXPERIMENTAL` | Extracción de contornos y cálculo de heatmap temporal. |

### 🧬 2. FUSIÓN MULTISENSOR (JDL Niveles 0–4)
| Nivel | Nombre | Estado | Descripción |
|---|---|:---:|---|
| 0 | Señal | `EXPERIMENTAL` | Agrupamiento y normalización de detecciones crudas. |
| 1 | Objeto | `EXPERIMENTAL` | Correlación espacial por distancia Haversine y ventana temporal. |
| 2 | Situación | `EXPERIMENTAL` | Reconocimiento de formaciones y agrupaciones tácticas. |
| 3 | Impacto | `EXPERIMENTAL` | Estimación heurística de amenaza y ventanas de oportunidad. |
| 4 | Proceso | `EXPERIMENTAL` | Sugerencias de asignación y reconfiguración de sensores. |

### 🎯 3. CURSOS DE ACCIÓN (COA) Y SIMULACIÓN
- **Carácter:** Simulación y apoyo analítico (NO OPERATIVO).
- **Plantillas:** Envolvimiento, penetración, fuegos indirectos, defensa perimétrica.
- **Validación:** Regla de autorización humana (Human Approval Required) en toda recomendación.

### 🛡️ 4. SEGURIDAD Y CONTROL DE ACCESO
- **Autenticación:** JWT con claims tipados, `jti` revocable en Redis y tokens de refresco rotados.
- **MFA:** Desafíos TOTP con secretos cifrados en reposo mediante **AES-256-GCM** y tickets de reto (`type="mfa_challenge"`) de un solo uso.
- **Control de Acceso:** ABAC jerárquico (`OPEN` → `RESTRICTED` → `CONFIDENTIAL` → `SECRET` → `TOP_SECRET`) verificado en backend.
- **Anti-Brute Force:** Protección distribuida con Redis y bloqueo tras 5 intentos fallidos.
- **Anti-SSRF:** Bloqueo estricto de redes RFC 1918, CGNAT, 0.0.0.0/8, benchmarking, IPv6 local y metadata endpoints.
- **Cadena de Auditoría:** Encadenamiento criptográfico **SHA-256** con persistencia en base de datos y control de concurrencia.

### 🌐 6. OSINT (Inteligencia de Fuentes Abiertas)
- Búsqueda en redes sociales, foros, dark web
- Escaneo de puertos y servicios (Shodan)
- Verificación de filtraciones (Have I Been Pwned)
- WhoIS, DNS, certificados SSL
- Análisis de inteligencia financiera (FinInt)
- Correlación de fuentes con deduplicación inteligente

### 📱 7. MÓVIL (Flutter)
- App COP en tiempo real
- Mesh P2P cifrado con HMAC-SHA256 + anti-replay
- Certificate pinning real (SHA-256)
- Almacenamiento seguro de tokens (flutter_secure_storage)
- Señal de coacción (Duress PIN) — borra credenciales al activarse
- Despliegue táctico sin infraestructura (mesh P2P)

---

## 🧪 Casos prácticos (misiones reales)

### 🏴‍☠️ Caso 1: Interdicción marítima en el Estrecho

**Situación:** La Guardia Civil detecta una embarcación sospechosa en el Estrecho de Gibraltar. No responde a llamadas. Podría ser narco-tráfico o inmigración ilegal.

**Cómo ayuda SmartNationDefense:**

```
1. 📡 Radar costero → SensorEvent {type: "RADAR_CONTACT", pos: 35.9°N, 5.3°W, speed: 18kn}
2. 🛰️ Satélite PAZ → foto del barco, YOLO lo clasifica como "lancha rápida"
3. 🔗 Fusión JDL → correlaciona radar + satélite = mismo target → Track #473
4. 🇪🇸 Base de datos → el barco no tiene AIS, no está registrado → ALERTA
5. 🎯 COA Engine propone:
   ┌──────────────────────────────────────────────────┐
   │ 🥇 Opción A (Score 87): Interceptar con P-71    │
   │   Riesgo: BAJO · Tiempo: 25 min                  │
   │ 🥈 Opción B (Score 72): Seguimiento desde dron  │
   │   Riesgo: MUY BAJO · Tiempo: 15 min              │
   │ 🥉 Opción C (Score 45): Bloqueo de puerto        │
   │   Riesgo: MEDIO · Tiempo: 45 min                 │
   └──────────────────────────────────────────────────┘
6. 👨‍✈️ Mando elige Opción A → genera OPORD automáticamente
7. ✅ Misión completada: interceptación, inspección, incautación
```

### 🛸 Caso 2: Detección de drones no identificados en Melilla

**Situación:** Múltiples drones cruzan la frontera de Melilla. Podrían ser contrabando o vigilancia.

**Cómo ayuda SmartNationDefense:**

```
1. 🛰️ Radar de baja altitud (RAN-3L) → 3 contactos a 200m, 30 nudos
2. 👁️ Visión por computadora: cámara térmica + YOLO → "DJI Matrice 300"
3. 🧬 Fusión: no están en flight plan → ALERTA CRÍTICA
4. 💡 Sugiere: activar guerra electrónica (EW) para interferir GPS
5. 🎯 COA: 3 opciones con evaluación de riesgo civil
6. 📱 Alerta push a móvil del jefe de operaciones
7. 🚁 Se despliega dron SIVA para identificación visual
```

### 🌐 Caso 3: Ciberataque a infraestructura crítica

**Situación:** El puerto de Algeciras sufre un ataque informático. Los sistemas de carga están caídos.

**Cómo ayuda SmartNationDefense:**

```
1. 🔴 Alerta CYBER desde el SOC del puerto
2. 🌐 OSINT busca en foros de hacking → "SombraNegra" se atribuye el ataque
3. 🧬 Correlación: mismo grupo atacó otros puertos → patrón conocido
4. 📊 Reporte automático de inteligencia (STIX/TAXII compatible)
5. 🎯 COA: recomienda aislar redes + activar protocolo de contingencia
6. 📋 After Action Review generado automáticamente
```

---

## 🚀 Instalación (paso a paso, como si tuvieras 10 años)

### 📋 Lo que necesitas
- Un ordenador con **Windows 10/11** o **Linux** (8 GB RAM mínimo, 16 GB mejor)
- **Docker** instalado ([descargar aquí](https://docker.com))
- **Git** instalado ([descargar aquí](https://git-scm.com))
- **Python 3.12+** (solo para seed de datos)
- **Node.js 20+** (solo para frontend)
- Opcional: **Flutter 3.22+** (solo para móvil)

### 🎬 Paso 1: Descargar el proyecto

```bash
# Abre una terminal (PowerShell en Windows, bash en Linux)
git clone https://github.com/murdok1982/SmartNationDefense.git
cd SmartNationDefense
```

### ⚙️ Paso 2: Configurar

```bash
# Copia el archivo de ejemplo de configuración
cp .env.example .env

# Ahora edita .env con un bloc de notas:
# - Cambia CHANGE_ME_POSTGRES_PASSWORD por una contraseña tuya
# - Cambia CHANGE_ME_NEO4J_PASSWORD por otra
# - Cambia CHANGE_ME_GRAFANA_PASSWORD por otra
# - Deja DEBUG=false (modo producción)
```

> 💡 **Pista**: Las contraseñas deben ser distintas entre sí, y largas. Ej: `MiClaveSuperSegura123!`

### 🐳 Paso 3: Arrancar con Docker (opción fácil)

```bash
# En Windows:
scripts\demo.bat

# En Linux/Mac:
make demo

# ¿Qué hace esto? 1) Construye todo 2) Arranca bases de datos
# 3) Puebla datos de demostración 4) Abre el navegador
```

### 🐳 Paso 3b: O manualmente (si eres más técnico)

```bash
# Arranca todo
docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build -d

# Espera 15 segundos a que postgres arranque
# Llena la base de datos con datos de ejemplo
docker compose run --rm seed

# Abre el navegador en: https://localhost
```

### 🧪 Paso 4: Verificar que funciona

```bash
# El sistema debería responder:
curl https://localhost/health
# → {"status": "ok", "version": "2.0"}

# Y la web debería mostrarte la pantalla de login en:
# https://localhost
```

### 🎮 Paso 5: Jugar con la demo

Usa estas credenciales para entrar:

| 👤 Usuario | 🔑 Contraseña | 🎖️ Nivel | 🎯 Rol |
|---|---|---|---|
| `coronel.garcia` | `Demo2024!` | TOP SECRET | admin |
| `capitan.lopez` | `Demo2024!` | SECRET | operator |
| `teniente.martin` | `Demo2024!` | RESTRICTED | analyst |

---

## 🎨 Cómo usarlo (guía visual)

### 🌐 Web (Frontend COP)

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔴 RESTRICTED ● SECRET ● TOP SECRET     👤 coronel.garcia   ⏰ 14:23 │
├─────────────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────────────────────────────────────────────┐   │
│ │ 📋 MENÚ  │ │                  🗺️ MAPA TÁCTICO                 │   │
│ │          │ │                                                  │   │
│ │ ☰ Intel  │ │     🟦 Brigada X     🔴 Contacto radar          │   │
│ │ ⚠️Alertas│ │        🟦 Brigada VI     🔴 Drone hostil        │   │
│ │ 🎯 COA   │ │     🟦 Armada            🟢 Buque neutral       │   │
│ │ 🔗 Fusión│ │        🟦 Ala 14     🟠 Zona de exclusión      │   │
│ │ 🛰️ Maven  │ │                                                  │   │
│ │          │ │               🟡 38°12'N, 5°15'W                │   │
│ └──────────┘ └──────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│ │📡 Detecciones │🔴 Alertas │📊 Intel │📜 Timeline                │
│ ├──────────────────────────────────────────────────────────────────┤
│ │ ⏱️ 14:20 🛰️ Satélite detecta movimiento en Sector 7             │
│ │ ⏱️ 14:15 📡 Radar: 3 contactes a 12nm, rumbo 045°              │
│ │ ⏱️ 14:10 ✈️ Dron SIVA reporta convoy en carretera N-340         │
│ └──────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────┘
```

### 🛰️ Maven Fusion (la guinda)

Navega a **https://localhost/maven** para ver:

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🛰️ MAVEN FUSION                         [🔄 Auto-refresh cada 30s]  │
├─────────────────────────────────────────────────────────────────────┤
│ ┌──────────┬──────────┬──────────┬──────────┬────────────────────┐  │
│ │ 🛰️       │  🎯      │  🧬      │  🎯      │  ⚔️ COA PLANNER    │  │
│ │ Satélite │Detect.  │ Tracks  │ COA    │  ┌────────────────┐ │  │
│ │          │CV       │Fusionad.│Planner │  │ Objetivo:      │ │  │
│ │[imagen]  │[YOLO]   │[tracks] │[score] │  │ Lat: 35.89     │ │  │
│ │          │         │         │        │  │ Lon: -5.33     │ │  │
│ │T-72 98%  │Camión   │Track 47 │🥇87   │  │ Fuerzas: ▣▣▣▣▢  │ │  │
│ │Bunker87% │militar  │Track 23 │🥈72   │  │ [Generar COAs] │ │  │
│ │          │         │         │        │  └────────────────┘ │  │
│ └──────────┴──────────┴──────────┴────────┴────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuración avanzada

### Variables de entorno importantes en `.env`

| Variable | ¿Qué es? | Ejemplo |
|---|---|---|
| `DATABASE_URL` | Dónde está la base de datos | `postgresql+asyncpg://user:pass@postgres:5432/sesis` |
| `SECRET_KEY` | La clave maestra para firmar tokens | `cambia-esto-en-produccion` |
| `REDIS_URL` | Conexión a Redis (caché + sesiones) | `redis://redis:6379/0` |
| `NATS_URL` | Mensajería en tiempo real | `nats://nats:4222` |
| `NEO4J_URL` | Base de datos de grafos (inteligencia) | `bolt://neo4j:7687` |
| `ADMIN_INITIAL_PASSWORD` | Contraseña del admin en primer arranque | `cambia-esto-tambien` |
| `CELESTRAK_TLE_URL` | Fuente de datos de satélites | `https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle` |
| `TERRAIN_ELEVATION_API_URL` | API de elevación del terreno | `https://api.open-elevation.com` |
| `AISSTREAM_API_KEY` | API key para tracking de barcos | (opcional, déjalo vacío si no tienes) |
| `NEWSAPI_API_KEY` | API key para noticias OSINT | (opcional) |

### Pre-descargar el modelo YOLO (para demo sin internet)

```bash
# Con internet, una sola vez:
cd backend
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
python -c "
from pathlib import Path
import shutil
src = Path.home() / '.cache' / 'ultralytics' / 'models' / 'yolov8n.pt'
dst = Path('app/services/vision/models/yolov8n.pt')
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(str(src), str(dst))
print('✅ Modelo listo para demo offline en', dst)
"
```

---

## 🧪 Tests (para asegurarte de que todo funciona)

```bash
cd backend

# Ejecuta todos los tests (23 pruebas)
python -m pytest tests/ -v

# Verás algo así:
# ✅ test_login_correct_creds PASSED
# ✅ test_login_incorrect_creds PASSED
# ✅ test_register PASSED
# ✅ test_health PASSED
# ✅ test_alerts_without_token PASSED
# ✅ test_logout_valid_token PASSED
# ✅ test_refresh_rotation_after_logout PASSED
# ✅ test_rejects_private_ip_127 PASSED
# ✅ ... 23/23 passed!
```

---

## 📚 Mapa de archivos del proyecto

```
SmartNationDefense/
├── backend/                  # 🖥️ Servidor Python (FastAPI)
│   ├── app/
│   │   ├── api/              # 🌐 Endpoints REST
│   │   │   ├── v1/           #   COP básico (alerts, intel, map, messaging...)
│   │   │   ├── v2/           #   Espacio, frontera, cyber, EW
│   │   │   ├── v3/           #   🚀 MAVEN (visión, fusión, COA)
│   │   │   ├── tactical/     #   ⚔️ OpOrd, wargaming, BDA, PSYOPS
│   │   │   ├── osint/        #   🌐 Inteligencia fuentes abiertas
│   │   │   ├── intel/        #   📊 Inteligencia clasificada
│   │   │   ├── agents/       #   🤖 Agentes autónomos
│   │   │   └── satellite/    #   🛰️ Procesamiento satelital
│   │   ├── core/             #   🔧 Seguridad, crypto, config, rate limit
│   │   ├── db/               #   🗄️ Modelos de base de datos
│   │   ├── services/         #   🧠 Lógica de negocio
│   │   │   ├── vision/       #     👁️ Computer Vision (YOLOv8)
│   │   │   ├── fusion/       #     🧬 Fusión JDL 5 niveles
│   │   │   ├── tactical/     #     ⚔️ COA engine, wargaming real
│   │   │   ├── osint/        #     🌐 OSINT tools (Shodan, HIBP, DNS...)
│   │   │   ├── terrain/      #     ⛰️ Elevación Open-Elevation
│   │   │   ├── satellite/    #     🛰️ CelesTrak + detección
│   │   │   └── prediction/   #     📈 Predicción de amenazas
│   │   └── main.py           #   🚀 Punto de entrada
│   ├── tests/                # 🧪 23 tests (y creciendo)
│   └── requirements.txt      # 📦 Dependencias Python
├── frontend/                 # 🌐 Web COP (Next.js + TypeScript + Zustand)
│   └── src/
│       ├── app/
│       │   ├── login/        #   🔑 Pantalla de login
│       │   └── maven/        #   🚀 COP Unificado tipo Palantir
│       └── components/
│           └── cop/          # 📦 Componentes del COP
├── mobile/                   # 📱 App móvil (Flutter)
│   └── sesis_cop/lib/
│       ├── core/network/     # 🔐 API client + Mesh cifrado + Pinning
│       ├── features/         # 📱 Pantallas (login, dashboard, intel, etc.)
│       └── core/storage/     # 💾 Almacenamiento local cifrado
├── ml/                       # 📊 Machine Learning (correlación, anomalías)
├── guardian/                 # 🛡️ Guardian scripts (Python, Rust, Shell, Dart...)
├── infra/                    # 🏗️ Infraestructura (nginx, grafana, prometheus)
│   └── ssl/                  # 🔒 Certificados TLS para demo
├── scripts/                  # 📜 Scripts de utilidad (demo, seed)
├── docker-compose.yml        # 🐳 Orquestación Docker
├── docker-compose.demo.yml   # 🐳 Override de demo
└── .env.example              # ⚙️ Configuración de ejemplo
```

---

## ☎️ API (para desarrolladores)

### 🔐 Autenticación

```bash
# Obtener token
curl -X POST https://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "coronel.garcia", "password": "Demo2024!"}'

# → {"access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer"}

# Usar token para llamadas autenticadas
curl https://localhost/api/v1/alerts/ \
  -H "Authorization: Bearer eyJ..."
```

### 🎯 Endpoints principales

| Método | Ruta | ¿Qué hace? |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Iniciar sesión |
| `POST` | `/api/v1/auth/refresh` | Renovar token |
| `POST` | `/api/v1/auth/logout` | Cerrar sesión |
| `GET` | `/api/v1/health` | ¿Está vivo el sistema? |
| `GET` | `/api/v1/alerts/` | Alertas activas |
| `GET` | `/api/v1/intel/feed` | Feed de inteligencia |
| `POST` | `/api/v1/messaging/send` | Enviar mensaje táctico |
| `POST` | `/api/v3/vision/analyze-satellite` | 📸 Analizar imagen satélite |
| `POST` | `/api/v3/vision/detect-changes` | 🆚 Detectar cambios entre fotos |
| `POST` | `/api/v3/fusion/ingest-event` | 📡 Ingerir evento de sensor |
| `GET` | `/api/v3/fusion/cop` | 🗺️ Obtener COP fusionado |
| `POST` | `/api/v3/coa/generate` | 🎯 Generar cursos de acción |
| `POST` | `/api/v3/coa/compare` | ⚖️ Comparar COAs |
| `GET` | `/api/v3/coa/templates` | 📋 Ver plantillas ROAD |

📖 Documentación completa interactiva: `https://localhost/docs`

---

## 🛡️ Seguridad (esto es serio)

SmartNationDefense ha sido diseñado con **Zero Trust Architecture**:

| Principio | Implementación |
|---|---|
| **Nunca confíes, siempre verifica** | Cada petición se autentica, cada token se valida |
| **Mínimo privilegio** | Cada usuario ve solo lo que su clearance permite |
| **Defensa en profundidad** | Auth + rate limit + SSRF protection + audit + cifrado |
| **Datos en reposo cifrados** | PostgreSQL + cifrado de campo con Fernet |
| **Datos en tránsito cifrados** | TLS 1.2+ exclusivo, HSTS, CSP estricto |
| **No exponer secretos** | Contraseñas en .env (nunca en código), bcrypt |
| **Anti-fuerza bruta** | 5 intentos/minuto por IP en login |
| **Anti-SSRF** | Validación de IP destino anti-DNS rebinding |
| **Logs inmutables** | Cadena de auditoría encadenada criptográficamente |

---

## 📋 Licencia

MIT © 2026 — Ver archivo [LICENSE](LICENSE) para más detalles.

---

## 👨‍💻 ¿Preguntas?

| Canal | Cómo llegar |
|---|---|
| **Issues** | Abre un issue en [GitHub](https://github.com/murdok1982/SmartNationDefense/issues) |
| **Discusiones** | Usa la pestaña Discussions del repo |

---

<h3 align="center">
  <sub>Hecho en 🇪🇸 España · Con ❤️ para nuestras Fuerzas Armadas</sub>
  <br><br>
  <sub>
  "La mejor defensa es conocer todo lo que pasa antes de que pase"
  </sub>
</h3>

```ascii
═══════════════════════════════════════════════════════════════════════════════════
  SmartNationDefense v2.0 — C4ISR · Fusion · Vision · COA · COP
═══════════════════════════════════════════════════════════════════════════════════
```
