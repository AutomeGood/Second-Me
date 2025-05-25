import subprocess
import platform
import logging
import argparse
import os
import re
import shutil # For creating activation script
import zipfile # For handling .zip files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def get_os_type():
    """Detects the operating system."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"

def get_linux_distro():
    """Detects the Linux distribution."""
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    distro_val = line.split("=")[1].strip().lower()
                    # Remove quotes if any
                    distro = distro_val.replace('"', '')
                    if distro in ["debian", "fedora", "redhat", "arch", "alpine", "ubuntu"]:
                        return distro
                    return distro # Return the ID even if not in the known list
        # Fallback for older systems or if /etc/os-release is not available
        dist_info = platform.freedesktop_os_release()
        if 'ID' in dist_info:
            distro_val = dist_info['ID'].lower()
            distro = distro_val.replace('"', '')
            if distro in ["debian", "fedora", "redhat", "arch", "alpine", "ubuntu"]:
                return distro
            return distro
    except FileNotFoundError:
        pass # /etc/os-release not found
    except Exception as e:
        logging.warning(f"Could not determine Linux distribution from /etc/os-release: {e}")

    # Fallback to platform.linux_distribution() if available and /etc/os-release fails
    # Note: platform.linux_distribution() is deprecated in Python 3.8+
    # and platform.freedesktop_os_release() is preferred
    try:
        # platform.linux_distribution() was removed in Python 3.8
        # Use platform.freedesktop_os_release() as a more modern alternative
        # However, some systems might still rely on the older method or lack /etc/os-release
        dist_info = platform.freedesktop_os_release()
        if 'ID' in dist_info:
            distro_val = dist_info['ID'].lower()
            distro = distro_val.replace('"', '')
            if distro in ["debian", "fedora", "redhat", "arch", "alpine", "ubuntu"]:
                 return distro
            return distro # Return the ID even if not in the known list
    except Exception as e:
        logging.warning(f"Could not determine Linux distribution using platform module: {e}")

    return "other"


def get_system_id():
    """Returns a system identifier string."""
    os_type = get_os_type()
    if os_type == "linux":
        distro = get_linux_distro()
        return f"{os_type}-{distro}"
    return os_type

def check_python():
    """Checks for Python version >= 3.12."""
    try:
        result = subprocess.run(["python", "--version"], capture_output=True, text=True, check=True)
        version_str = result.stdout.strip().split(" ")[1]
        major, minor, _ = map(int, version_str.split("."))
        if major >= 3 and minor >= 12:
            logging.info(f"Python version {version_str} found.")
            return True
        else:
            logging.error(f"Python version {version_str} is installed, but >= 3.12 is required.")
            return False
    except (FileNotFoundError, subprocess.CalledProcessError, IndexError, ValueError) as e:
        logging.error(f"Error checking Python version: {e}")
        return False

def check_node():
    """Checks for Node.js."""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
        logging.info(f"Node.js version {result.stdout.strip()} found.")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.error(f"Error checking Node.js version: {e}")
        return False

def check_npm():
    """Checks for npm."""
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, check=True)
        logging.info(f"npm version {result.stdout.strip()} found.")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.error(f"Error checking npm version: {e}")
        return False

def check_cmake():
    """Checks for CMake."""
    try:
        result = subprocess.run(["cmake", "--version"], capture_output=True, text=True, check=True)
        # Extract version from the first line (e.g., "cmake version 3.22.1" or "cmake3 version 3.22.1")
        version_line = result.stdout.splitlines()[0]
        # Handle cases where the executable might be cmake3
        match = re.search(r"(?:cmake|cmake3)\s+version\s+([\d.]+)", version_line)
        if match:
            version_str = match.group(1)
            logging.info(f"CMake version {version_str} found.")
            return True
        else:
            logging.warning(f"Could not parse CMake version from: '{version_line}'. CMake is present.")
            return True # Assume it's okay if present but version not parsable
    except (FileNotFoundError, subprocess.CalledProcessError, IndexError) as e:
        logging.error(f"Error checking CMake version: {e}. Is CMake installed and in PATH?")
        return False

def check_poetry():
    """Checks for Poetry."""
    try:
        result = subprocess.run(["poetry", "--version"], capture_output=True, text=True, check=True)
        logging.info(f"Poetry version {result.stdout.strip()} found.")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.error(f"Error checking Poetry version: {e}")
        return False

def check_sqlite():
    """Checks for SQLite."""
    try:
        result = subprocess.run(["sqlite3", "--version"], capture_output=True, text=True, check=True)
        logging.info(f"SQLite version {result.stdout.strip().split(' ')[0]} found.")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.error(f"Error checking SQLite version: {e}")
        return False

# Utility function to run shell commands
def run_command(command_list, cwd=None, env=None, check_exit_code=True):
    """Runs a shell command and logs its output."""
    try:
        command_str = " ".join(command_list)
        logging.info(f"Running command: {command_str} (cwd: {cwd or os.getcwd()})")
        process = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            check=False, # We will check manually
            cwd=cwd,
            env=env,
        )
        if process.stdout:
            logging.info(f"Stdout:\n{process.stdout.strip()}")
        if process.stderr:
            # Stderr is not always an error, sometimes just progress or verbose info from tools like poetry
            logging.info(f"Stderr:\n{process.stderr.strip()}")

        if check_exit_code and process.returncode != 0:
            # Manually raise CalledProcessError if check_exit_code is True and return code is non-zero
            raise subprocess.CalledProcessError(process.returncode, command_list, output=process.stdout, stderr=process.stderr)
        return process # Return the completed process object for flexibility
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{' '.join(command_list)}' failed with exit code {e.returncode}")
        if e.stdout: # stdout might be on the exception object or on the process object
            logging.error(f"Stdout:\n{e.stdout.strip() if e.stdout else 'N/A'}")
        if e.stderr:
            logging.error(f"Stderr:\n{e.stderr.strip() if e.stderr else 'N/A'}")
        return None # Indicate failure
    except FileNotFoundError:
        logging.error(f"Command not found: {command_list[0]}. Please ensure it is installed and in PATH.")
        return None # Indicate failure
    except Exception as e:
        logging.error(f"An unexpected error occurred while running command '{' '.join(command_list)}': {e}")
        return None # Indicate failure


def install_python_dependencies():
    """Sets up the Python environment using Poetry."""
    logging.info("Starting Python dependencies setup using Poetry...")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    logging.info(f"Project root determined as: {project_root}")

    # 1. Check for pyproject.toml
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    if not os.path.exists(pyproject_path):
        logging.error(f"pyproject.toml not found at {pyproject_path}. Cannot proceed with Poetry setup.")
        return False
    logging.info(f"Found pyproject.toml at {pyproject_path}")

    # 2. Update Poetry Lockfile
    logging.info("Updating Poetry lockfile...")
    if not run_command(["poetry", "lock", "--no-cache"], cwd=project_root):
        logging.error("Failed to update Poetry lockfile.")
        return False
    logging.info("Poetry lockfile updated successfully.")

    # 3. Install Dependencies
    logging.info("Installing dependencies using Poetry...")
    if not run_command(["poetry", "install", "--no-root", "--no-interaction"], cwd=project_root):
        logging.error("Failed to install dependencies using Poetry.")
        return False
    logging.info("Poetry dependencies installed successfully.")

    # 4. Verify Key Packages
    logging.info("Verifying installation of key packages...")
    required_packages = ["flask", "chromadb", "langchain"] # Example list
    all_packages_verified = True
    for pkg in required_packages:
        logging.info(f"Verifying package: {pkg}...")
        # Construct the command to import the package
        # We need to get the python executable from the poetry env
        poetry_env_path_cmd = run_command(["poetry", "env", "info", "-p"], cwd=project_root)
        if not poetry_env_path_cmd or not poetry_env_path_cmd.stdout:
            logging.error("Failed to get Poetry environment path. Cannot verify packages.")
            return False
        
        env_path = poetry_env_path_cmd.stdout.strip()
        python_executable = os.path.join(env_path, "bin", "python")

        # Check if python executable exists
        if not os.path.exists(python_executable):
            logging.error(f"Python executable not found at {python_executable}. Cannot verify packages.")
            # Attempt to find it in Scripts for Windows
            python_executable_win = os.path.join(env_path, "Scripts", "python.exe")
            if os.path.exists(python_executable_win):
                python_executable = python_executable_win
                logging.info(f"Found Python executable at {python_executable} (Windows path)")
            else:
                logging.error(f"Python executable also not found at {python_executable_win}. Cannot verify packages.")
                return False


        import_command = [python_executable, "-c", f"import {pkg}"]
        
        # Using run_command to check the import
        # We set check_exit_code=True (default) so it returns None on failure
        verify_process = run_command(import_command, cwd=project_root)
        if verify_process is None: # run_command returns None on failure
            logging.error(f"Failed to verify package '{pkg}'. It might not be installed correctly in the Poetry environment.")
            all_packages_verified = False
        else:
            logging.info(f"Package '{pkg}' verified successfully.")
    
    if not all_packages_verified:
        logging.error("One or more key packages could not be verified. Please check the Poetry environment and installation logs.")
        # Depending on strictness, you might want to return False here
        # For now, we'll log the error and continue, as graphrag installation is separate
    else:
        logging.info("All key packages verified successfully.")

    # 5. Create Poetry Activation Script (Original Step 6)
    logging.info("Attempting to create Poetry activation script...")
    poetry_env_path_cmd = run_command(["poetry", "env", "info", "-p"], cwd=project_root)
    if not poetry_env_path_cmd or not poetry_env_path_cmd.stdout:
        logging.warning("Failed to get Poetry environment path. Cannot create activation script.")
        # This is optional, so we don't return False, just log a warning.
    else:
        env_path = poetry_env_path_cmd.stdout.strip()
        activate_script_name = "activate-poetry-env.sh" # For Linux/macOS
        activate_script_path = os.path.join(project_root, activate_script_name)
        
        actual_activate_script = os.path.join(env_path, "bin", "activate")
        if platform.system().lower() == "windows":
            # Windows uses a different script name and path structure usually
            actual_activate_script = os.path.join(env_path, "Scripts", "activate")
            # The wrapper script might need to be a .bat or .ps1 file for Windows
            # For simplicity, we'll stick to a .sh style for now, user might need to adjust for Windows
            # Or, we can create a .bat file as well.
            # activate_script_name = "activate-poetry-env.bat"
            # activate_script_path = os.path.join(project_root, activate_script_name)


        if not os.path.exists(actual_activate_script):
            logging.warning(f"Actual activation script not found at {actual_activate_script}. Cannot create wrapper script.")
        else:
            try:
                with open(activate_script_path, "w") as f:
                    if platform.system().lower() == "windows":
                        # Create a .bat file for Windows
                        activate_script_name_bat = "activate-poetry-env.bat"
                        activate_script_path_bat = os.path.join(project_root, activate_script_name_bat)
                        f_bat = open(activate_script_path_bat, "w")
                        f_bat.write(f'@echo off\ncall "{actual_activate_script}"\n')
                        f_bat.close()
                        os.chmod(activate_script_path_bat, 0o755)
                        logging.info(f"Poetry activation script created at {activate_script_path_bat}")
                        # Remove the .sh file if we created a .bat instead for Windows
                        if os.path.exists(activate_script_path): os.remove(activate_script_path)

                    else: # For Linux/macOS
                        f.write(f"#!/bin/bash\n")
                        f.write(f"# Wrapper script to activate the Poetry virtual environment\n")
                        f.write(f"source \"{actual_activate_script}\"\n")
                        os.chmod(activate_script_path, 0o755) # Make it executable
                        logging.info(f"Poetry activation script created at {activate_script_path}")

            except IOError as e:
                logging.warning(f"Could not write activation script: {e}")

    # 6. Install graphrag (Original Step 7)
    logging.info("Starting graphrag installation process...")
    graphrag_target_version = "1.2.1.dev27" # As specified
    # Corrected path assuming setup.py is in scripts/ and dependencies/ is at project root
    graphrag_tar_gz_name = f"graphrag-{graphrag_target_version}.tar.gz"
    graphrag_local_path = os.path.join(project_root, "dependencies", graphrag_tar_gz_name)
    
    # Determine Python executable in Poetry environment
    poetry_env_path_cmd = run_command(["poetry", "env", "info", "-p"], cwd=project_root)
    if not poetry_env_path_cmd or not poetry_env_path_cmd.stdout:
        logging.error("Failed to get Poetry environment path. Cannot proceed with graphrag installation.")
        return False
    env_path = poetry_env_path_cmd.stdout.strip()
    python_executable = os.path.join(env_path, "bin", "python")
    if platform.system().lower() == "windows":
        python_executable = os.path.join(env_path, "Scripts", "python.exe")

    if not os.path.exists(python_executable):
        logging.error(f"Python executable not found at {python_executable}. Cannot manage graphrag.")
        return False

    # Check currently installed graphrag version
    current_version = None
    logging.info("Checking current graphrag version...")
    # Use pip show as it's more reliable for getting version info
    # The command needs to be run with the poetry env python/pip
    pip_executable = os.path.join(os.path.dirname(python_executable), "pip")
    if platform.system().lower() == "windows":
         pip_executable = os.path.join(os.path.dirname(python_executable), "pip.exe")


    show_cmd_result = run_command([pip_executable, "show", "graphrag"], cwd=project_root, check_exit_code=False)

    if show_cmd_result and show_cmd_result.returncode == 0 and show_cmd_result.stdout:
        for line in show_cmd_result.stdout.splitlines():
            if line.startswith("Version:"):
                current_version = line.split(":")[1].strip()
                logging.info(f"Currently installed graphrag version: {current_version}")
                break
    else:
        logging.info("graphrag is not currently installed or 'pip show graphrag' failed.")

    if current_version == graphrag_target_version:
        logging.info(f"graphrag version {graphrag_target_version} is already installed. Skipping installation.")
    else:
        logging.info(f"graphrag version mismatch (found: {current_version}, target: {graphrag_target_version}) or not installed. Proceeding with installation.")
        if not os.path.exists(graphrag_local_path):
            logging.error(f"graphrag tarball not found at {graphrag_local_path}. Cannot install.")
            return False
        
        logging.info(f"Installing graphrag from {graphrag_local_path}...")
        # Using pip directly from the Poetry environment
        install_cmd = [pip_executable, "install", "--force-reinstall", graphrag_local_path]
        if not run_command(install_cmd, cwd=project_root):
            logging.error(f"Failed to install graphrag from {graphrag_local_path}.")
            return False
        logging.info("graphrag installation command executed. Verifying installation...")

        # Verify installation
        show_cmd_result_after_install = run_command([pip_executable, "show", "graphrag"], cwd=project_root, check_exit_code=False)
        installed_version = None
        if show_cmd_result_after_install and show_cmd_result_after_install.returncode == 0 and show_cmd_result_after_install.stdout:
            for line in show_cmd_result_after_install.stdout.splitlines():
                if line.startswith("Version:"):
                    installed_version = line.split(":")[1].strip()
                    break
        
        if installed_version == graphrag_target_version:
            logging.info(f"graphrag version {installed_version} installed successfully.")
        else:
            logging.error(f"graphrag installation verification failed. Expected {graphrag_target_version}, found {installed_version}.")
            return False

    return True


def build_llama_cpp():
    """Builds the Llama.cpp project."""
    logging.info("Starting Llama.cpp build process...")
    original_cwd = os.getcwd() # Remember original CWD
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    llama_cpp_dir = os.path.join(project_root, "llama.cpp")
    llama_cpp_zip_path = os.path.join(project_root, "dependencies", "llama.cpp.zip")

    # 1. Setup llama.cpp Directory
    if not os.path.exists(llama_cpp_dir):
        logging.info(f"Llama.cpp directory not found at {llama_cpp_dir}.")
        if os.path.exists(llama_cpp_zip_path):
            logging.info(f"Found llama.cpp.zip at {llama_cpp_zip_path}. Extracting...")
            try:
                with zipfile.ZipFile(llama_cpp_zip_path, "r") as zip_ref:
                    # We want to extract the contents of the zip such that a 'llama.cpp' folder is created at project_root
                    # Typically, the zip might contain a 'llama.cpp-master' or similar top-level folder.
                    # For robust extraction, let's extract all and then rename if necessary,
                    # or ensure the zip is structured to create 'llama.cpp' directly.
                    # For now, assume the zip creates a 'llama.cpp' folder when extracted to project_root.
                    zip_ref.extractall(project_root)
                
                # Verify if 'llama.cpp' was created. This depends on the zip structure.
                # If the zip creates 'llama.cpp-main' or similar, we would need to rename it.
                # For this task, we assume the zip extracts a folder named 'llama.cpp'.
                if not os.path.exists(llama_cpp_dir):
                     # Let's check common variations like 'llama.cpp-master' or 'llama.cpp-main'
                    extracted_folders = [name for name in os.listdir(project_root) if os.path.isdir(os.path.join(project_root, name)) and 'llama.cpp' in name and name != "llama.cpp"]
                    if extracted_folders:
                        actual_extracted_folder_name = extracted_folders[0] # Take the first match
                        logging.info(f"Zip extracted to {actual_extracted_folder_name}, renaming to llama.cpp")
                        os.rename(os.path.join(project_root, actual_extracted_folder_name), llama_cpp_dir)
                        if not os.path.exists(llama_cpp_dir): # Check again after rename
                             logging.error(f"Failed to find or rename extracted folder to {llama_cpp_dir}.")
                             return False
                    else:
                        logging.error(f"Llama.cpp directory not found at {llama_cpp_dir} after extraction. The zip might have an unexpected structure.")
                        return False
                logging.info(f"Successfully extracted llama.cpp to {llama_cpp_dir}")
            except zipfile.BadZipFile:
                logging.error(f"Error: The file at {llama_cpp_zip_path} is not a valid zip file.")
                return False
            except Exception as e:
                logging.error(f"Failed to extract {llama_cpp_zip_path}: {e}")
                return False
        else:
            logging.error(f"Llama.cpp zip file not found at {llama_cpp_zip_path}. Cannot proceed with build.")
            return False
    else:
        logging.info(f"Llama.cpp directory found at {llama_cpp_dir}.")

    # 2. Define llama-server executable path (OS-dependent)
    llama_server_exe_name = "llama-server.exe" if platform.system() == "Windows" else "llama-server"
    # Standard location after CMake build
    llama_server_path_candidates = [
        os.path.join(llama_cpp_dir, "build", "bin", llama_server_exe_name), # Linux/macOS typical
        os.path.join(llama_cpp_dir, "build", "bin", "Release", llama_server_exe_name), # Windows typical
        os.path.join(llama_cpp_dir, llama_server_exe_name), # If built in-source (less common with CMake but possible)
        os.path.join(llama_cpp_dir, "Release", llama_server_exe_name), # Older Visual Studio build output location
        os.path.join(llama_cpp_dir, "build", llama_server_exe_name) # Another possible location
    ]
    
    llama_server_exe = ""
    for candidate_path in llama_server_path_candidates:
        if os.path.exists(candidate_path) and os.access(candidate_path, os.X_OK):
            llama_server_exe = candidate_path
            logging.info(f"Found existing llama-server executable at: {llama_server_exe}")
            break
    
    # 3. Check Existing Build
    if llama_server_exe: # If a plausible executable was found
        logging.info(f"Attempting to verify existing Llama.cpp build by running: {llama_server_exe} --version")
        version_check_result = run_command([llama_server_exe, "--version"], cwd=llama_cpp_dir, check_exit_code=False)
        if version_check_result and version_check_result.returncode == 0 and version_check_result.stdout:
            # Llama.cpp server --version output is minimal, often just the version number or build info.
            # It might also exit with a non-zero code if it expects other arguments,
            # so we check for non-empty stdout as a basic sign of life.
            # A more robust check might involve parsing specific version patterns if available.
            logging.info(f"Llama-server --version stdout: {version_check_result.stdout.strip()}")
            logging.info("Existing Llama.cpp build seems functional. Skipping rebuild.")
            os.chdir(original_cwd)
            return True
        else:
            logging.warning("Existing Llama.cpp build found, but '--version' command failed or gave unexpected output. Proceeding with rebuild.")
            # It's possible the server binary exists but is from a failed/partial build, or --version isn't supported as expected.
            if version_check_result:
                logging.warning(f"Llama-server --version exit code: {version_check_result.returncode}, stderr: {version_check_result.stderr.strip()}")


    # 4. Build Process
    logging.info("Starting Llama.cpp build process...")
    try:
        os.chdir(llama_cpp_dir) # Change CWD to llama.cpp for build steps

        # Clean Previous Build
        build_dir = os.path.join(llama_cpp_dir, "build") # Relative to current dir (llama_cpp_dir)
        if os.path.exists(build_dir):
            logging.info(f"Removing existing build directory: {build_dir}")
            shutil.rmtree(build_dir)
        
        logging.info(f"Creating new build directory: {build_dir}")
        os.makedirs(build_dir)
        
        os.chdir(build_dir) # Change CWD to the new build directory

        # Configure CMake
        logging.info("Configuring Llama.cpp with CMake...")
        cmake_configure_command = ["cmake", ".."]
        # Note: Windows CMake generator logic could be added here if needed.
        # e.g., if platform.system() == "Windows": cmake_configure_command.extend(["-G", "Visual Studio 17 2022"])
        configure_result = run_command(cmake_configure_command, cwd=os.getcwd()) # cwd is now build_dir
        if not configure_result or configure_result.returncode != 0:
            logging.error("CMake configuration failed.")
            os.chdir(original_cwd)
            return False
        
        # Build Project
        logging.info("Building Llama.cpp with CMake...")
        # Using --parallel for potentially faster builds, adjust if needed
        build_command = ["cmake", "--build", ".", "--config", "Release", "--parallel"] 
        build_result = run_command(build_command, cwd=os.getcwd()) # cwd is still build_dir
        if not build_result or build_result.returncode != 0:
            logging.error("CMake build failed.")
            os.chdir(original_cwd)
            return False
        
        logging.info("Llama.cpp build completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred during the Llama.cpp build process: {e}")
        os.chdir(original_cwd) # Ensure CWD is reset on any exception
        return False
    finally:
        os.chdir(original_cwd) # Always change back to original CWD

    # 5. Verify Build (after building)
    # Re-check for the server executable in expected locations
    llama_server_exe_final = ""
    for candidate_path in llama_server_path_candidates: # Use the same candidates as before
        # Ensure candidate_path is absolute for os.path.exists and os.access checks
        abs_candidate_path = os.path.join(llama_cpp_dir, os.path.relpath(candidate_path, llama_cpp_dir)) if not os.path.isabs(candidate_path) else candidate_path

        # We need to reconstruct the absolute path if candidate_path was relative to llama_cpp_dir
        # More simply, redefine candidates based on the now existing build_dir
    
    # Let's redefine paths based on where it *should* be after build
    # These paths are relative to llama_cpp_dir for clarity in this section
    final_server_exe_name = "llama-server.exe" if platform.system() == "Windows" else "llama-server"
    
    # Potential locations for the built executable
    # Note: these are relative to llama_cpp_dir for the check
    built_server_path_candidates = []
    if platform.system() == "Windows":
        # Windows builds often place executables in a subdirectory named after the configuration (e.g., Release)
        built_server_path_candidates.append(os.path.join("build", "bin", "Release", final_server_exe_name))
        built_server_path_candidates.append(os.path.join("build", "bin", final_server_exe_name)) # Less common for MSVC
        built_server_path_candidates.append(os.path.join("build", "Release", final_server_exe_name)) # If "bin" is not used
    else: # Linux/macOS
        built_server_path_candidates.append(os.path.join("build", "bin", final_server_exe_name))
        built_server_path_candidates.append(os.path.join("build", final_server_exe_name)) # If not in a 'bin' subdirectory

    
    found_built_server_path = None
    for relative_candidate in built_server_path_candidates:
        abs_candidate_path = os.path.join(llama_cpp_dir, relative_candidate)
        if os.path.exists(abs_candidate_path) and os.access(abs_candidate_path, os.X_OK):
            found_built_server_path = abs_candidate_path
            logging.info(f"Llama-server executable found at {found_built_server_path} after build and is executable.")
            break
            
    if found_built_server_path:
        # Optionally, run --version again to be absolutely sure
        verify_run = run_command([found_built_server_path, "--version"], cwd=llama_cpp_dir, check_exit_code=False)
        if verify_run and verify_run.returncode == 0 and verify_run.stdout:
             logging.info(f"Post-build verification with --version successful: {verify_run.stdout.strip()}")
        elif verify_run: # Command ran but non-zero exit or no stdout
            logging.warning(f"Post-build --version check ran but indicated potential issues. Exit code: {verify_run.returncode}, stdout: '{verify_run.stdout.strip()}', stderr: '{verify_run.stderr.strip()}'")
            # Depending on strictness, this could be a failure. For now, we accept it if the file exists.
        else: # run_command returned None
            logging.warning("Post-build --version check command failed to execute.")
        # os.chdir(original_cwd) # CWD is reset in finally block
        return True
    else:
        logging.error(f"Llama-server executable not found or not executable in expected locations after build.")
        # Log contents of common bin directories for diagnostics
        common_bin_dirs = [
            os.path.join(llama_cpp_dir, "build", "bin"),
            os.path.join(llama_cpp_dir, "build", "bin", "Release"), # Windows
            os.path.join(llama_cpp_dir, "build")
        ]
        for bin_dir_path in common_bin_dirs:
            if os.path.exists(bin_dir_path) and os.path.isdir(bin_dir_path):
                try:
                    logging.info(f"Contents of {bin_dir_path}: {os.listdir(bin_dir_path)}")
                except Exception as e:
                    logging.info(f"Could not list contents of {bin_dir_path}: {e}")
            else:
                logging.info(f"Diagnostic directory {bin_dir_path} does not exist or is not a directory.")
        # os.chdir(original_cwd) # CWD is reset in finally block
        return False


def main(args):
    """Main function to run setup checks."""
    system_id = get_system_id()
    logging.info(f"Detected System ID: {system_id}")

    initial_checks_passed = True
    poetry_available = False # Flag to track if poetry is available

    if not args.skip_initial_checks:
        logging.info("Running initial dependency checks...")
        checks = {
            "Python >= 3.12": check_python,
            "Node.js": check_node,
            "npm": check_npm,
            "CMake": check_cmake, # CMake is crucial for Llama.cpp
            "Poetry": check_poetry,
            "SQLite": check_sqlite,
        }
        for check_name, check_func in checks.items():
            passed = check_func()
            if not passed:
                logging.error(f"{check_name} check failed.")
                initial_checks_passed = False
            else:
                logging.info(f"{check_name} check passed.")
            if check_name == "Poetry" and passed:
                poetry_available = True
            if check_name == "CMake" and not passed: # Specific check for CMake for Llama.cpp
                logging.warning("CMake check failed. This is required for Llama.cpp compilation.")
                # We don't exit here, but build_llama_cpp might fail later if CMake is truly missing

        if not initial_checks_passed:
            logging.error("One or more initial dependency checks failed. Please review the logs.")
            if not poetry_available:
                logging.error("Poetry is not installed. Cannot proceed with Python dependency installation. Exiting.")
                return
        else:
            logging.info("All initial dependency checks passed.")
    else: # Initial checks skipped
        logging.info("Skipping initial dependency checks as per --skip-initial-checks.")
        # Crucial checks even if skipped: Poetry for Python part, CMake for Llama.cpp
        poetry_available = check_poetry()
        if not poetry_available:
            logging.error("Poetry is not installed, but --skip-initial-checks was used. "
                          "Cannot proceed with Python dependency installation. Exiting.")
            return
        logging.info("Poetry check passed (or assumed to be present due to skip).")
        if not check_cmake():
             logging.warning("CMake check failed (or was skipped but is not found). "
                             "This is required for Llama.cpp compilation.")
        else:
            logging.info("CMake check passed (or assumed to be present due to skip).")


    # Proceed with Python environment setup
    if poetry_available:
        if not install_python_dependencies():
            logging.error("Python dependency setup failed. Please review the logs. Exiting.")
            return
        else:
            logging.info("Python dependency setup completed successfully.")
    else:
        # This should be caught by earlier exits if Poetry is missing.
        logging.info("Skipping Python dependency setup as Poetry is not available.")

    # Proceed with Llama.cpp build
    if not build_llama_cpp():
        logging.error("Llama.cpp build failed. Please review the logs.")
        # Decide if this is a critical failure that should stop the script
        # return
    else:
        logging.info("Llama.cpp build process completed successfully.")


    logging.info("Setup script finished.")


def setup_frontend():
    """Sets up the frontend project."""
    logging.info("Starting frontend setup process...")
    original_cwd = os.getcwd()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    frontend_dir = os.path.join(project_root, "lpm_frontend")

    if not os.path.isdir(frontend_dir):
        logging.error(f"Frontend directory not found: {frontend_dir}")
        return False

    try:
        os.chdir(frontend_dir)
        logging.info(f"Changed working directory to: {frontend_dir}")

        # 3. Install Dependencies
        logging.info("Installing frontend dependencies with npm install...")
        # run_command already logs the command, stdout, and stderr.
        # It returns the process object on success, None on failure (like command not found or non-zero exit if check_exit_code=True).
        # We expect run_command to handle the check_exit_code internally and log errors.
        npm_install_result = run_command(["npm", "install"], cwd=frontend_dir) # cwd is technically already frontend_dir, but explicit is fine

        if npm_install_result is None or npm_install_result.returncode != 0:
            logging.error("npm install command failed or returned non-zero exit code.")
            # run_command already logs details of the failure (stdout/stderr)
            return False
        logging.info("npm install completed successfully.")

        # 4. Verify Installation
        node_modules_path = os.path.join(frontend_dir, "node_modules")
        if not os.path.isdir(node_modules_path):
            logging.error(f"node_modules directory not found at {node_modules_path} after npm install.")
            logging.error("Frontend dependencies installation failed verification.")
            return False
        
        logging.info(f"node_modules directory found at {node_modules_path}. Frontend dependencies verified.")

    except Exception as e:
        logging.error(f"An unexpected error occurred during frontend setup: {e}")
        return False
    finally:
        os.chdir(original_cwd)
        logging.info(f"Restored working directory to: {original_cwd}")
    
    return True # Placeholder


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Setup Script")
    parser.add_argument(
        "--skip-initial-checks",
        action="store_true",
        help="Skip initial dependency checks (Python, Node, CMake, etc.). Poetry check will still run if not skipped."
    )
    args = parser.parse_args()
    main(args)
