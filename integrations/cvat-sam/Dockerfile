FROM python:3.10-slim-bookworm

ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu118
ARG MOBILESAM_REVISION=f706ad9c4eb7f219c00d9050e46328518ffb65d2
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
    MOBILESAM_CHECKPOINT=/opt/models/mobile_sam.pt \
    PYTHONPATH=/opt/nuclio

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip==24.3.1 \
    && python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url ${TORCH_INDEX_URL}
COPY requirements.txt /opt/mobilesam/requirements.txt
RUN python -m pip install -r /opt/mobilesam/requirements.txt \
    && python -m pip install --no-deps git+https://github.com/ChaoningZhang/MobileSAM.git@${MOBILESAM_REVISION}
COPY weights/mobile_sam.pt /opt/models/mobile_sam.pt
RUN echo '6dbb90523a35330fedd7f1d3dfc66f995213d81b29a5ca8108dbcdd4e37d6c2f  /opt/models/mobile_sam.pt' | sha256sum -c -
COPY nuclio/mobilesam/*.py /opt/nuclio/
COPY tests/ /opt/mobilesam/tests/
COPY scripts/smoke-test.py /opt/mobilesam/smoke-test.py
WORKDIR /opt/nuclio
