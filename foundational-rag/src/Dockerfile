ARG BASE_IMAGE_URL=nvcr.io/nvidia/base/ubuntu
ARG BASE_IMAGE_TAG=22.04_20240212
FROM ${BASE_IMAGE_URL}:${BASE_IMAGE_TAG}
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND noninteractive
# Install required ubuntu packages for setting up python 3.10
RUN apt update && \
 apt install -y curl software-properties-common libgl1 libglib2.0-0 libmagic1 file && \
 add-apt-repository ppa:deadsnakes/ppa && \
 apt update && apt install -y python3.10 && \
 apt-get clean
# Install pip for python3.10
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
RUN rm -rf /var/lib/apt/lists/*

# Clean installation of PDF and document processing packages
RUN pip uninstall -y pdfminer pdfminer.six unstructured langchain-unstructured
RUN pip install pdfminer.six==20250327 unstructured==0.17.2 langchain-unstructured

# Will perform the text replacement in the file
RUN sed -i 's/from pdfminer.pdfparser import PSSyntaxError/from pdfminer.pdfparser import PDFSyntaxError as PSSyntaxError/' /usr/local/lib/python3.10/dist-packages/unstructured/partition/pdf_image/pdfminer_utils.py
# Install build dependencies before pip install
RUN apt update && apt install -y \
    build-essential \
    gcc \
    g++ \
    python3.10-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download the sources of apt packages within the container for standard legal compliance
RUN sed -i 's/# deb-src/deb-src/g' /etc/apt/sources.list
RUN apt update
# xz-utils is needed to pull the source and unpack them correctly
RUN apt install xz-utils -y
RUN mkdir -p /legal/source
WORKDIR /legal/source
# Read installed packages, strip all but the package names, pipe to 'apt source' to download respective packages
RUN apt list --installed | grep -i installed | sed 's|\(.*\)/.*|\1|' | xargs apt source --download-only
# The source is saved in directories as well as tarballs in the current dir
RUN rm xz-utils*
COPY LICENSE-3rd-party.txt /legal/

# Install common dependencies for all examples
RUN --mount=type=cache,id=pip_cache,target=/root/.cache/pip,sharing=locked \
 --mount=type=bind,source=./requirements.txt,target=/opt/requirements.txt \
 pip3 install --no-cache-dir -r /opt/requirements.txt

# Set environment variables needed for Text splitter
RUN mkdir /tmp-data/;
RUN chmod 777 -R /tmp-data
RUN chown 1000:1000 -R /tmp-data
ENV HF_HOME=/tmp-data
WORKDIR /workspace
COPY ./ /workspace
WORKDIR /workspace/
ENTRYPOINT ["uvicorn", "src.server:app"]
