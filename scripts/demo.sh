#!/bin/bash
set -euo pipefail

echo "============================================"
echo " SESIS-FEDERATION — Inicio de Demo"
echo "============================================"
echo ""

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "[AVISO] .env no encontrado. Copiando desde .env.example..."
        cp .env.example .env
        echo "[AVISO] Revise las credenciales en .env antes de continuar."
        echo ""
    else
        echo "[ERROR] No existe .env ni .env.example. Abortando."
        exit 1
    fi
fi

if [ ! -f fernet.key ]; then
    echo "[INFO] Generando fernet.key..."
    python scripts/generate_keys.py
fi

echo "[1/4] Construyendo imagenes e iniciando servicios..."
docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build -d

echo "[2/4] Esperando 15s a que los servicios se estabilicen..."
sleep 15

echo "[3/4] Ejecutando seed de datos..."
docker compose -f docker-compose.yml -f docker-compose.demo.yml --profile seed-only run --rm seed || echo "[AVISO] Seed reporto errores (no critico para la demo)"

echo "[4/4] Abriendo navegador..."
if command -v xdg-open &>/dev/null; then
    xdg-open "https://localhost"
elif command -v open &>/dev/null; then
    open "https://localhost"
elif command -v gnome-open &>/dev/null; then
    gnome-open "https://localhost"
else
    echo "Abra https://localhost en su navegador."
fi

echo ""
echo "============================================"
echo " Demo iniciada. Accesos:"
echo " Frontend    : https://localhost"
echo " API         : https://localhost/api/v1/health"
echo " Grafana     : http://localhost:3001"
echo " Prometheus  : http://localhost:9090"
echo ""
echo " Admin por defecto: admin / \${ADMIN_INITIAL_PASSWORD}"
echo ""
echo " Para detener: docker compose down"
echo "============================================"
