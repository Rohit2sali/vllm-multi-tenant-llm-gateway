# Multi-Tenant LLM Inference Gateway

A high-performance, containerized API gateway for managing and serving Large Language Models (LLMs) to multiple tenants. Built to wrap around the **vLLM** engine, this gateway provides enterprise-grade features including request scheduling, concurrent user rate-limiting, API key management, and dynamic Multi-LoRA routing.

## 🚀 Features

* **High-Throughput Inference:** Leverages `vLLM` as the core engine for state-of-the-art serving throughput and memory management (PagedAttention).
* **Multi-Tenancy & Authentication:** Uses an embedded `SQLite` database to manage user accounts, securely store API keys, and track tenant-specific usage.
* **Concurrency Limiting:** Built-in rate limiter restricts the number of concurrent requests per user/tenant to prevent resource starvation and ensure fair usage.
* **Smart Request Scheduling:** Queues and schedules incoming inference requests to optimize GPU utilization and maintain stable latency under heavy load.
* **Dynamic Multi-LoRA Support:** Allows different tenants to seamlessly query different fine-tuned LoRA adapters on top of a single base model without needing to load multiple base models into VRAM.
* **Fully Containerized:** Easily deployable via Docker, ensuring environment consistency across different host machines.

## 🏗️ Architecture

flowchart TD
    %% Styling definitions
    classDef client fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px
    classDef api fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px
    classDef storage fill:#fff3e0,stroke:#fb8c00,stroke-width:2px
    classDef management fill:#e8f5e9,stroke:#43a047,stroke-width:2px
    classDef inference fill:#ffebee,stroke:#e53935,stroke-width:2px

    %% Components
    UI([Frontend UI / User]):::client
    DB[(SQLite Database\nUsers & API Keys)]:::storage
    FastAPI[FastAPI Wrapper]:::api
    
    subgraph Request_Management [Request Management Zone]
        Scheduler{Scheduler}:::management
        Limiter[Concurrent Limiter]:::management
        Q1[Queue 1]:::management
        Q2[Queue 2]:::management
        Q3[Queue 3]:::management
    end

    subgraph Inference_Zone [Inference Zone]
        vLLM[vLLM Engine]:::inference
        LoRA[[LoRA Adapters]]:::inference
    end

    %% Workflow Connections
    UI -->|1. Generate User ID & API Key| DB
    UI -->|2. Input API Key & Submit Prompt| FastAPI
    
    FastAPI -->|3. Fetch Tier & LoRA Key| DB
    FastAPI -->|4. Forward Prompt + User Metadata| Scheduler
    
    Scheduler <-->|5. Check User Limits| Limiter
    
    Scheduler -->|6. Assign to Queue based on tier/traffic| Q1
    Scheduler -->|6. Assign to Queue based on tier/traffic| Q2
    Scheduler -->|6. Assign to Queue based on tier/traffic| Q3
    
    Q1 -->|7. Dispatch Request| vLLM
    Q2 -->|7. Dispatch Request| vLLM
    Q3 -->|7. Dispatch Request| vLLM
    
    vLLM -.->|Applies specific| LoRA
    
    vLLM -->|8. Return LLM Response| UI  
    

🛠️ Technology Stack
Inference Engine: vLLM

API Framework: FastAPI / Python

Database: SQLite

Deployment: Docker

📦 Getting Started
Prerequisites
Docker installed on your host machine.

NVIDIA GPU(s) with drivers installed.

NVIDIA Container Toolkit installed to expose GPUs to Docker.

Running the Gateway
You can spin up the entire gateway using the following Docker command. This command mounts a local data directory to persist your SQLite database and model weights, exposes port 8000, and grants the container access to all available GPUs.


# 1. Clone the repository
git clone [https://github.com/yourusername/multi-tenant-llm-gateway.git](https://github.com/yourusername/multi-tenant-llm-gateway.git)
cd multi-tenant-llm-gateway

# 2. Build the Docker image
docker build -t llm-gateway .

# 3. Run the container
docker run -d \
  --name llm-gateway-instance \
  --gpus all \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v /path/to/your/models:/app/models \
  llm-gateway


# 1. Clone the repository
git clone [https://github.com/yourusername/multi-tenant-llm-gateway.git](https://github.com/yourusername/multi-tenant-llm-gateway.git)
cd multi-tenant-llm-gateway

# 2. Build the Docker image
docker build -t llm-gateway .

# 3. Run the container
docker run -d \
  --name llm-gateway-instance \
  --gpus all \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v /path/to/your/models:/app/models \
  llm-gateway

📖 API Usage Example
Once the container is running, you can interact with the gateway.

1. Generate Text (Specifying a LoRA)

Bash
curl -X POST "http://localhost:8000/v1/completions" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "model": "base-model-name",
           "lora_name": "tenant-specific-lora",
           "prompt": "Explain the concept of PagedAttention.",
           "max_tokens": 200
         }'
