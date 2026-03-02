.PHONY: install run test docker-up docker-down docker-logs

install:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt

run:
	.venv/bin/python main.py

test:
	.venv/bin/pytest

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f bot
