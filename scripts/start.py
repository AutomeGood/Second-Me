import os
import subprocess
import time
import logging
import dotenv
import argparse
import shutil # Required but not explicitly in the list, common for file ops
import socket
import requests 

# --- Global Variables & Configuration ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_LOCAL_APP_PORT = 8002
DEFAULT_LOCAL_FRONTEND_PORT = 3000
DEFAULT_HOST_ADDRESS = "127.0.0.1" # Explicitly define default host

# --- Logging Setup ---
LOG_DIR = os.path.join(project_root, "logs")
RUN_DIR = os.path.join(project_root, "run")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(RUN_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "start.log")) # Main log for start.py itself
    ]
)

# --- Environment Variable Loading ---
def load_env_vars():
    """Loads environment variables from .env file and returns key settings."""
    env_path = os.path.join(project_root, ".env")
    if not os.path.exists(env_path):
        logging.warning(f".env file not found at {env_path}. Creating a default one.")
        try:
            with open(env_path, "w") as f:
                f.write(f"LOCAL_APP_PORT={DEFAULT_LOCAL_APP_PORT}\n")
                f.write(f"LOCAL_FRONTEND_PORT={DEFAULT_LOCAL_FRONTEND_PORT}\n")
                f.write(f"HOST_ADDRESS={DEFAULT_HOST_ADDRESS}\n") # Use defined default
            logging.info(f"Created a default .env file at {env_path}")
        except IOError as e:
            logging.error(f"Could not create default .env file: {e}")
            # Continue with defaults even if write fails
    
    loaded = dotenv.load_dotenv(dotenv_path=env_path)
    if loaded:
        logging.info(f"Loaded environment variables from {env_path}")
    else:
        logging.warning(f"Could not load .env file from {env_path} (file might be empty or unreadable). Using defaults.")

    local_app_port = int(os.getenv("LOCAL_APP_PORT", DEFAULT_LOCAL_APP_PORT))
    local_frontend_port = int(os.getenv("LOCAL_FRONTEND_PORT", DEFAULT_LOCAL_FRONTEND_PORT))
    host_address = os.getenv("HOST_ADDRESS", DEFAULT_HOST_ADDRESS) # Use defined default
    
    try: # Ensure .env is up-to-date with effective settings
        current_env_vars = dotenv.dotenv_values(env_path) if os.path.exists(env_path) else {}
        current_env_vars["LOCAL_APP_PORT"] = str(local_app_port)
        current_env_vars["LOCAL_FRONTEND_PORT"] = str(local_frontend_port)
        current_env_vars["HOST_ADDRESS"] = host_address
        with open(env_path, "w") as f:
            for key, value in current_env_vars.items():
                f.write(f"{key}={value}\n")
        logging.info(f"Ensured .env file at {env_path} is up-to-date with effective ports/host.")
    except IOError as e:
        logging.warning(f"Could not update .env file with effective ports/host: {e}")

    return local_app_port, local_frontend_port, host_address

# --- PID File Management ---
PID_BACKEND_FILE = os.path.join(RUN_DIR, ".backend.pid")
PID_FRONTEND_FILE = os.path.join(RUN_DIR, ".frontend.pid")

def write_pid(pid_file_path, pid):
    try:
        with open(pid_file_path, "w") as f:
            f.write(str(pid))
        logging.info(f"PID {pid} written to {pid_file_path}")
    except IOError as e:
        logging.error(f"Could not write PID to {pid_file_path}: {e}")

def read_pid(pid_file_path):
    try:
        if os.path.exists(pid_file_path):
            with open(pid_file_path, "r") as f:
                pid_str = f.read().strip()
                if pid_str: return int(pid_str)
        return None
    except (IOError, ValueError) as e:
        logging.error(f"Could not read PID from {pid_file_path}: {e}")
        return None

def kill_process_by_pid(pid, service_name="Service"):
    if pid is None:
        logging.warning(f"No PID provided for {service_name}. Cannot kill.")
        return False
    try:
        if os.name == 'nt': # Windows
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=True, capture_output=True, text=True)
        else: # Unix-like (Linux, macOS)
            os.killpg(os.getpgid(pid), 9) # Kill process group with SIGKILL
        logging.info(f"Successfully sent kill signal to {service_name} (PID {pid}) and its process group.")
        return True
    except ProcessLookupError:
        logging.warning(f"{service_name} with PID {pid} not found (already terminated?).")
        return True
    except Exception as e:
        # On Unix, os.getpgid(pid) can fail if the process already exited.
        logging.error(f"Failed to kill {service_name} with PID {pid}: {e}")
        # Fallback for Unix if group kill failed (e.g. process exited before getpgid)
        if os.name != 'nt':
            try:
                os.kill(pid,9)
                logging.info(f"Fallback: Successfully killed individual process {pid} for {service_name}")
                return True
            except Exception as e_ind:
                logging.error(f"Fallback kill for individual process {pid} also failed: {e_ind}")

        return False

