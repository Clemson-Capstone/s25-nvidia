# Docker RAG System Makefile
# This Makefile simplifies container management for the RAG system
# NOTE: Image captioning is a required feature for this system

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

# Required image captioning configuration variables
define IMAGE_CAPTION_CONFIG
APP_NVINGEST_EXTRACTIMAGES=True
VLM_CAPTION_ENDPOINT=https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions
VLM_CAPTION_MODEL_NAME=meta/llama-3.2-11b-vision-instruct
# Do not use the vlm-ms service as it doesn't exist
VLM_USE_LOCAL_SERVICE=False
endef
export IMAGE_CAPTION_CONFIG

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
	@echo "  make config-captions   - Configure required image captioning settings"
	@echo "  make vectordb          - Start vector database containers"
	@echo "  make ingestor          - Start ingestion containers (using prebuilt images)"
	@echo "  make ingestor-build    - Start ingestion containers (with rebuild)"
	@echo "  make restart-ingestor  - Restart ingestion containers with cloud image captioning"
	@echo "  make fix-captions      - Fix image captioning by rebuilding with direct environment variables"
	@echo "  make ragserver         - Start RAG server containers (using prebuilt images)"
	@echo "  make ragserver-build   - Start RAG server containers (with rebuild)"
	@echo "  make guardrails        - Start only the guardrails microservice"
	@echo "  make guardrails-build  - Start guardrails microservice with rebuild"
	@echo "  make all               - Start all components (vectordb, ingestor, ragserver) with captioning"
	@echo "  make all-build         - Start all components with rebuilding containers and captioning"
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

# Configure image captioning (required)
.PHONY: config-captions
config-captions:
	@echo "Configuring required image captioning functionality..."
	@echo "$$IMAGE_CAPTION_CONFIG" | while IFS= read -r line; do \
		if [ -n "$$line" ]; then \
			export_line="export $$line"; \
			echo "$$export_line"; \
			eval "$$export_line"; \
		fi; \
	done
	@echo "Image captioning configuration applied successfully!"
	@echo ""
	@echo "NOTE: Using the cloud-hosted VLM model for image captioning"
	@echo "Endpoint: $${VLM_CAPTION_ENDPOINT}"
	@echo "Model name: $${VLM_CAPTION_MODEL_NAME}"

# Start vector database containers
.PHONY: vectordb
vectordb:
	@echo "Starting vector database containers..."
	docker compose -f deploy/compose/vectordb.yaml up -d

# Start ingestion containers (with image captioning)
.PHONY: ingestor
ingestor: config-captions
	@echo "Starting ingestion containers with image captioning..."
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d

# Start ingestion containers with rebuild (with image captioning)
.PHONY: ingestor-build
ingestor-build: config-captions
	@echo "Starting ingestion containers with rebuild and image captioning..."
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d --build

# Restart just the ingestor service with image captioning config
.PHONY: restart-ingestor
restart-ingestor: config-captions
	@echo "Restarting ingestion containers with cloud image captioning..."
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml down
	@echo "Setting environment variables explicitly..."
	export APP_NVINGEST_EXTRACTIMAGES=True && \
	export VLM_CAPTION_ENDPOINT="https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions" && \
	export VLM_CAPTION_MODEL_NAME="meta/llama-3.2-11b-vision-instruct" && \
	export VLM_USE_LOCAL_SERVICE=False && \
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d
	@echo "Ingestion service restarted with cloud image captioning!"
	@echo "ENV VARS: APP_NVINGEST_EXTRACTIMAGES=True"
	@echo "ENV VARS: VLM_CAPTION_ENDPOINT=https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions"
	@echo "ENV VARS: VLM_CAPTION_MODEL_NAME=meta/llama-3.2-11b-vision-instruct"
	@echo "ENV VARS: VLM_USE_LOCAL_SERVICE=False"

# Rebuild and restart ingestor service with direct environment variables for cloud model
.PHONY: fix-captions
fix-captions:
	@echo "Rebuilding and restarting ingestion containers with direct environment variables..."
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml down
	@echo "Creating Docker command with direct environment variables..."
	APP_NVINGEST_EXTRACTIMAGES=True \
	APP_NVINGEST_CAPTIONMODELNAME="meta/llama-3.2-11b-vision-instruct" \
	APP_NVINGEST_CAPTIONENDPOINTURL="https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions" \
	VLM_CAPTION_ENDPOINT="https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions" \
	VLM_CAPTION_MODEL_NAME="meta/llama-3.2-11b-vision-instruct" \
	VLM_USE_LOCAL_SERVICE=False \
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d --build
	@echo "Ingestion service rebuilt and restarted with direct environment variables!"
	@echo ""
	@echo "If this does not fix the issue, you may need to edit the Docker Compose file directly:"
	@echo "1. Open deploy/compose/docker-compose-ingestor-server.yaml"
	@echo "2. Change 'VLM_CAPTION_ENDPOINT: \$${VLM_CAPTION_ENDPOINT:-http://vlm-ms:8000/v1/chat/completions}' to"
	@echo "   'VLM_CAPTION_ENDPOINT: https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions'"
	@echo "3. Make the same change for APP_NVINGEST_CAPTIONENDPOINTURL"
	@echo "4. Set APP_NVINGEST_EXTRACTIMAGES: 'True' (not False)"

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

# Start all components (with image captioning)
.PHONY: all
all: config-captions vectordb ingestor ragserver
	@echo "All components started successfully with image captioning enabled!"

# Start all components with rebuilding (with image captioning)
.PHONY: all-build
all-build: config-captions vectordb ingestor-build ragserver-build
	@echo "All components started with rebuild successfully and image captioning enabled!"

# Stop all containers
.PHONY: stop-all
stop-all:
	@echo "Stopping all containers..."
	docker compose -f deploy/compose/vectordb.yaml down
	docker compose -f deploy/compose/docker-compose-ingestor-server.yaml down
	docker compose -f deploy/compose/docker-compose-rag-server.yaml down
	docker compose -f deploy/compose/docker-compose-nemo-guardrails.yaml down
	@echo "All containers stopped successfully!"
