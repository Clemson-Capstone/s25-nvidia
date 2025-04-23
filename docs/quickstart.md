# Quick Start

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
  1. export the following environment variables:
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
        export ENABLE_GUARDRAILS=true
        export DEFAULT_CONFIG=nemoguard_cloud
        export NIM_ENDPOINT_URL=https://integrate.api.nvidia.com/v1
        ```
   **Tip**: If you plan to switch to on-prem models after trying out the NVIDIA hosted models, make sure the above environment variables are `unset` before trying out the pipeline, with the exception of `ENABLE_GUARDRAILS`. If you intend to use guardrails on prem that variable still should be set. 

   2. Start all containers from the repo root:
        ```bash
        docker compose -f deploy/compose/docker-compose.yaml up -d
        ```

   **Tip**: Add `--build` if you've made code changes:
    ```bash
    docker compose -f deploy/compose/docker-compose.yaml up -d --build
    ```

   To confirm all containers are running, run the following command:

   ```bash
   docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```

   *Example Output*
   ```
    CONTAINER ID   NAMES                            STATUS
    dee4a9b3e9eb   rag-playground                   Up 2 minutes
    300b82db1cd5   rag-server                       Up 2 minutes
    c4ea7ae570f8   nemo-guardrails-microservice     Up 2 minutes (healthy)
    d0a5a060e61e   ingestor-server                  Up 2 minutes
    3767d780c1ef   milvus-standalone                Up 2 minutes (healthy)
    62ddf5713e9c   prometheus-server                Up 2 minutes
    65f4ca2aacf5   course_manager_api               Up 2 minutes
    ea835fcf9dd2   milvus-etcd                      Up 2 minutes (healthy)
    089ad311d2b3   frontend                         Up 2 minutes
    73180841063e   compose-redis-1                  Up 2 minutes
    f50e32cdec8f   milvus-minio                     Up 2 minutes (healthy)
    5dd5449f614b   compose-nv-ingest-ms-runtime-1   Up 2 minutes (health: starting)
   ```


   **Note:** The Guardrails service sometimes needs to be restarted a couple times to resolve a pip dependency issue. If restarting is not fixing the issue, please go into the guardrails container and run `pip install langchain-nvidia-ai-endpoints` to fix the dependency issue.

   You should be good to go! Visit [localhost:3000](http://localhost:3000) with your browser to use the frontend with the canvas integration and chatbot. Alternatively, you can go to [localhost:8090](http://localhost:8090) to use the RAG Playground and chat without the canvas integration to play around.

### Next Steps
To learn more about how to get a canvas token to paste in, please refer to this [guide](https://community.canvaslms.com/t5/Canvas-Basics-Guide/How-do-I-manage-API-access-tokens-in-my-user-account/ta-p/615312).

# Running Containers Separately
While developing, you may only be making changes to one component of this project. For example, if you are only modifying the course manager API, you may want to only rebuild that one container and leave everything else running.

This section will go over how to run the NVIDIA RAG Blueprint containers separately, then separately build the frontend and course manager api containers.

## NVIDIA rag repo
this repository contains a fork of the NVIDIA rag repo, in folder `nvidia-rag-2.0`. This folder contains all the prexisting code and docs for the rag 2.0 repo. the NVIDIA_rag_fork.md file goes over the only changes made by us. 

rag repo: https://github.com/NVIDIA-AI-Blueprints/rag/

repo at time of writing(April 22, 2025) in case of changes: https://github.com/NVIDIA-AI-Blueprints/rag/tree/c51ff5be36b755fe21a98a2a5155f9b943bf9d93

1. cd into the rag 2.0 folder:
   ```bash
   cd nvidia-rag-2.0
   ```
3. Start the vector database containers from the rag root:

   ```bash
   docker compose -f deploy/compose/vectordb.yaml up -d
   ```

4. Start the ingestion containers from the rag root:

   ```bash
   docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d
   ```

   **Tip**: Add `--build` if you've made code changes:
   ```bash
   docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d --build
   ```
5. Start the rag containers from the rag root. This pulls the prebuilt containers from NGC and deploys it on your system.
    ```bash
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
   ```

   **Tip**: Add `--build` if you've made code changes:
   ```bash
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d --build
   ```
    You can check the status of the rag-server and its dependencies by issuing this curl command

    ```bash
    curl -X 'GET' 'http://workstation_ip:8081/v1/health?check_dependencies=true' -H 'accept: application/json'
    ```
   
6. Set up the guardrails container to use guardrails

    These are the environment variables to set for guardrails. They were in the big block of export commands above, but are here again for clarity.
    ```bash
    export ENABLE_GUARDRAILS=true
    export DEFAULT_CONFIG=nemoguard_cloud # or nemoguard for on-prem
    export NIM_ENDPOINT_URL=https://integrate.api.nvidia.com/v1
    ```

    deploy the guardrails service from the rag root:

    ```bash
    docker compose -f deploy/compose/docker-compose-nemo-guardrails.yaml up -d --no-deps nemo-guardrails-microservice
    ```

    If the container doesn't start automatically or starts and then fails, manually restart it a few times.  
    Alternatively, install the required packages locally and restart on Docker Desktop:

    ```bash
    pip install langchain-nvidia-ai-endpoints
    pip install langchain-unstructured
    ```

    7. Confirm all containers are running so far:

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
    Congrats! The NVIDIA RAG Blueprint is now running! Now we can move on to adding the custom frontend and canvas integration on top. You can visit [localhost:8090](http://localhost:8090) to use the RAG Playground and chat without the canvas integration to play around at this stage.

### Canvas Integration
Now you will cd back out to the repo root and run the following commands to set up the frontend and canvas integration.
1. cd out to the repo root:
   ```bash
   cd ..
   ```

2. Build the canvas course manager api container:
    ```bash
    docker compose -f deploy/compose/course-manager.yaml up -d
    ```

    **Tip**: Add `--build` if you've made code changes:
    ```bash
    docker compose -f deploy/compose/course-manager.yaml up -d --build
    ```

    You can confirm the course manager api is running by visiting [localhost:8012/metrics](http://localhost:8012/metrics) in your browser. If you see the metrics, then the course manager api is running!

### Frontend
You can either run the frontend locally for development or build the docker image and run it in a container. For testing purposes, running locally is recommended. Deployment is the only time you will likely need to build the docker image.

#### Running Locally

1. Starting from the repo root, cd into the frontend folder:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm i --legacy-peer-deps
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) with your browser to see the application.

#### Building in a container for Production

This application includes a multi-stage Dockerfile to optimize build and runtime performance. Run the following command to build the docker image:

```bash
docker compose -f deploy/compose/frontend.yaml up -d
```

**Tip**: Add `--build` if you've made code changes:
```bash
docker compose -f deploy/compose/frontend.yaml up -d --build
```

## Backend Dependencies

The frontend expects the following backend services to be running:

- RAG Server at http://localhost:8081
- Ingestion Server at http://localhost:8082
- Course Manager API at http://localhost:8012

And there you have it! at this point the application should be fully functional, and you can rebuild containers as needed for development.

## Deploy with On-Premises Models

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