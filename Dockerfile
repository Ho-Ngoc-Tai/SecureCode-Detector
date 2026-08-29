FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY demo/backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY demo/ ./demo/

WORKDIR /app/demo/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
