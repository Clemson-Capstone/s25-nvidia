<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Get Started With AI Blueprint: RAG

Use the following documentation to get started with the NVIDIA RAG Blueprint.

- [Obtain an API Key](#obtain-an-api-key)
- [Deploy With Docker Compose](#deploy-with-docker-compose)



## Obtain an API Key

You need to obtain a single API key for accessing NIM services, to pull models on-prem, or to access models hosted in the NVIDIA API Catalog.
Use one of the following methods to generate an API key:

  - Sign in to the [NVIDIA Build](https://build.nvidia.com/explore/discover?signin=true) portal with your email.
    - Click any [model](https://build.nvidia.com/meta/llama-3_1-70b-instruct), then click **Get API Key**, and finally click **Generate Key**.

  - Sign in to the [NVIDIA NGC](https://ngc.nvidia.com/) portal with your email.
    - Select your organization from the dropdown menu after logging in. You must select an organization which has NVIDIA AI Enterprise (NVAIE) enabled.
    - Click your account in the top right, and then select **Setup**.
    - Click **Generate Personal Key**, and then click **+ Generate Personal Key** to create your API key.
      - Later, you use this key in the `NVIDIA_API_KEY` environment variables.

## Common Prerequisites
1. Export your NVIDIA API key as an environment variable. Ensure you followed steps [in previous section](#obtain-an-api-key) to get an API key.

   ```bash
   export NVIDIA_API_KEY="nvapi-..."
   ```


## Deploy With Docker Compose

Use these procedures to deploy with Docker Compose for a single node deployment.


### Prerequisites

1. Verify that you meet the [common prerequisites](#common-prerequisites).

1. Install Docker Engine. For more information, see [Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

1. Install Docker Compose. For more information, see [install the Compose plugin](https://docs.docker.com/compose/install/linux/).

   a. Ensure the Docker Compose plugin version is 2.29.1 or later.

   b. After you get the Docker Compose plugin installed, run `docker compose version` to confirm.

1. To pull images required by the blueprint from NGC, you must first authenticate Docker with NGC. Use the NGC API Key you created in [Obtain an API Key](#obtain-an-api-key).

   ```bash
   export NVIDIA_API_KEY="nvapi-..."
   echo "${NVIDIA_API_KEY}" | docker login nvcr.io -u '$oauthtoken' --password-stdin
   ```

1. (Optional) You can run some containers with GPU acceleration, such as Milvus and NVIDIA NIMS deployed on-prem. To configure Docker for GPU-accelerated containers, [install](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html), the NVIDIA Container Toolkit, and ensure you meet [the hardware requirements](../README.md#hardware-requirements).

1. (Optional) You can enable GPU acceleration for the Milvus vector database container, if you have at least one L40/A100/H100 GPU available. For more information, see [Configuring Milvus with GPU Acceleration](./vector-database.md#configuring-milvus-with-gpu-acceleration).


### Start the Containers using cloud hosted models (no GPU by default)

Use the following procedure to start the containers using cloud-hosted models.

[!IMPORTANT]
To start the containers using on-premises models, use the procedure in the next section instead.

1. Export `NVIDIA_API_KEY` environment variable to pull the containers and models. Check the [Common Prerequisites](#common-prerequisites) section for the same.

1. Start the containers from the repo root. This pulls the prebuilt containers from NGC and deploys it on your system.

   ```bash
   docker compose -f deploy/compose/docker-compose.yaml up -d
   ```

   *Example Output*

   ```output
    ✔ Network nvidia-rag           Created
    ✔ Container rag-playground     Started
    ✔ Container milvus-minio       Started
    ✔ Container rag-server         Started
    ✔ Container milvus-etcd        Started
    ✔ Container milvus-standalone  Started
   ```

   [!TIP]
   You can add a `--build` argument in case you have made some code changes or have any requirement of re-building containers from source code:

   ```bash
   docker compose -f deploy/compose/docker-compose.yaml up -d --build
   ```

1. Confirm that the containers are running.

   ```bash
   docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```

   *Example Output*

   ```output
   CONTAINER ID   NAMES               STATUS
   39a8524829da   rag-playground      Up 2 minutes
   bfbd0193dbd2   rag-server          Up 2 minutes
   ec02ff3cc58b   milvus-standalone   Up 3 minutes
   6969cf5b4342   milvus-minio        Up 3 minutes (healthy)
   57a068d62fbb   milvus-etcd         Up 3 minutes (healthy)
   ```

1. Open a web browser and access `http://localhost:8090` to use the RAG Playground. You can use the upload tab to ingest files into the server or follow [the notebooks](../notebooks/) to understand the API usage.


### Start the Containers using on-prem models

Use the following procedure to start the containers using on-premises models.

[!IMPORTANT]
To start the containers using cloud-hosted models, see the procedure in the previous section instead.

1. Verify that you meet the [hardware requirements](../README.md#hardware-requirements).

1. Export `NVIDIA_API_KEY` environment variable to pull the containers and models. Check the [Common Prerequisites](#common-prerequisites) section for the same.

1. Create a directory to cache the models and export the path to the cache as an environment variable.

   ```bash
   mkdir -p ~/.cache/model-cache
   export MODEL_DIRECTORY=~/.cache/model-cache
   ```

1. Export the connection information for the inference and retriever services. Replace the host address of the below URLs with workstation IPs, if the NIMs are deployed in a different workstation or outside the `nvidia-rag` docker network on the same system.

   ```bash
   export APP_LLM_SERVERURL="nemollm-inference:8000"
   export APP_EMBEDDINGS_SERVERURL="embedding-ms:8000"
   export APP_RANKING_SERVERURL="ranking-ms:8000"
   ```

   [!TIP]: To change the GPUs used for NIM deployment, set the following environment variables before triggering the docker compose. You can check available GPU details on your system using `nvidia-smi`

   ```bash
   LLM_MS_GPU_ID: Update this to specify the LLM GPU IDs (e.g., 0,1,2,3).
   EMBEDDING_MS_GPU_ID: Change this to set the embedding GPU ID.
   RANKING_MS_GPU_ID: Modify this to adjust the reranking LLM GPU ID.
   RANKING_MS_GPU_ID: Modify this to adjust the reranking LLM GPU ID.
   VECTORSTORE_GPU_DEVICE_ID : Modify to adjust the Milvus vector database GPU ID. This is applicable only if GPU acceleration is enabled for milvus.
   ```

1. Start the containers. Ensure all containers go into `up` status before testing. The NIM containers may take around 10-15 mins to start at first launch. The models are downloaded and cached in the path specified by `MODEL_DIRECTORY`.

    ```bash
    USERID=$(id -u) docker compose -f deploy/compose/docker-compose.yaml --profile local-nim up -d
    ```

   *Example Output*

   ```output
   ✔ Container milvus-minio                           Running
   ✔ Container rag-server                             Running
   ✔ Container nemo-retriever-embedding-microservice  Running
   ✔ Container milvus-etcd                            Running
   ✔ Container nemollm-inference-microservice         Running
   ✔ Container nemollm-retriever-ranking-microservice Running
   ✔ Container rag-playground                         Running
   ✔ Container milvus-standalone                      Running
   ```

1. Open a web browser and access `http://localhost:8090` to use the RAG Playground. You can use the upload tab to ingest files into the server or follow [the notebooks](../notebooks/) to understand the API usage.



