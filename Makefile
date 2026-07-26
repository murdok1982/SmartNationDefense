.PHONY: dev build up down logs clean demo demo-windows seed seed-docker keys

dev:
	docker compose up -d --build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v --rmi all

demo:
	scripts/demo.sh

demo-windows:
	scripts/demo.bat

seed:
	PYTHONPATH=backend python backend/scripts/seed_data.py

seed-docker:
	docker compose -f docker-compose.yml -f docker-compose.demo.yml --profile seed-only run --rm seed

keys:
	python scripts/generate_keys.py
