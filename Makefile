.PHONY: install run test docker-up

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

run:
	python dashboard.py

test:
	pytest

docker-up:
	docker compose up --build
