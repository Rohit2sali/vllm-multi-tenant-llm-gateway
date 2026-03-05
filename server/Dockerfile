FROM vllm/vllm-openai:latest

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your server code
COPY . .

# OVERRIDE the default vllm entrypoint so it doesn't force the vllm CLI
ENTRYPOINT []

# Start your FastAPI server normally
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
