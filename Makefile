.PHONY: setup test run migrate lint docker-up docker-down

setup:
	python -m venv venv
	./venv/bin/pip install -r requirements.txt || venv\Scripts\pip install -r requirements.txt
	$(MAKE) test

test:
	python -m pytest app/tests/ -v

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

lint:
	ruff check app/
	black --check app/

docker-up:
	docker compose up --build

docker-down:
	docker compose down
