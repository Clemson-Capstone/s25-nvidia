# S25 NVIDIA RAG System Makefile

# Include environment variables
-include .env
export

# Colors for terminal output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m  # No Color

# Detach flag for Docker containers
DETACH ?= 0

# Shell configuration
SHELL := /bin/bash

REQUIRED_ENV_VARS := NVIDIA_API_KEY MAX_CONCURRENT_REQUESTS

# Path configurations
RAG_PATH := ./nvidia-rag-2.0
FRONTEND_PATH := ./frontend
COURSE_API_PATH := ./course_manager_api

# Helper function to print available commands
.PHONY: help
help:
	@echo "$(GREEN)S25-NVIDIA RAG System Makefile$(NC)"
	@echo "$(YELLOW)================================================$(NC)"
	@echo "$(BLUE)Backend Commands:$(NC)"
	@echo "  $(GREEN)make setup$(NC)       - Install dependencies and prepare environment"
	@echo "  $(GREEN)make cloud$(NC)       - Run NVIDIA RAG system with cloud NIMs"
	@echo "  $(GREEN)make onprem$(NC)      - Run NVIDIA RAG system with on-prem NIMs"
	@echo "  $(GREEN)make onprem-nims$(NC) - Start just the on-prem NIMs"
	@echo "  $(GREEN)make vectordb$(NC)    - Start just the vector database"
	@echo "  $(GREEN)make ingest$(NC)      - Start just the ingestion service"
	@echo "  $(GREEN)make server$(NC)      - Start just the RAG server"
	@echo ""
	@echo "$(BLUE)Frontend Commands:$(NC)"
	@echo "  $(GREEN)make frontend-setup$(NC)   - Install frontend dependencies"
	@echo "  $(GREEN)make frontend-start$(NC)   - Start the frontend application"
	@echo "  $(GREEN)make api-setup$(NC)        - Setup course manager API dependencies"
	@echo "  $(GREEN)make api-start$(NC)        - Start the course manager API"
	@echo ""
	@echo "$(BLUE)Combined Commands:$(NC)"
	@echo "  $(GREEN)make all$(NC)          - Setup and start everything (backend and frontend)"
	@echo "  $(GREEN)make stop$(NC)         - Stop all running containers"
	@echo "  $(GREEN)make clean$(NC)        - Clean up all containers and volumes"
	@echo "  $(GREEN)make status$(NC)       - Check status of deployed services"



check_env:
	@for var in $(REQUIRED_ENV_VARS); do \
		if [ -z "$$(eval echo "\$$$$var")" ]; then \
			echo "$(RED)Error: $$var is not set$(NC)"; \
			echo "Please set required environment variables:"; \
			echo "  export $$var=<value>"; \
			exit 1; \
		else \
			echo "$(GREEN)✓ $$var is set$(NC)"; \
		fi \
	done

# Use uv to set up Python environment and install dependencies
.PHONY: setup
setup:
	@echo "$(GREEN)Running UV-based setup...$(NC)"
	@bash ./setup.sh

# Run NVIDIA RAG system with cloud NIMs
.PHONY: cloud
cloud:
	@echo "$(GREEN)Starting NVIDIA RAG system with cloud NIMs...$(NC)"
	@echo "$(YELLOW)Setting up cloud environment variables...$(NC)"
	export APP_EMBEDDINGS_SERVERURL= && \
	export APP_LLM_SERVERURL= && \
	export APP_RANKING_SERVERURL= && \
	export EMBEDDING_NIM_ENDPOINT=https://integrate.api.nvidia.com/v1 && \
	export PADDLE_HTTP_ENDPOINT=https://ai.api.nvidia.com/v1/cv/baidu/paddleocr && \
	export PADDLE_INFER_PROTOCOL=http && \
	export YOLOX_HTTP_ENDPOINT=https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-page-elements-v2 && \
	export YOLOX_INFER_PROTOCOL=http && \
	export YOLOX_GRAPHIC_ELEMENTS_HTTP_ENDPOINT=https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-graphic-elements-v1 && \
	export YOLOX_GRAPHIC_ELEMENTS_INFER_PROTOCOL=http && \
	export YOLOX_TABLE_STRUCTURE_HTTP_ENDPOINT=https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-table-structure-v1 && \
	export YOLOX_TABLE_STRUCTURE_INFER_PROTOCOL=http && \
	export APP_NVINGEST_EXTRACTIMAGES=True && \
	export VLM_CAPTION_ENDPOINT=https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions && \
	export VLM_CAPTION_MODEL_NAME=meta/llama-3.2-11b-vision-instruct && \
	export VLM_USE_LOCAL_SERVICE=False && \
	export DEFAULT_CONFIG=nemoguard_cloud && \
	export NIM_ENDPOINT_URL=https://integrate.api.nvidia.com/v1 && \
	cd $(RAG_PATH) && docker compose -f deploy/compose/vectordb.yaml up -d && \
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d && \
	docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
	@echo "$(GREEN)NVIDIA RAG system started in cloud mode!$(NC)"
	@echo "$(YELLOW)Check service status with 'make status'$(NC)"

# Run NVIDIA RAG system with on-prem NIMs
.PHONY: onprem
onprem:
	@echo "$(GREEN)Starting NVIDIA RAG system with on-prem NIMs...$(NC)"
	@echo "$(YELLOW)Setting up model cache...$(NC)"
	export MODEL_DIRECTORY=~/.cache/model-cache && \
	export VECTORSTORE_GPU_DEVICE_ID=0 && \
	export PADDLE_MS_GPU_ID=0 && \
	export YOLOX_TABLE_MS_GPU_ID=0 && \
	export YOLOX_GRAPHICS_MS_GPU_ID=0 && \
	export YOLOX_MS_GPU_ID=0 && \
	export LLM_MS_GPU_ID=2,3 && \
	export RANKING_MS_GPU_ID=1 && \
	export EMBEDDING_MS_GPU_ID=1 && \
	cd $(RAG_PATH) && USERID=$$(id -u) docker compose -f deploy/compose/nims.yaml up -d && \
	docker compose -f deploy/compose/vectordb.yaml up -d && \
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d && \
	docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
	@echo "$(GREEN)NVIDIA RAG system started in on-premises mode!$(NC)"
	@echo "$(YELLOW)Note: First run may take up to 30 minutes as models are downloaded$(NC)"
	@echo "$(YELLOW)Check service status with 'make status'$(NC)"

