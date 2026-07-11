.PHONY: install test build dev-backend dev-frontend compose-up compose-down compose-config

install:
	python -m pip install -r backend/requirements.txt
	npm --prefix frontend install

test:
	cd backend && pytest

build:
	npm --prefix frontend run build

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	npm --prefix frontend run dev

compose-up:
	docker compose up --build

compose-down:
	docker compose down

compose-config:
	docker compose config

