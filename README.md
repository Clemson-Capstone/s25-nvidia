<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

## License and Attribution

This project is licensed under the [Apache License 2.0](./LICENSE).

### Upstream NVIDIA Dependencies

This project builds upon and integrates components from the [NVIDIA RAG Blueprint v2.0.0](https://github.com/NVIDIA-AI-Blueprints/rag), which is licensed under the Apache License 2.0. Portions of the original RAG blueprint are located under the `foundational-rag/` directory.

Additionally, this project uses the [`nemoguardrails`](https://github.com/NVIDIA/NeMo-Guardrails) Python package (v0.11.0), also licensed under Apache License 2.0, to provide guardrail functionality for chatbot safety and control.

All original and modified content is redistributed in compliance with the terms of the Apache License 2.0.


# Get Started With VTA Blueprint:

Use the following documentation to get started with the NVIDIA RAG Blueprint.
- [Introduction](#introduction)
- [Obtain an API Key](#obtain-an-api-key)
- [Deploy With Docker Compose](#deploy-with-docker-compose)


## Introduction
Everything is run via docker containers, with docker compose. 

### Folder Structure:
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

1. Open a web browser and access `http://localhost:8090` to use the RAG Playground, or go to `http://localhost:3000` to use the frontend for the canvas application. the RAG playground is more for testing the chatbot, and the frontend is for the canvas integration with the chatbot.