# Start just the on-prem NIMs
.PHONY: onprem-nims
onprem-nims:
	@echo "$(GREEN)Starting on-prem NIMs...$(NC)"
	export MODEL_DIRECTORY=~/.cache/model-cache && \
	export LLM_MS_GPU_ID=2,3 && \
	export RANKING_MS_GPU_ID=1 && \
	export EMBEDDING_MS_GPU_ID=1 && \
	cd $(RAG_PATH) && USERID=$$(id -u) docker compose -f deploy/compose/nims.yaml up -d
	@echo "$(GREEN)On-prem NIMs started!$(NC)"
	@echo "$(YELLOW)Note: First run may take up to 30 minutes as models are downloaded$(NC)"

# Start just the vector database
.PHONY: vectordb
vectordb:
	@echo "$(GREEN)Starting vector database...$(NC)"
	cd $(RAG_PATH) && docker compose -f deploy/compose/vectordb.yaml up -d
	@echo "$(GREEN)Vector database started!$(NC)"

# Start just the ingestion service
.PHONY: ingest
ingest:
	@echo "$(GREEN)Starting ingestion service...$(NC)"
	cd $(RAG_PATH) && docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d
	@echo "$(GREEN)Ingestion service started!$(NC)"

# Start just the RAG server
.PHONY: server
server:
	@echo "$(GREEN)Starting RAG server...$(NC)"
	cd $(RAG_PATH) && docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
	@echo "$(GREEN)RAG server started!$(NC)"

# Setup frontend dependencies
.PHONY: frontend-setup
frontend-setup:
	@echo "$(GREEN)Setting up frontend dependencies...$(NC)"
	@if [ ! -d "$(FRONTEND_PATH)" ]; then \
		echo "$(RED)Error: Frontend directory not found at $(FRONTEND_PATH)$(NC)"; \
		exit 1; \
	fi
	cd $(FRONTEND_PATH) && npm install
	@echo "$(GREEN)Frontend dependencies installed successfully!$(NC)"

# Start the frontend application (including build step)
.PHONY: frontend-start
frontend-start: frontend-setup
	@echo "$(GREEN)Building and starting the frontend application...$(NC)"
	@if [ ! -d "$(FRONTEND_PATH)" ]; then \
		echo "$(RED)Error: Frontend directory not found at $(FRONTEND_PATH)$(NC)"; \
		exit 1; \
	fi
	cd $(FRONTEND_PATH) && npm run build && npm start
	@echo "$(GREEN)Frontend application started!$(NC)"


# Start the course manager API
.PHONY: api-start
api-start:
	@echo "$(GREEN)Starting the course manager API...$(NC)"
	cd $(COURSE_API_PATH) && python app.py
	@echo "$(GREEN)Course manager API started!$(NC)"

# Setup and start everything
.PHONY: all
all: check_env frontend-setup onprem api-start frontend-start
	@echo "$(GREEN)All components have been set up and started!$(NC)"

# Stop all running containers
.PHONY: stop
stop:
	@echo "$(GREEN)Stopping all containers...$(NC)"
	cd $(RAG_PATH) && docker compose -f deploy/compose/nims.yaml down || true
	cd $(RAG_PATH) && docker compose -f deploy/compose/vectordb.yaml down || true
	cd $(RAG_PATH) && docker compose -f deploy/compose/docker-compose-ingestor-server.yaml down || true
	cd $(RAG_PATH) && docker compose -f deploy/compose/docker-compose-rag-server.yaml down || true
	@echo "$(GREEN)All containers stopped!$(NC)"

# Clean up all containers and volumes
.PHONY: clean
clean: stop
	@echo "$(GREEN)Cleaning up containers and volumes...$(NC)"
	cd $(RAG_PATH) && docker compose -f deploy/compose/nims.yaml down -v || true
	cd $(RAG_PATH) && docker compose -f deploy/compose/vectordb.yaml down -v || true
	cd $(RAG_PATH) && docker compose -f deploy/compose/docker-compose-ingestor-server.yaml down -v || true
	cd $(RAG_PATH) && docker compose -f deploy/compose/docker-compose-rag-server.yaml down -v || true
	@echo "$(GREEN)Cleanup completed!$(NC)"

# Check status of deployed services
.PHONY: status
status:
	@echo "$(GREEN)Checking RAG system status...$(NC)"
	@echo "$(YELLOW)NIMs status:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "nim-llm-ms|nemoretriever-embedding-ms|nemoretriever-ranking-ms|compose-paddle-1|compose-page-elements-1|compose-graphic-elements-1|compose-table-structure-1" || echo "No NIMs found"
	@echo "$(YELLOW)Vector database status:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "milvus-" || echo "No vector database found"
	@echo "$(YELLOW)Ingestion service status:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "ingestor-server" || echo "No ingestion service found"
	@echo "$(YELLOW)RAG server status:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "rag-server|rag-playground" || echo "No RAG server found"
	@echo "$(YELLOW)To check RAG server health:$(NC)"
	@echo "curl -X 'GET' 'http://localhost:8081/v1/health?check_dependencies=true' -H 'accept: application/json'"