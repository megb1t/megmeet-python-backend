# --- Stage 1: Build ---
FROM ghcr.io/astral-sh/uv:python3.12-slim AS builder

# Set the working directory
WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Install dependencies using the lockfile
# We use mounts to avoid copying large cache files into the final image
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

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