# --- Port Checking ---
def check_port_available(port, host=DEFAULT_HOST_ADDRESS):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.bind((host, port))
        return True
    except socket.error as e:
        if e.errno == socket.errno.EADDRINUSE or (os.name == 'nt' and e.winerror == 10048): # EADDRINUSE for Windows
            logging.warning(f"Port {port} on host {host} is already in use.")
        else:
            logging.error(f"Error checking port {port} on host {host}: {e}")
        return False
    finally:
        s.close()

# --- Prerequisites Check ---
def check_prerequisites():
    logging.info("Checking prerequisites...")
    all_prereqs_met = True
    llama_cpp_dir = os.path.join(project_root, "llama.cpp")
    llama_server_exe_name = "llama-server.exe" if os.name == "nt" else "llama-server"
    
    built_server_path_candidates = []
    if os.name == "nt":
        built_server_path_candidates.extend([
            os.path.join(llama_cpp_dir, "build", "bin", "Release", llama_server_exe_name),
            os.path.join(llama_cpp_dir, "build", "bin", llama_server_exe_name)
        ])
    else:
        built_server_path_candidates.extend([
            os.path.join(llama_cpp_dir, "build", "bin", llama_server_exe_name),
            os.path.join(llama_cpp_dir, "build", llama_server_exe_name) # If not in a 'bin' subdirectory
        ])

    if any(os.path.exists(p) and os.access(p, os.X_OK) for p in built_server_path_candidates):
        logging.info("Llama server executable found.")
    else:
        logging.error(f"Llama server executable not found in expected locations (e.g., {built_server_path_candidates[0]}).")
        all_prereqs_met = False

    frontend_node_modules = os.path.join(project_root, "lpm_frontend", "node_modules")
    if os.path.isdir(frontend_node_modules):
        logging.info("Frontend 'node_modules' directory found.")
    else:
        logging.error(f"Frontend 'node_modules' directory not found at {frontend_node_modules}.")
        all_prereqs_met = False

    if not all_prereqs_met:
        logging.error("One or more prerequisites are missing. Please run 'python scripts/setup.py' first.")
    else:
        logging.info("All prerequisites met.")
    return all_prereqs_met

# --- Backend Service Management ---
def check_backend_health(port, host, max_attempts=300, delay=1): # Increased attempts for slower systems
    health_url = f"http://{host}:{port}/health"
    logging.info(f"Checking backend health at {health_url}...")
    for attempt in range(max_attempts):
        try:
            response = requests.get(health_url, timeout=3) # Short timeout for individual request
            if response.status_code == 200:
                logging.info(f"Backend health check successful (Status {response.status_code}).")
                return True
            logging.warning(f"Backend health check attempt {attempt + 1}/{max_attempts} failed with status {response.status_code}.")
        except requests.ConnectionError:
            logging.info(f"Backend health check attempt {attempt + 1}/{max_attempts}: Connection error. Backend not yet ready.")
        except requests.Timeout:
            logging.warning(f"Backend health check attempt {attempt + 1}/{max_attempts}: Request timed out.")
        except requests.RequestException as e:
            logging.error(f"Backend health check attempt {attempt + 1}/{max_attempts} encountered an error: {e}")
        time.sleep(delay)
    logging.error(f"Backend health check failed after {max_attempts} attempts.")
    return False

def start_backend(args_cli, local_app_port, host_address):
    logging.info("Attempting to start the backend service...")
    if not check_port_available(local_app_port, host_address):
        return False # Error already logged

    start_script = os.path.join(project_root, "scripts", "start_local.sh")
    if not os.path.exists(start_script):
        logging.error(f"{start_script} not found. Cannot start backend.")
        return False
    try:
        os.chmod(start_script, 0o755) # Ensure executable
    except Exception as e:
        logging.error(f"Failed to make {start_script} executable: {e}")
        return False

    log_file_path = os.path.join(LOG_DIR, "backend.log")
    pid = None
    try:
        with open(log_file_path, "wb") as log_f: # Open in binary write for Popen
            cmd = ["bash", start_script] if os.name != 'nt' else [start_script] # Windows might need Git Bash/WSL
            # For Unix, os.setsid creates a new session and process group, detaching from the current terminal.
            # This is good for daemonizing and ensuring kill_process_by_pid can target the group.
            process_creation_flags = {} if os.name == 'nt' else {'preexec_fn': os.setsid}
            process = subprocess.Popen(cmd, stdout=log_f, stderr=log_f, cwd=project_root, **process_creation_flags)
            pid = process.pid
            write_pid(PID_BACKEND_FILE, pid)
        logging.info(f"Backend service process initiated with PID {pid}. Logs directed to: {log_file_path}")
        
        if not check_backend_health(local_app_port, host_address):
            logging.error("Backend health check failed after starting process. Attempting to stop backend process.")
            kill_process_by_pid(pid, "Backend")
            if os.path.exists(PID_BACKEND_FILE): os.remove(PID_BACKEND_FILE)
            return False
        logging.info("Backend service started and health check passed.")
        return True
    except Exception as e:
        logging.error(f"Failed to start backend service: {e}", exc_info=True)
        if pid: # If process was started but an error occurred later
            kill_process_by_pid(pid, "Backend")
            if os.path.exists(PID_BACKEND_FILE): os.remove(PID_BACKEND_FILE)
        return False

