# Docker RAG System Makefile
# This Makefile simplifies container management for the RAG system

# Environment variables for NIMs
define ENV_VARS
APP_EMBEDDINGS_SERVERURL=
APP_LLM_SERVERURL=
APP_RANKING_SERVERURL=
EMBEDDING_NIM_ENDPOINT=https://integrate.api.nvidia.com/v1
PADDLE_HTTP_ENDPOINT=https://ai.api.nvidia.com/v1/cv/baidu/paddleocr
PADDLE_INFER_PROTOCOL=http
YOLOX_HTTP_ENDPOINT=https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-page-elements-v2
YOLOX_INFER_PROTOCOL=http
YOLOX_GRAPHIC_ELEMENTS_HTTP_ENDPOINT=https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-graphic-elements-v1
YOLOX_GRAPHIC_ELEMENTS_INFER_PROTOCOL=http
YOLOX_TABLE_STRUCTURE_HTTP_ENDPOINT=https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-table-structure-v1
YOLOX_TABLE_STRUCTURE_INFER_PROTOCOL=http
endef
export ENV_VARS

# Cloud configuration variables
define CLOUD_CONFIG
DEFAULT_CONFIG=nemoguard_cloud
NIM_ENDPOINT_URL=https://integrate.api.nvidia.com/v1
endef
export CLOUD_CONFIG

# Helper function to print available commands
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make env-export        - Export all NIM endpoint environment variables"
	@echo "  make env-unset         - Unset all NIM endpoint environment variables (for on-prem models)"
	@echo "  make cloud-config      - Set configuration for cloud deployment"
	@echo "  make vectordb          - Start vector database containers"
	@echo "  make ingestor          - Start ingestion containers (using prebuilt images)"
	@echo "  make ingestor-build    - Start ingestion containers (with rebuild)"
	@echo "  make ragserver         - Start RAG server containers (using prebuilt images)"
	@echo "  make ragserver-build   - Start RAG server containers (with rebuild)"
	@echo "  make guardrails        - Start only the guardrails microservice"
	@echo "  make guardrails-build  - Start guardrails microservice with rebuild"
	@echo "  make all               - Start all components (vectordb, ingestor, ragserver)"
	@echo "  make all-build         - Start all components with rebuilding containers"
	@echo "  make stop-all          - Stop all running containers"

# Export environment variables
.PHONY: env-export
env-export:
	@echo "Exporting environment variables for NIMs..."
	@echo "$$ENV_VARS" | while IFS= read -r line; do \
		if [ -n "$$line" ]; then \
			export_line="export $$line"; \
			echo "$$export_line"; \
			eval "$$export_line"; \
		fi; \
	done

# Unset environment variables
.PHONY: env-unset
env-unset:
	@echo "Unsetting environment variables for on-prem models..."
	@echo "$$ENV_VARS" | while IFS= read -r line; do \
		if [ -n "$$line" ]; then \
			var=$$(echo "$$line" | cut -d= -f1); \
			echo "unset $$var"; \
			unset "$$var"; \
		fi; \
	done

# Set cloud configuration
.PHONY: cloud-config
cloud-config:
	@echo "Setting cloud configuration..."
	@echo "$$CLOUD_CONFIG" | while IFS= read -r line; do \
		if [ -n "$$line" ]; then \
			export_line="export $$line"; \
			echo "$$export_line"; \
			eval "$$export_line"; \
		fi; \
	done

# Start vector database containers
.PHONY: vectordb
vectordb:
	@echo "Starting vector database containers..."
	docker compose -f deploy/compose/vectordb.yaml up -d

# Start ingestion containers
.PHONY: ingestor
ingestor:
	@echo "Starting ingestion containers..."
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d

# Start ingestion containers with rebuild
.PHONY: ingestor-build
ingestor-build:
	@echo "Starting ingestion containers with rebuild..."
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d --build

# Start RAG server containers
.PHONY: ragserver
ragserver:
	@echo "Starting RAG server containers..."
	docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d

# Start RAG server containers with rebuild
.PHONY: ragserver-build
ragserver-build:
	@echo "Starting RAG server containers with rebuild..."
	docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d --build

# Start guardrails microservice only
.PHONY: guardrails
guardrails:
	@echo "Starting guardrails microservice..."
	docker compose -f deploy/compose/docker-compose-nemo-guardrails.yaml up -d --no-deps nemo-guardrails-microservice

# Start guardrails microservice with rebuild
.PHONY: guardrails-build
guardrails-build:
	@echo "Starting guardrails microservice with rebuild..."
	docker compose -f deploy/compose/docker-compose-nemo-guardrails.yaml up -d --no-deps --build nemo-guardrails-microservice

# Start all components
.PHONY: all
all: vectordb ingestor ragserver
	@echo "All components started successfully!"

# Start all components with rebuilding
.PHONY: all-build
all-build: vectordb ingestor-build ragserver-build
	@echo "All components started with rebuild successfully!"

# Stop all containers
.PHONY: stop-all
stop-all:
	@echo "Stopping all containers..."
	docker compose -f deploy/compose/vectordb.yaml down
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml down
	docker compose -f deploy/compose/docker-compose-rag-server.yaml down
	docker compose -f deploy/compose/docker-compose-nemo-guardrails.yaml down
	@echo "All containers stopped successfully!"
