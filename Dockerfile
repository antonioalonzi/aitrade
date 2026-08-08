FROM python:3.11-slim

WORKDIR /app

# Copy dependency definition and install
COPY pyproject.toml .
COPY src/ ./src
RUN pip install --no-cache-dir .

CMD ["python", "-m", "aitrade"]
