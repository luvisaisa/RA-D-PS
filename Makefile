# Makefile for RA-D-PS Schema-Agnostic System
# Python 3.12+, PostgreSQL 16, Docker required

.PHONY: help setup db-up db-down db-migrate db-reset test fmt lint clean docs

# Default target
help:
	@echo "RA-D-PS Schema-Agnostic System - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Install dependencies and setup environment"
	@echo "  make install        - Install package in editable mode"
	@echo ""
	@echo "Database Management:"
	@echo "  make db-up          - Start PostgreSQL container"
	@echo "  make db-down        - Stop PostgreSQL container"
	@echo "  make db-migrate     - Apply database migrations"
	@echo "  make db-reset       - ⚠️  Reset database (deletes all data)"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo "  make pgadmin        - Start pgAdmin UI (http://localhost:5050)"
	@echo ""
	@echo "Development:"
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make fmt            - Format code with black"
	@echo "  make lint           - Run linters (flake8, mypy)"
	@echo "  make clean          - Remove build artifacts and cache files"
	@echo ""
	@echo "Running:"
	@echo "  make api            - Start FastAPI server (when implemented)"
	@echo "  make gui            - Launch Tkinter GUI"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-up      - Start all services"
	@echo "  make docker-down    - Stop all services"
	@echo "  make docker-logs    - View container logs"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs           - Open implementation guide"

# ============================================================================
# SETUP
# ============================================================================

setup:
	@echo "🔧 Setting up development environment..."
	python3 -m pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✅ Setup complete"

install:
	@echo "📦 Installing ra-d-ps package..."
	pip install -e .
	@echo "✅ Package installed in editable mode"

# ============================================================================
# DATABASE MANAGEMENT
# ============================================================================

db-up:
	@echo "🐘 Starting PostgreSQL..."
	docker-compose up -d postgres
	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@sleep 5
	@docker-compose ps postgres
	@echo "✅ PostgreSQL is running"

db-down:
	@echo "🛑 Stopping PostgreSQL..."
	docker-compose down
	@echo "✅ PostgreSQL stopped"

db-migrate:
	@echo "📊 Applying database migrations..."
	@export PGPASSWORD=changeme && \
	psql -h localhost -U ra_d_ps_user -d ra_d_ps_db \
	     -f migrations/001_initial_schema.sql
	@echo "✅ Migrations applied"

db-reset:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo "🗑️  Resetting database..."
	docker-compose down -v
	$(MAKE) db-up
	@sleep 5
	$(MAKE) db-migrate
	@echo "✅ Database reset complete"

db-shell:
	@echo "🐚 Opening PostgreSQL shell..."
	@export PGPASSWORD=changeme && \
	psql -h localhost -U ra_d_ps_user -d ra_d_ps_db

pgadmin:
	@echo "🌐 Starting pgAdmin..."
	docker-compose --profile dev up -d pgadmin
	@echo "✅ pgAdmin running at http://localhost:5050"
	@echo "   Email: admin@ra-d-ps.local"
	@echo "   Password: admin"

# ============================================================================
# TESTING
# ============================================================================

test:
	@echo "🧪 Running all tests..."
	pytest -q

test-unit:
	@echo "🧪 Running unit tests..."
	pytest tests/ -k "not integration" -v

test-integration:
	@echo "🧪 Running integration tests..."
	pytest tests/integration/ -v

test-coverage:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=src/ra_d_ps --cov-report=html --cov-report=term
	@echo "📊 Coverage report: htmlcov/index.html"

test-watch:
	@echo "👁️  Running tests in watch mode..."
	pytest-watch

# ============================================================================
# CODE QUALITY
# ============================================================================

fmt:
	@echo "🎨 Formatting code with black..."
	black src/ tests/ --line-length 100
	@echo "✅ Code formatted"

lint:
	@echo "🔍 Running linters..."
	@echo "▶️  flake8..."
	flake8 src/ tests/ --max-line-length 100 --extend-ignore=E203,W503
	@echo "▶️  mypy..."
	mypy src/ra_d_ps --ignore-missing-imports
	@echo "✅ Linting complete"

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete"

# ============================================================================
# RUNNING
# ============================================================================

api:
	@echo "🚀 Starting FastAPI server..."
	uvicorn src.ra_d_ps.api.main:app --reload --host 0.0.0.0 --port 8000

gui:
	@echo "🖥️  Launching GUI..."
	python -m src.ra_d_ps.gui

