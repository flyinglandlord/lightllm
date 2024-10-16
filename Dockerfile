FROM nvidia/cuda:11.8.0-runtime-ubuntu20.04 as base
ARG PYTORCH_VERSION=2.4.0
ARG PYTHON_VERSION=3.9
ARG CUDA_VERSION=11.8
ARG MAMBA_VERSION=23.1.0-1
ARG TARGETPLATFORM

ENV PATH=/opt/conda/bin:$PATH \
    CONDA_PREFIX=/opt/conda

RUN chmod 777 -R /tmp && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    libssl-dev \
    curl \
    g++ \
    make \
    git && \
    rm -rf /var/lib/apt/lists/*

RUN case ${TARGETPLATFORM} in \
    "linux/arm64")  MAMBA_ARCH=aarch64  ;; \
    *)              MAMBA_ARCH=x86_64   ;; \
    esac && \
    curl -fsSL -o ~/mambaforge.sh -v "https://github.com/conda-forge/miniforge/releases/download/${MAMBA_VERSION}/Mambaforge-${MAMBA_VERSION}-Linux-${MAMBA_ARCH}.sh" && \
    bash ~/mambaforge.sh -b -p /opt/conda && \
    rm ~/mambaforge.sh

RUN case ${TARGETPLATFORM} in \
    "linux/arm64")  exit 1 ;; \
    *)              /opt/conda/bin/conda update -y conda &&  \
    /opt/conda/bin/conda install -y "python=${PYTHON_VERSION}" ;; \
    esac && \
    /opt/conda/bin/conda clean -ya


WORKDIR /root

COPY ./requirements.txt /lightllm/requirements.txt
RUN pip install -r /lightllm/requirements.txt --no-cache-dir --ignore-installed --extra-index-url https://download.pytorch.org/whl/cu118
RUN pip install nvidia-nccl-cu12==2.20.5

COPY . /lightllm
RUN pip install -e /lightllm --no-cache-dir
