# Track 2 Dockerfile — Simulated TEE Boundary
#
# Honesty Note (RULES.md & LIMITATIONS.md):
#   This container provides process and filesystem isolation. It is explicitly
#   NOT a hardware Trusted Execution Environment (TEE). In a production system,
#   this container boundary would be replaced by an actual hardware enclave
#   (such as Intel TDX or AMD SEV-SNP using Gramine LibOS).

FROM python:3.12-slim

# Install C++ build tools required by llama-cpp-python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utilities and Track 2 server code
COPY shared/ /app/shared/
COPY track2_with_tee/ /app/track2_with_tee/

# Create models directory (to be mounted from host at runtime)
RUN mkdir -p /app/models

# Expose Track 2 port
EXPOSE 8001

ENV MODEL_PATH=/app/models/model.gguf
ENV PORT=8001
ENV PYTHONUNBUFFERED=1

# Run Track 2 server
CMD ["python", "-m", "uvicorn", "track2_with_tee.server:app", "--host", "0.0.0.0", "--port", "8001"]