parse:
	@echo "📄 Running CLI parser..."
	@read -p "Enter XML file path: " filepath && \
	python -m src.cli.parse "$$filepath"

# ============================================================================
# DOCKER
# ============================================================================

docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t ra-d-ps:latest .
	@echo "✅ Docker image built"

docker-up:
	@echo "🐳 Starting all services..."
	docker-compose --profile api up -d
	@echo "✅ All services running"
	@docker-compose ps

docker-down:
	@echo "🛑 Stopping all services..."
	docker-compose --profile api down
	@echo "✅ All services stopped"

docker-logs:
	@echo "📜 Viewing container logs..."
	docker-compose logs -f

docker-shell:
	@echo "🐚 Opening shell in API container..."
	docker-compose exec api bash

# ============================================================================
# DEVELOPMENT UTILITIES
# ============================================================================

profile-test:
	@echo "🧪 Testing profile manager..."
	python3 -c "\
from src.ra_d_ps.profile_manager import get_profile_manager; \
manager = get_profile_manager(); \
print(f'Profiles loaded: {len(manager.list_profiles())}'); \
print('✅ Profile manager working')"

schema-test:
	@echo "🧪 Testing canonical schema..."
	python3 -c "\
from src.ra_d_ps.schemas.canonical import RadiologyCanonicalDocument, DocumentMetadata; \
from datetime import datetime; \
doc = RadiologyCanonicalDocument( \
    document_metadata=DocumentMetadata(title='Test', date=datetime.now()), \
    study_instance_uid='1.2.3.4.5' \
); \
print(f'Document type: {doc.document_metadata.document_type}'); \
print('✅ Canonical schema working')"

db-status:
	@echo "📊 Database status..."
	@export PGPASSWORD=changeme && \
	psql -h localhost -U ra_d_ps_user -d ra_d_ps_db -c "\
		SELECT 'Documents' as table, COUNT(*) as count FROM documents \
		UNION ALL \
		SELECT 'Profiles', COUNT(*) FROM profiles \
		UNION ALL \
		SELECT 'Logs', COUNT(*) FROM ingestion_logs;"

create-profile:
	@echo "📝 Creating new profile..."
	@mkdir -p profiles
	@read -p "Profile name: " name && \
	python3 scripts/create_profile.py "$$name"

# ============================================================================
# DOCUMENTATION
# ============================================================================

docs:
	@echo "📖 Opening documentation..."
	@if command -v open > /dev/null; then \
		open docs/IMPLEMENTATION_GUIDE_SCHEMA_AGNOSTIC.md; \
	elif command -v xdg-open > /dev/null; then \
		xdg-open docs/IMPLEMENTATION_GUIDE_SCHEMA_AGNOSTIC.md; \
	else \
		echo "Please open docs/IMPLEMENTATION_GUIDE_SCHEMA_AGNOSTIC.md manually"; \
	fi

docs-summary:
	@echo "📖 Opening summary..."
	@cat docs/SCHEMA_AGNOSTIC_SUMMARY.md | head -n 50

quickstart:
	@echo "📖 Opening quickstart..."
	@cat QUICKSTART_SCHEMA_AGNOSTIC.md

# ============================================================================
# CI/CD (for future use)
# ============================================================================

ci: lint test
	@echo "✅ CI checks passed"

pre-commit: fmt lint test
	@echo "✅ Pre-commit checks passed"

# ============================================================================
# MIGRATION HELPERS
# ============================================================================

migrate-sqlite-to-postgres:
	@echo "🔄 Migrating SQLite data to PostgreSQL..."
	@echo "⚠️  Not yet implemented - create script in /scripts/"

export-profiles:
	@echo "📤 Exporting all profiles..."
	@mkdir -p exports
	python3 -c "\
from src.ra_d_ps.profile_manager import get_profile_manager; \
manager = get_profile_manager(); \
for p in manager.list_profiles(): \
    manager.export_profile(p.profile_name, f'exports/{p.profile_name}.json'); \
    print(f'Exported: {p.profile_name}');"
	@echo "✅ Profiles exported to exports/"

import-profiles:
	@echo "📥 Importing profiles from profiles/ directory..."
	@for f in profiles/*.json; do \
		echo "Importing $$f..."; \
		python3 -c "from src.ra_d_ps.profile_manager import get_profile_manager; \
		            manager = get_profile_manager(); \
		            manager.import_profile('$$f')"; \
	done
	@echo "✅ Profiles imported"
