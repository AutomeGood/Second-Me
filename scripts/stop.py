import os
import subprocess
import time
import logging
import dotenv
import shutil # Though not explicitly in list, good for PID file removal if needed beyond os.remove
import signal # For signal constants if needed, though psutil handles this mostly
import psutil
import argparse

# --- Global Variables & Configuration ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_LOCAL_APP_PORT = 8002
DEFAULT_LOCAL_FRONTEND_PORT = 3000
DEFAULT_LLAMA_SERVER_PORT = 8080 # Common default for llama.cpp server

# --- Logging Setup ---
LOG_DIR = os.path.join(project_root, "logs")
RUN_DIR = os.path.join(project_root, "run") # For PID files
os.makedirs(LOG_DIR, exist_ok=True)
# RUN_DIR should already exist if start.py ran, but ensure for standalone use
os.makedirs(RUN_DIR, exist_ok=True) 

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "stop.log"))
    ]
)

# --- Environment Variable Loading ---
def load_env_vars():
    """Loads environment variables from .env file."""
    env_path = os.path.join(project_root, ".env")
    loaded = dotenv.load_dotenv(dotenv_path=env_path)
    if loaded:
        logging.info(f"Loaded environment variables from {env_path}")
    else:
        logging.info(f".env file not found at {env_path} or is empty. Using default ports.")

    # Get ports, defaulting if not found in .env
    local_app_port = int(os.getenv("LOCAL_APP_PORT", DEFAULT_LOCAL_APP_PORT))
    local_frontend_port = int(os.getenv("LOCAL_FRONTEND_PORT", DEFAULT_LOCAL_FRONTEND_PORT))
    # Llama server port might not be in .env, handle separately or use a common default
    
    return local_app_port, local_frontend_port

# --- PID File Management ---
PID_BACKEND_FILE = os.path.join(RUN_DIR, ".backend.pid")
PID_FRONTEND_FILE = os.path.join(RUN_DIR, ".frontend.pid")

def read_pid(pid_file_path):
    """Reads PID from file. Returns int or None."""
    try:
        if os.path.exists(pid_file_path):
            with open(pid_file_path, "r") as f:
                pid_str = f.read().strip()
                if pid_str:
                    return int(pid_str)
        return None
    except (IOError, ValueError) as e:
        logging.error(f"Error reading PID from {pid_file_path}: {e}")
        return None

def remove_pid_file(pid_file_path):
    """Deletes PID file if it exists."""
    try:
        if os.path.exists(pid_file_path):
            os.remove(pid_file_path)
            logging.info(f"Removed PID file: {pid_file_path}")
    except OSError as e:
        logging.error(f"Error removing PID file {pid_file_path}: {e}")


# --- Main script execution placeholder ---
if __name__ == "__main__":
    logging.info(f"Stop script initialized from project_root: {project_root}")
    
    parser = argparse.ArgumentParser(description="Stop the application services.")
    parser.add_argument(
        "--llama-port",
        type=int,
        default=DEFAULT_LLAMA_SERVER_PORT, # Use the global default
        help=f"Port to target for stopping Llama server processes (default: {DEFAULT_LLAMA_SERVER_PORT})."
    )
    args = parser.parse_args()

    main(args)
