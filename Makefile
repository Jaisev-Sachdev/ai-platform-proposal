# =============================================================================
# Venti AI Platform — Makefile
# Shortcuts for common operations. Run `make help` to see all commands.
# =============================================================================

.PHONY: help setup phoenix-up phoenix-down phoenix-logs multica-setup demo clean

MULTICA_DIR := multica-server
ENV_FILE    := .env

help: ## Show this help message
	@echo ""
	@echo "Venti AI Platform — available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""

# -----------------------------------------------------------------------------
# First-time setup
# -----------------------------------------------------------------------------

setup: env-check multica-clone ## Full first-time setup (run this first)
	@echo ""
	@echo "Setup complete. Next steps:"
	@echo "  1. make phoenix-up         — start Phoenix"
	@echo "  2. make multica-up         — start Multica self-hosted server"
	@echo "  3. make multica-cli-setup  — configure the CLI and start the daemon"
	@echo "  4. make demo               — run the Phoenix tracing demo"
	@echo ""

env-check: ## Check that .env exists (copies .env.example if missing)
	@if [ ! -f "$(ENV_FILE)" ]; then \
		cp .env.example $(ENV_FILE); \
		echo "Created .env from .env.example — please fill in your ANTHROPIC_API_KEY"; \
	else \
		echo ".env already exists"; \
	fi

multica-clone: ## Clone the Multica server repo (skips if already cloned)
	@if [ ! -d "$(MULTICA_DIR)" ]; then \
		echo "Cloning Multica server..."; \
		git clone https://github.com/multica-ai/multica.git $(MULTICA_DIR); \
		echo "Multica server cloned to ./$(MULTICA_DIR)"; \
	else \
		echo "$(MULTICA_DIR) already exists, skipping clone"; \
	fi

# -----------------------------------------------------------------------------
# Phoenix
# -----------------------------------------------------------------------------

phoenix-up: ## Start Phoenix + its database (detached)
	@echo "Starting Phoenix..."
	docker compose -f docker-compose.phoenix.yml --env-file $(ENV_FILE) up -d
	@echo ""
	@echo "Phoenix is starting. Once healthy:"
	@echo "  Web UI:       http://localhost:6006"
	@echo "  OTLP gRPC:    http://localhost:4317"
	@echo "  OTLP HTTP:    http://localhost:4318"
	@echo ""
	@echo "Waiting for Phoenix to be ready..."
	@until docker exec phoenix curl -sf http://localhost:6006/healthz > /dev/null 2>&1; do \
		printf '.'; sleep 2; \
	done
	@echo ""
	@echo "Phoenix is ready."

phoenix-down: ## Stop Phoenix and its database
	docker compose -f docker-compose.phoenix.yml down

phoenix-logs: ## Follow Phoenix logs
	docker compose -f docker-compose.phoenix.yml logs -f phoenix

phoenix-status: ## Show Phoenix container status
	docker compose -f docker-compose.phoenix.yml ps

# -----------------------------------------------------------------------------
# Multica
# -----------------------------------------------------------------------------

multica-up: multica-clone ## Start Multica self-hosted server
	@echo "Starting Multica server..."
	cd $(MULTICA_DIR) && make selfhost
	@echo ""
	@echo "Multica is running:"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8080"

multica-down: ## Stop Multica server
	@if [ -d "$(MULTICA_DIR)" ]; then \
		cd $(MULTICA_DIR) && docker compose -f docker-compose.selfhost.yml down; \
	else \
		echo "$(MULTICA_DIR) not found — nothing to stop"; \
	fi

multica-logs: ## Follow Multica backend logs
	cd $(MULTICA_DIR) && docker compose -f docker-compose.selfhost.yml logs -f backend

multica-cli-setup: ## Configure Multica CLI to point at local server and start daemon
	multica setup self-host

# -----------------------------------------------------------------------------
# Demo
# -----------------------------------------------------------------------------

demo: ## Run the Phoenix tracing demo (requires .env with ANTHROPIC_API_KEY)
	@echo "Running Phoenix tracing demo..."
	cd demo && pip install -q -r requirements.txt && python demo.py
	@echo ""
	@echo "View traces at: http://localhost:6006"

demo-install: ## Install demo Python dependencies only
	cd demo && pip install -r requirements.txt

# -----------------------------------------------------------------------------
# Utility
# -----------------------------------------------------------------------------

up: phoenix-up multica-up ## Start everything (Phoenix + Multica)

down: phoenix-down multica-down ## Stop everything

clean: ## Remove cloned Multica server directory (does not remove Docker volumes)
	@echo "Removing $(MULTICA_DIR)..."
	rm -rf $(MULTICA_DIR)
	@echo "Done. Docker volumes are preserved (run 'docker volume prune' to remove them)."

status: ## Show status of all running containers
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "phoenix|multica|postgres" || echo "No platform containers running."
