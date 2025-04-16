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

# Install shared package in editable mode (optional)
if [ -d "shared" ]; then
    echo -e "${GREEN}Installing editable shared/ package...${NC}"
    uv pip install -e shared/
fi

echo -e "${GREEN} UV environment setup complete!${NC}"
