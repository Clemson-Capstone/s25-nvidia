.PHONY: setup login deploy status clean frontend-dev frontend-build frontend-start frontend-install

# Load environment variables from .env.local
include .env.local
export

# Default values
DOCKER_COMPOSE_FILE ?= deploy/compose/docker-compose.yaml
ROOT_DIR := $(shell pwd)
FOUNDATIONAL_RAG_DIR := $(ROOT_DIR)/foundational-rag

# Export NVIDIA_API_KEY for docker compose
export NVIDIA_API_KEY

setup: login deploy status

# NGC Login using API key
login:
	@echo "Logging into NGC..."
	@cd $(FOUNDATIONAL_RAG_DIR) && printf "%s" "$(NVIDIA_API_KEY)" | docker login nvcr.io -u '$$oauthtoken' --password-stdin

# Deploy containers
deploy:
	@echo "Deploying containers..."
	@cd $(FOUNDATIONAL_RAG_DIR) && NVIDIA_API_KEY="$(NVIDIA_API_KEY)" docker compose -f $(DOCKER_COMPOSE_FILE) up -d
	@echo "Access the Nvidia RAG Playground at http://localhost:8090"
	@echo ""

# Deploy containers with rebuild
deploy-build:
	@echo "Deploying containers with rebuild..."
	@cd $(FOUNDATIONAL_RAG_DIR) && NVIDIA_API_KEY="$(NVIDIA_API_KEY)" docker compose -f $(DOCKER_COMPOSE_FILE) up -d --build
	@echo "Access the Nvidia RAG Playground at http://localhost:8090"

# Check container status
status:
	@echo "Checking container status..."
	@docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
	@echo "Access the Nvidia RAG Playground at http://localhost:8090"
	@echo ""

# Stop and remove containers
clean:
	@echo "Cleaning up containers..."
	@cd $(FOUNDATIONAL_RAG_DIR) && docker compose -f $(DOCKER_COMPOSE_FILE) down

# Frontend Commands
frontend-install:
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install

frontend-dev:
	@echo "Starting frontend in development mode..."
	@cd frontend && npm run dev

frontend-build:
	@echo "Building frontend..."
	@cd frontend && npm run build

frontend-start:
	@echo "Starting frontend in production mode..."
	@cd frontend && npm run start

# Combined commands
dev: setup frontend-dev

# Help target
help:
	@echo "Available targets:"
	@echo " setup          - Complete setup: login, deploy, and check status"
	@echo " login          - Login to NGC using API key"
	@echo " deploy         - Deploy containers"
	@echo " deploy-build   - Deploy containers with rebuild"
	@echo " status         - Check container status"
	@echo " clean          - Stop and remove containers"
	@echo " frontend-install - Install frontend dependencies"
	@echo " frontend-dev   - Start frontend in development mode"
	@echo " frontend-build - Build frontend for production"
	@echo " frontend-start - Start frontend in production mode"
	@echo " dev           - Deploy backend and start frontend in development mode"