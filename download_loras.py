from huggingface_hub import snapshot_download
from pathlib import Path

# Get project root (directory where this script lives)
BASE_DIR = Path(__file__).resolve().parent

# Create loras directory inside project
LORAS_DIR = BASE_DIR / "loras"
LORAS_DIR.mkdir(exist_ok=True)

print("Downloading Adapter 1 (Tool Calling)...")
snapshot_download(
    repo_id="codelion/Llama-3.2-1B-Instruct-tool-calling-lora",
    local_dir=LORAS_DIR / "tool_adapter",
    allow_patterns=["*.json", "*.safetensors", "*.bin"]
)

print("Downloading Adapter 2 (Function Calling)...")
snapshot_download(
    repo_id="minpeter/LoRA-Llama-3.2-1B-tool-vllm-ci",
    local_dir=LORAS_DIR / "function_adapter",
    allow_patterns=["*.json", "*.safetensors", "*.bin"]
)

print("Downloading Adapter 3 (Journals)...")
snapshot_download(
    repo_id="HaiderKH/journals3-llama3.2-1b-lora-adapter",
    local_dir=LORAS_DIR / "journal_adapter",
    allow_patterns=["*.json", "*.safetensors", "*.bin"]
)

print("Downloading Adapter 4 (General)...")
snapshot_download(
    repo_id="S21348/llama-3.2-1b-lora",
    local_dir=LORAS_DIR / "general_adapter",
    allow_patterns=["*.json", "*.safetensors", "*.bin"]
)