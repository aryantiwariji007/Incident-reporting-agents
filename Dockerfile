# ---------- 1. Use a lightweight Python base image ----------
FROM python:3.12-slim

# ---------- 2. Set the working directory ----------
WORKDIR /app

# ---------- 3. Install system dependencies you might need ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# ---------- 4. Copy requirements and install with pip ----------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- 5. Copy your source code ----------
COPY . .





# ---------- 8. Default command ----------
CMD ["python", "main.py"]
