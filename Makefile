.PHONY: help build up down restart logs shell migrate makemigrations createsuperuser test lint format clean

# ==============================================================================
# Comandos de ayuda
# ==============================================================================
help:  ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==============================================================================
# Docker
# ==============================================================================
build:  ## Construir contenedores
	docker-compose build

up:  ## Levantar servicios
	docker-compose up -d

down:  ## Detener servicios
	docker-compose down

restart:  ## Reiniciar servicios
	docker-compose restart

logs:  ## Ver logs de todos los servicios
	docker-compose logs -f

logs-web:  ## Ver logs solo del servicio web
	docker-compose logs -f web

shell:  ## Abrir shell de Django
	docker-compose exec web python manage.py shell

bash:  ## Abrir bash en el contenedor web
	docker-compose exec web bash

# ==============================================================================
# Django
# ==============================================================================
migrate:  ## Aplicar migraciones
	docker-compose exec web python manage.py migrate

makemigrations:  ## Crear migraciones
	docker-compose exec web python manage.py makemigrations

createsuperuser:  ## Crear superusuario
	docker-compose exec web python manage.py createsuperuser

collectstatic:  ## Recolectar archivos estáticos
	docker-compose exec web python manage.py collectstatic --noinput

# ==============================================================================
# Testing & Quality
# ==============================================================================
test:  ## Ejecutar tests
	docker-compose exec web pytest

test-coverage:  ## Ejecutar tests con cobertura
	docker-compose exec web pytest --cov=. --cov-report=html

lint:  ## Ejecutar linter (flake8)
	docker-compose exec web flake8 .

format:  ## Formatear código (black + isort)
	docker-compose exec web black .
	docker-compose exec web isort .

# ==============================================================================
# Utilidades
# ==============================================================================
clean:  ## Limpiar archivos generados
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete

reset-db:  ## Resetear base de datos (¡CUIDADO!)
	docker-compose down -v
	docker-compose up -d db
	sleep 3
	docker-compose up -d web
	docker-compose exec web python manage.py migrate
	@echo "Base de datos reseteada. Considera crear un superusuario con 'make createsuperuser'"

# ==============================================================================
# Setup inicial
# ==============================================================================
setup:  ## Setup inicial del proyecto
	cp .env.example .env
	@echo "✅ Archivo .env creado. Edítalo con tus valores."
	docker-compose build
	docker-compose up -d
	sleep 5
	docker-compose exec web python manage.py migrate
	@echo "✅ Proyecto configurado. Crea un superusuario con 'make createsuperuser'"
