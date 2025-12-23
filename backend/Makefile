.PHONY: help install dev test migrate create-migration run

help:
	@echo "VAS Backend Makefile"
	@echo ""
	@echo "Commands:"
	@echo "  install           - Install dependencies"
	@echo "  dev               - Run development server with hot reload"
	@echo "  test              - Run tests"
	@echo "  migrate           - Run database migrations"
	@echo "  create-migration  - Create new migration (MESSAGE='description')"
	@echo "  run               - Run production server"

install:
	pip install -r requirements.txt

dev:
	uvicorn main:app --host 0.0.0.0 --port 8080 --reload

test:
	pytest tests/ -v

migrate:
	alembic upgrade head

create-migration:
	alembic revision --autogenerate -m "$(MESSAGE)"

run:
	uvicorn main:app --host 0.0.0.0 --port 8080


