#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m'

# Install npm if not already installed for frontend
echo -e "${GREEN}Setting up frontend dependencies...${NC}"
if command -v npm &> /dev/null; then
    cd ./frontend && npm install
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${RED}✗ npm not found. Please install Node.js & npm to set up frontend.${NC}"
fi

echo -e "${GREEN} UV environment setup complete!${NC}"


# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo -e "${GREEN}Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment using uv
echo -e "${GREEN}Creating virtual environment...${NC}"
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install the three main requirements files
echo -e "${GREEN}Installing requirements from key components...${NC}"
uv pip install -r nvidia-rag-2.0/requirements.txt
uv pip install -r course_manager_api/requirements.txt
uv pip install -r nvidia-rag-2.0/src/ingestor_server/requirements.txt

# For canvas API
uv pip install fastapi==0.115.2 uvicorn==0.32.0 pydantic==2.9.2 python-multipart==0.0.20 \
    requests==2.32.3 aiohttp==3.11.16 certifi==2025.1.31 \
    prometheus-client==0.21.1 prometheus-fastapi-instrumentator==7.1.0

#For nvidia-rag-2.0 reqs
uv pip install bleach==6.2.0 \
    dataclass-wizard==0.27.0 \
    fastapi==0.115.5 \
    langchain-core==0.3.18 \
    langchain-nvidia-ai-endpoints==0.3.7 \
    langchain-openai==0.2.8 \
    langchain==0.3.7 \
    langchain-community==0.3.7 \
    pymilvus==2.5.4 \
    python-multipart==0.0.18 \
    "unstructured[all-docs]==0.16.11" \
    "uvicorn[standard]==0.32.0" \
    pydantic==2.9.2 \
    PyYAML==6.0.2 \
    langchain-milvus==0.1.8 \
    minio==7.2.15 \
    opentelemetry-api==1.29.0 \
    opentelemetry-sdk==1.29.0 \
    opentelemetry-instrumentation==0.50b0 \
    opentelemetry-exporter-otlp==1.29.0 \
    opentelemetry-exporter-prometheus==0.50b0 \
    opentelemetry-instrumentation-milvus==0.36.0 \
    opentelemetry-instrumentation-fastapi==0.50b0 \
    opentelemetry-processor-baggage==0.50b0 \
    "nemoguardrails[embeddings]==0.11.0"
# Install shared package in editable mode (optional)
if [ -d "shared" ]; then
    echo -e "${GREEN}Installing editable shared/ package...${NC}"
    uv pip install -e shared/
fi

echo -e "${GREEN} UV environment setup complete!${NC}"
