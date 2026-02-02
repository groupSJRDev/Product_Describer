# Product Describer Makefile
# Simplifies common operations for analyzing and generating product images

.PHONY: help describe generate test install setup clean format lint up down test-backend test-frontend test-all

# Default target - show help
help:
	@echo "Product Describer - Makefile Commands"
	@echo "======================================"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make up             Start backend and frontend"
	@echo "  make down           Stop backend services"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install dependencies with Poetry"
	@echo "  make setup          Complete project setup (install + create dirs)"
	@echo ""
	@echo "Analysis:"
	@echo "  make describe       Analyze product images and generate YAML specs"
	@echo "                      Requires: PRODUCT_NAME set in .env"
	@echo ""
	@echo "Testing:"
	@echo "  make test-all       Run all tests (backend + frontend)"
	@echo "  make test-backend   Run backend tests with pytest"
	@echo "  make test-frontend  Run frontend build and lint"
	@echo ""
	@echo "Generation:"
	@echo "  make generate       Generate image using default or saved prompt"
	@echo ""
	@echo "With custom prompt:"
	@echo "  make generate PROMPT='Your custom prompt here'"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format         Format code with Black"
	@echo "  make lint           Run linters (flake8 and mypy)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          Remove generated files and caches"
	@echo ""
	@echo "Examples:"
	@echo "  make describe"
	@echo "  make generate"
	@echo "  make generate PROMPT='Futuristic neon style'"
	@echo ""

# Install dependencies
install:
	@echo "Installing dependencies..."
	poetry install
	@echo "✓ Dependencies installed"

# Complete setup
setup: install
	@echo "Setting up project directories..."
	@mkdir -p data temp
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env file - please configure it"; \
	else \
		echo "✓ .env already exists"; \
	fi
	@echo "✓ Project setup complete"

# Run product analysis (description generation)
describe:
	@echo "Analyzing product images..."
	@echo "============================"
	@poetry run python -m product_describer.main
	@echo ""
	@echo "✓ Analysis complete!"

# Generate image with optional custom prompt
generate:
	@if [ -n "$(PROMPT)" ]; then \
		echo "Using custom prompt: $(PROMPT)"; \
		echo ""; \
		GENERATION_PROMPT="$(PROMPT)" poetry run python -m product_describer.generate_test; \
	else \
		echo "Using default or saved prompt"; \
		echo ""; \
		poetry run python -m product_describer.generate_test; \
	fi

# Run backend tests
test-backend:
	@echo "Running backend tests..."
	@echo "========================"
	@poetry run pytest tests/ -v
	@echo ""
	@echo "✓ Backend tests complete!"

# Run frontend tests
test-frontend:
	@echo "Running frontend tests..."
	@echo "========================="
	@echo ""
	@echo "Building frontend..."
	@cd frontend && npm run build
	@echo ""
	@echo "Running ESLint..."
	@cd frontend && npm run lint
	@echo ""
	@echo "✓ Frontend tests complete!"

# Run all tests
test-all: test-backend test-frontend
	@echo ""
	@echo "=============================="
	@echo "✓ All tests passed successfully!"
	@echo "=============================="

# Format code with Black
format:
	@echo "Formatting code with Black..."
	@poetry run black src/ tests/
	@echo "✓ Code formatted"

# Run linters
lint:
	@echo "Running linters..."
	@echo "Flake8:"
	@poetry run flake8 src/ tests/ || true
	@echo ""
	@echo "MyPy:"
	@poetry run mypy src/ || true
	@echo "✓ Linting complete"

# Clean generated files and caches
clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleaned caches and temporary files"

# Quick workflow: analyze then generate
workflow:
	@echo "Running complete workflow..."
	@echo ""
	@make describe
	@echo ""
	@make generate
	@echo ""
	@echo "✓ Workflow complete!"

# Infrastructure commands
up:
	@./scripts/start.sh

down:
	@./scripts/stop.sh
