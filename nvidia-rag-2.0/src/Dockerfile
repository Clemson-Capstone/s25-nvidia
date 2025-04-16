ARG BASE_IMAGE_URL=nvcr.io/nvidia/base/ubuntu
ARG BASE_IMAGE_TAG=22.04_20240212

FROM ${BASE_IMAGE_URL}:${BASE_IMAGE_TAG}

ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system and build dependencies
RUN apt update && apt install -y \
    curl \
    software-properties-common \
    libgl1 \
    libglib2.0-0 \
    libmagic1 \
    file \
    build-essential \
    gcc \
    g++ \
    python3.10 \
    python3.10-dev \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt update && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install pip for python3.10
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

# Optional: Check pip version (useful for debugging)
RUN python3.10 -m pip --version

# Legal compliance - download sources of installed packages
RUN sed -i 's/# deb-src/deb-src/g' /etc/apt/sources.list && \
    apt update && \
    apt install -y xz-utils && \
    mkdir -p /legal/source && \
    cd /legal/source && \
    apt list --installed | grep -i installed | sed 's|\(.*\)/.*|\1|' | xargs apt source --download-only && \
    rm -f /legal/source/xz-utils* && \
    apt remove -y xz-utils

COPY LICENSE-3rd-party.txt /legal/

# Install Python dependencies (shared)
RUN --mount=type=cache,id=pip_cache,target=/root/.cache/pip,sharing=locked \
    --mount=type=bind,source=./requirements.txt,target=/opt/requirements.txt \
    pip3 install --no-cache-dir -r /opt/requirements.txt

# Ensure clean versions of document parsers (important for unstructured)
RUN pip uninstall -y pdfminer pdfminer.six unstructured langchain-unstructured
RUN pip install pdfminer.six==20250327 unstructured==0.17.2 langchain-unstructured

# Patch for compatibility with unstructured version
RUN sed -i 's/from pdfminer.pdfparser import PSSyntaxError/from pdfminer.pdfparser import PDFSyntaxError as PSSyntaxError/' /usr/local/lib/python3.10/dist-packages/unstructured/partition/pdf_image/pdfminer_utils.py

# Create and configure /tmp-data for HF and embeddings
RUN mkdir /tmp-data && chmod 777 -R /tmp-data && chown 1000:1000 -R /tmp-data
ENV HF_HOME=/tmp-data

# Copy project files
WORKDIR /workspace
COPY ./ /workspace
WORKDIR /workspace/

# Run app
ENTRYPOINT ["uvicorn", "src.server:app"]