# --- Frontend Service Management ---
def check_frontend_ready(port, host, log_file, max_attempts=300, delay=1): # Increased attempts
    frontend_url = f"http://{host}:{port}"
    logging.info(f"Checking frontend readiness at {frontend_url} and in log {log_file}...")
    # Keywords that might indicate frontend dev server is ready
    readiness_keywords = ["Local:", "Ready", "Compiled successfully", "vite", "webpack", "Serving!", "Network:", "DONE"]

    for attempt in range(max_attempts):
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    # Read last few lines for efficiency, or tail-like behavior if possible
                    # For simplicity, reading whole file, but can be optimized for large logs
                    content = f.read() 
                    if any(keyword in content for keyword in readiness_keywords):
                        logging.info(f"Frontend readiness detected in log file (found keyword).")
                        # As a secondary check, try connecting via HTTP
                        try:
                            requests.get(frontend_url, timeout=3)
                            logging.info(f"Frontend also responding to HTTP GET at {frontend_url}.")
                            return True
                        except requests.RequestException:
                            logging.warning(f"Frontend log indicates ready, but {frontend_url} not responding. Retrying.")
            except Exception as e:
                logging.warning(f"Error reading frontend log file {log_file}: {e}")
        
        # Less frequent HTTP check as a fallback or primary if log check is unreliable
        if attempt > 0 and attempt % 10 == 0: 
            try:
                response = requests.get(frontend_url, timeout=3)
                if response.status_code < 500: # Any 2xx, 3xx, 4xx suggests server is up
                    logging.info(f"Frontend HTTP check to {frontend_url} successful (Status: {response.status_code}).")
                    return True
            except requests.ConnectionError:
                logging.info(f"Frontend HTTP check (attempt {attempt + 1}/{max_attempts}): Connection to {frontend_url} refused.")
            except requests.Timeout:
                logging.info(f"Frontend HTTP check (attempt {attempt + 1}/{max_attempts}): Connection to {frontend_url} timed out.")
            except requests.RequestException: 
                pass # Avoid too much noise, log primarily based on log file or connection errors

        logging.info(f"Frontend readiness check attempt {attempt + 1}/{max_attempts}. Waiting for indicators...")
        time.sleep(delay)
        
    logging.error(f"Frontend readiness check failed after {max_attempts} attempts.")
    return False

def start_frontend(args_cli, local_frontend_port, local_app_port, host_address):
    logging.info("Attempting to start the frontend service...")
    if not check_port_available(local_frontend_port, host_address):
        return False

    frontend_dir = os.path.join(project_root, "lpm_frontend")
    if not os.path.isdir(frontend_dir):
        logging.error(f"Frontend directory not found: {frontend_dir}. Cannot start.")
        return False

    try: # Update frontend .env file
        target_env_path = os.path.join(frontend_dir, ".env")
        # Read existing or create new
        fe_env_vars = dotenv.dotenv_values(target_env_path) if os.path.exists(target_env_path) else {}
        
        # These are common names for Vite, adjust if your frontend setup differs
        fe_env_vars["VITE_HOST_ADDRESS"] = host_address 
        fe_env_vars["VITE_LOCAL_APP_PORT"] = str(local_app_port)
        # Construct API base URL; frontend might use this to talk to backend
        fe_env_vars["VITE_API_BASE_URL"] = f"http://{host_address}:{local_app_port}"

        with open(target_env_path, "w") as f_target:
            for key, value in fe_env_vars.items():
                f_target.write(f"{key}={value}\n")
        logging.info(f"Updated/created .env file at {target_env_path} for frontend.")
    except Exception as e:
        logging.warning(f"Failed to update .env for frontend: {e}. Frontend might use stale or default settings.")

    log_file_path = os.path.join(LOG_DIR, "frontend.log")
    pid = None
    try:
        with open(log_file_path, "wb") as log_f:
            cmd = ["npm", "run", "dev"]
            # shell=True for Windows `npm.cmd` is often more reliable.
            # os.setsid for Unix-like process group management.
            process_creation_flags = {} if os.name == 'nt' else {'preexec_fn': os.setsid}
            process = subprocess.Popen(cmd, stdout=log_f, stderr=log_f, cwd=frontend_dir, 
                                       shell=(os.name == 'nt'), **process_creation_flags)
            pid = process.pid
            write_pid(PID_FRONTEND_FILE, pid)
        logging.info(f"Frontend service process initiated with PID {pid}. Logs: {log_file_path}")

        if not check_frontend_ready(local_frontend_port, host_address, log_file_path):
            logging.error("Frontend readiness check failed. Attempting to stop frontend process.")
            kill_process_by_pid(pid, "Frontend")
            if os.path.exists(PID_FRONTEND_FILE): os.remove(PID_FRONTEND_FILE)
            return False
        logging.info("Frontend service started and readiness check passed.")
        return True
    except Exception as e:
        logging.error(f"Failed to start frontend service: {e}", exc_info=True)
        if pid:
            kill_process_by_pid(pid, "Frontend")
            if os.path.exists(PID_FRONTEND_FILE): os.remove(PID_FRONTEND_FILE)
        return False

