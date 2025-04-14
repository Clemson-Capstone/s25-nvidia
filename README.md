# VTA Blueprint

## License and Attribution

This project is licensed under the [Apache License 2.0](./LICENSE).

### Upstream NVIDIA Dependencies

This project builds upon and integrates components from the [NVIDIA RAG Blueprint v2.0.0](https://github.com/NVIDIA-AI-Blueprints/rag), which is licensed under the Apache License 2.0. Portions of the original RAG blueprint are located under the `foundational-rag/` directory.

Additionally, this project uses the [`nemoguardrails`](https://github.com/NVIDIA/NeMo-Guardrails) Python package (v0.11.0), also licensed under Apache License 2.0, to provide guardrail functionality for chatbot safety and control.

All original and modified content is redistributed in compliance with the terms of the Apache License 2.0.

## Introduction

Everything is run via docker containers, with docker compose.

### Folder Structure
- `course_manager_api`: A single container for the Course Manager API. This is an API that allows you to download courses from Canvas and store them locally.
- `deploy/compose`: Docker Compose files for running the application
- `foundational-rag`: Foundational RAG application from NVIDIA that has containers:
   - rag-server
   - rag-playground
   - milvus-standalone
   - milvus-etcd
   - milvus-minio
- `prometheus`: Singular container for Prometheus service for monitoring
- `frontend`: Singular container with Next.js frontend for the application

## Obtain an API Key

You need to obtain a single API key for accessing NIM services, to pull models on-prem, or to access models hosted in the NVIDIA API Catalog.
Use one of the following methods to generate an API key:

- **NVIDIA Build Portal**:
  1. Sign in to the [NVIDIA Build](https://build.nvidia.com/explore/discover?signin=true) portal with your email.
  2. Click any [model](https://build.nvidia.com/meta/llama-3_1-70b-instruct), then click **Get API Key**, and finally click **Generate Key**.

- **NVIDIA NGC Portal**:
  1. Sign in to the [NVIDIA NGC](https://ngc.nvidia.com/) portal with your email.
  2. Select your organization from the dropdown menu after logging in. You must select an organization which has NVIDIA AI Enterprise (NVAIE) enabled.
  3. Click your account in the top right, and then select **Setup**.
  4. Click **Generate Personal Key**, and then click **+ Generate Personal Key** to create your API key.

## Common Prerequisites

1. Export your NVIDIA API key as an environment variable:

   ```bash
   export NVIDIA_API_KEY="nvapi-..."
   ```

2. Authenticate Docker with NGC:

   ```bash
   echo "${NVIDIA_API_KEY}" | docker login nvcr.io -u '$oauthtoken' --password-stdin
   ```



## Deploy With Docker Compose

Use these procedures to deploy with Docker Compose for a single node deployment.

### Prerequisites

1. Verify that you meet the [common prerequisites](#common-prerequisites).

2. Install Docker Engine. For more information, see [Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

3. Install Docker Compose. For more information, see [install the Compose plugin](https://docs.docker.com/compose/install/linux/).

   a. Ensure the Docker Compose plugin version is 2.29.1 or later.

   b. After you get the Docker Compose plugin installed, run `docker compose version` to confirm.

4. (Optional) You can run some containers with GPU acceleration, such as Milvus and NVIDIA NIMS deployed on-prem. To configure Docker for GPU-accelerated containers, [install](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html), the NVIDIA Container Toolkit, and ensure you meet [the hardware requirements](../README.md#hardware-requirements).

5. (Optional) You can enable GPU acceleration for the Milvus vector database container, if you have at least one L40/A100/H100 GPU available. For more information, see [Configuring Milvus with GPU Acceleration](./vector-database.md#configuring-milvus-with-gpu-acceleration).

### Option 1: Deploy with NVIDIA Hosted Models (Recommended)

This is the recommended deployment option using your NVIDIA API key to access cloud-hosted models.


1. Verify that you meet the prerequisites & cd into the correct directory nvidia-rag-2.0

2. Set the endpoint URLs for the NIMs:

   ```bash
   export APP_EMBEDDINGS_SERVERURL=""
   export APP_LLM_SERVERURL=""
   export APP_RANKING_SERVERURL=""
   export EMBEDDING_NIM_ENDPOINT="https://integrate.api.nvidia.com/v1"
   export PADDLE_HTTP_ENDPOINT="https://ai.api.nvidia.com/v1/cv/baidu/paddleocr"
   export PADDLE_INFER_PROTOCOL="http"
   export YOLOX_HTTP_ENDPOINT="https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-page-elements-v2"
   export YOLOX_INFER_PROTOCOL="http"
   export YOLOX_GRAPHIC_ELEMENTS_HTTP_ENDPOINT="https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-graphic-elements-v1"
   export YOLOX_GRAPHIC_ELEMENTS_INFER_PROTOCOL="http"
   export YOLOX_TABLE_STRUCTURE_HTTP_ENDPOINT="https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-table-structure-v1"
   export YOLOX_TABLE_STRUCTURE_INFER_PROTOCOL="http"
   ```

   **Tip**: If you plan to switch to on-prem models after trying out the NVIDIA hosted models, make sure the above environment variables are `unset` before trying out the pipeline.

3. Start the vector database containers from the repo root:

   ```bash
   docker compose -f deploy/compose/vectordb.yaml up -d
   ```

4. Start the ingestion containers from the repo root:

   ```bash
   docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d
   ```

   **Tip**: Add `--build` if you've made code changes:
   ```bash
   docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d --build
   ```

5. Set up the guardrails container to use guardrails

Set the environment variables for the guardrails
```bash
export DEFAULT_CONFIG=nemoguard_cloud
export NIM_ENDPOINT_URL=https://integrate.api.nvidia.com/v1
```

Run the `make` command to start the Guardrails service:

```bash
make guardrails-build
```

If the container doesn't start automatically or starts and then fails, manually restart it a few times.  
Alternatively, install the required packages locally and restart on Docker Desktop:

```bash
pip install langchain-nvidia-ai-endpoints
pip install langchain-unstructured
```
6. Start the Nemoguard Rails container from the repo root:

Make sure to set up the guardrails microservice:

For cloud deployment using NVIDIA-hosted models instead of the default self-hosted deployment:

```bash
export DEFAULT_CONFIG=nemoguard_cloud
export NIM_ENDPOINT_URL=https://integrate.api.nvidia.com/v1
```

Run the make command to start the guardrails service
```bash
make guardrails-build
```

If the container doesn't start automatically or starts and then fails, manually restart it a few times. Alternatively, you can install the required packages locally & then restart on docker desktop:

```bash
pip install langchain-nvidia-ai-endpoints
pip install langchain-unstructured
```
6. Confirm all containers are running:

   ```bash
   docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```

   *Example Output*
   ```
   NAMES                                   STATUS
   compose-nv-ingest-ms-runtime-1          Up 5 minutes (healthy)
   ingestor-server                         Up 5 minutes
   compose-redis-1                         Up 5 minutes
   rag-playground                          Up 9 minutes
   rag-server                              Up 9 minutes
   milvus-standalone                       Up 36 minutes
   milvus-minio                            Up 35 minutes (healthy)
   milvus-etcd                             Up 35 minutes (healthy)
   nemo-guardrails-microservice            Up 5 minutes
   ```

7. Open a web browser and access `http://localhost:8090` to use the RAG Playground, or go to `http://localhost:3000` to use the frontend for the canvas application. The RAG playground is more for testing the chatbot, and the frontend is for the canvas integration with the chatbot.

### Option 2: Deploy with On-Premises Models

1. Create a directory to cache the models and export the path as an environment variable:

   ```bash
   mkdir -p ~/.cache/model-cache
   export MODEL_DIRECTORY=~/.cache/model-cache
   ```

2. Start all required NIMs:

   ```bash
   USERID=$(id -u) docker compose -f deploy/compose/nims.yaml up -d
   ```

   Wait until the nemoretriever-ranking-ms, nemoretriever-embedding-ms, and nim-llm-ms NIMs are in a healthy state before proceeding. The nemo LLM service may take up to 30 mins to start for the first time as the model is downloaded and cached.

   **Note for A100 users**: If deploying on A100, allocate 4 available GPUs:
   ```bash
   export LLM_MS_GPU_ID=2,3,4,5
   ```

3. Start the vector database containers:

   ```bash
   docker compose -f deploy/compose/vectordb.yaml up -d
   ```

4. Start the ingestion containers:

   ```bash
   docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d
   ```

5. Start the RAG containers:

   ```bash
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
   ```

### Health Check

You can check the status of the rag-server and its dependencies with:

```bash
curl -X 'GET' 'http://localhost:8081/v1/health?check_dependencies=true' -H 'accept: application/json'
```
