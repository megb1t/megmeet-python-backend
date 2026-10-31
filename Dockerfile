# --- Stage 1: Build ---
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Set the working directory
WORKDIR /app

# Enable bytecode compilation and force full file copy mode to prevent filesystem copy errors
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Use CPU wheels to avoid massive CUDA library size issues if a GPU isn't required on this instance
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu

# Install dependencies using the lockfile with caching
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --link-mode=copy

# --- Stage 2: Runtime ---
FROM python:3.12-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy your source code
COPY . .

# Add the virtual environment to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
