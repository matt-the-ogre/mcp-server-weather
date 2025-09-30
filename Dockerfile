FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose port
EXPOSE 80

# Run the application using fastmcp CLI
CMD ["uv", "run", "fastmcp", "run", "--transport=http", "--host=0.0.0.0", "--port=80", "server.py"]