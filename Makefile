PORT ?= 8000

install:
	uv sync

package-install:
	uv tool install dist/*.whl

lint:
	uv run ruff check page_analyzer

dev:
	uv run flask --debug --app page_analyzer:app run

start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

build:
	./build.sh

.PHONY: install dev start render-start build