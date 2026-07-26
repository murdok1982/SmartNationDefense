@echo off
title SESIS-FEDERATION — Demo

echo ============================================
echo  SESIS-FEDERATION — Inicio de Demo
echo ============================================
echo.

if not exist .env (
    if exist .env.example (
        echo [AVISO] .env no encontrado. Copiando desde .env.example...
        copy .env.example .env
        echo [AVISO] Revise las credenciales en .env antes de continuar.
        echo.
    ) else (
        echo [ERROR] No existe .env ni .env.example. Abortando.
        exit /b 1
    )
)

if not exist fernet.key (
    echo [INFO] Generando fernet.key...
    python scripts\generate_keys.py
)

echo [1/4] Construyendo imagenes e iniciando servicios...
docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build -d
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Fallo al iniciar los servicios.
    exit /b 1
)

echo [2/4] Esperando 15s a que los servicios se estabilicen...
timeout /t 15 /nobreak >nul

echo [3/4] Ejecutando seed de datos...
docker compose -f docker-compose.yml -f docker-compose.demo.yml --profile seed-only run --rm seed
if %ERRORLEVEL% neq 0 (
    echo [AVISO] Seed reporto errores (no critico para la demo)
)

echo [4/4] Abriendo navegador...
start https://localhost

echo.
echo ============================================
echo  Demo iniciada. Accesos:
echo  Frontend : https://localhost
echo  API      : https://localhost/api/v1/health
echo  Grafana  : http://localhost:3001
echo  Prometheus : http://localhost:9090
echo.
echo  Admin por defecto: admin / (la variable ADMIN_INITIAL_PASSWORD)
echo.
echo  Para detener: docker compose down
echo ============================================
echo.
pause