# --- Main Application Logic ---
def main(parsed_args, app_port, frontend_port, host_addr):
    # Directories LOG_DIR and RUN_DIR are created at global scope.

    if not check_prerequisites():
        logging.critical("Prerequisite check failed. Exiting.")
        return

    logging.info("Starting backend service...")
    if not start_backend(parsed_args, app_port, host_addr):
        logging.critical("Failed to start backend service. Exiting.")
        return # Critical failure
    logging.info("Backend service initiation successful.")

    if not parsed_args.backend_only:
        logging.info("Starting frontend service...")
        if not start_frontend(parsed_args, frontend_port, app_port, host_addr):
            logging.critical("Failed to start frontend service. Backend might still be running.")
            # Optional: Attempt to stop backend if frontend fails
            backend_pid_val = read_pid(PID_BACKEND_FILE)
            if backend_pid_val:
                logging.info("Attempting to stop backend service due to frontend startup failure...")
                kill_process_by_pid(backend_pid_val, "Backend")
                if os.path.exists(PID_BACKEND_FILE): os.remove(PID_BACKEND_FILE)
            return # Critical failure
        logging.info("Frontend service initiation successful.")
    else:
        logging.info("Skipping frontend service startup due to --backend-only flag.")

    logging.info("All requested services have been initiated successfully.")
    logging.info(f"Backend should be available at: http://{host_addr}:{app_port}")
    if not parsed_args.backend_only:
        logging.info(f"Frontend should be available at: http://{host_addr}:{frontend_port}")
    
    logging.info("This script has finished initiating services.")
    logging.info("To stop services, run 'python scripts/stop.py'.")
    logging.info("If you started this script directly (e.g. `python scripts/start.py`), Ctrl+C will only stop this script, not the background services.")


# --- Main script execution ---
if __name__ == "__main__":
    logging.info(f"Initializing start script from project_root: {project_root}")
    
    # Load environment variables first
    APP_PORT, FRONTEND_PORT, HOST_ADDRESS_FROM_ENV = load_env_vars()
    logging.info(f"Effective settings from .env/defaults: Backend Port={APP_PORT}, Frontend Port={FRONTEND_PORT}, Host={HOST_ADDRESS_FROM_ENV}")
    
    parser = argparse.ArgumentParser(description="Start the application's backend and frontend services.")
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Start only the backend service."
    )
    # Add other arguments here if needed, e.g., to override ports or host
    # parser.add_argument("--app-port", type=int, help="Override backend port.")
    # parser.add_argument("--frontend-port", type=int, help="Override frontend port.")
    # parser.add_argument("--host", type=str, help="Override host address.")

    args = parser.parse_args()

    # Determine final ports and host (e.g., allow CLI args to override .env)
    # final_app_port = args.app_port if args.app_port else APP_PORT
    # final_frontend_port = args.frontend_port if args.frontend_port else FRONTEND_PORT
    # final_host_address = args.host if args.host else HOST_ADDRESS_FROM_ENV
    # For now, use .env loaded values directly:
    final_app_port = APP_PORT
    final_frontend_port = FRONTEND_PORT
    final_host_address = HOST_ADDRESS_FROM_ENV


    try:
        main(args, final_app_port, final_frontend_port, final_host_address)
    except KeyboardInterrupt:
        logging.info("Start script interrupted by user (Ctrl+C).")
        logging.warning("This action only stops the start.py script itself, not the background services.")
        logging.warning("Please use 'python scripts/stop.py' to stop the services.")
    except Exception as e:
        logging.error(f"An unexpected error occurred in the start script: {e}", exc_info=True)
    finally:
        logging.info("Start script execution finished.")
