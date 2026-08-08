FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ ./src
RUN mkdir -p data
RUN pip install --no-cache-dir .

CMD ["python", "-m", "aitrade"]
