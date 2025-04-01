# Load environment variables from .env.local
include .env.local
export

# Set shell to bash
SHELL := /bin/bash

# Detach for background docker
DETACH ?= 0

# Terminal colors
RED := \033[0;31m
GREEN := \033[0;32m
NC := \033[0m

# Required env vars
REQUIRED_ENV_VARS := NVIDIA_API_KEY

# Paths
FRONTEND_DIR := frontend
COMPOSE_FILE := deploy/compose/docker-compose.yaml

# Check environment variables
check_env:
	@for var in $(REQUIRED_ENV_VARS); do \
		if [ -z "$$(eval echo "\$$$${var}")" ]; then \
			echo "$(RED)✗ $$var is not set$(NC)"; \
			exit 1; \
		else \
			echo "$(GREEN)✓ $$var is set$(NC)"; \
		fi \
	done

# Setting up the dependencies 
setup:
	@echo "$(GREEN)Running setup.sh...$(NC)"
	chmod +x setup.sh
	./setup.sh


# Install frontend dependencies
frontend-install:
	@echo "$(GREEN)Installing frontend dependencies...$(NC)"
	cd $(FRONTEND_DIR) && npm install

# Start frontend in development mode
frontend-dev:
	cd $(FRONTEND_DIR) && npm run dev

# Run all services (frontend + backend)
all-services: check_env frontend-install
	@echo "$(GREEN)Starting all containers (frontend + backend)...$(NC)"
	@if [ "$(DETACH)" = "1" ]; then \
		docker compose -f $(COMPOSE_FILE) --env-file .env.local up --build -d; \
	else \
		docker compose -f $(COMPOSE_FILE) --env-file .env.local up --build; \
	fi

# Clean all containers + volumes
clean:
	docker compose -f $(COMPOSE_FILE) down -v

.PHONY: check_env all-services clean frontend-install frontend-dev
