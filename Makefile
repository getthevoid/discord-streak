.PHONY: install dev format lint typecheck check clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Run the application"
	@echo "  make format     - Format code with ruff"
	@echo "  make lint       - Lint code with ruff"
	@echo "  make typecheck  - Type check with pyright"
	@echo "  make check      - Run all checks (format, lint, typecheck)"
	@echo "  make clean      - Remove cache files"

# Install dependencies
install:
	uv sync

# Run the application
dev:
	uv run python -m src

# Format code
format:
	uv run ruff format .

# Lint code
lint:
	uv run ruff check --fix .

# Type check
typecheck:
	uv run pyright

# Run all checks
check: format lint typecheck

# Clean cache files
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
