# 非 Docker 本地部署指南

本指南提供分步说明，指导您如何在本地非 Docker 环境中使用提供的 Python 脚本来设置、启动、配置和停止应用程序及其服务（包括 Llama.cpp 服务器）。

## 先决条件

在开始之前，请确保您已安装以下工具：

*   **Python**: 版本 3.12 或更高。
    *   检查命令: `python --version` 或 `python3 --version`
*   **Node.js**: 版本 18 或更高 (包含 npm)。
    *   检查命令: `node -v`
*   **npm**: 通常随 Node.js 一起安装。
    *   检查命令: `npm --version`
*   **CMake**: 用于编译 Llama.cpp。
    *   检查命令: `cmake --version`
*   **Poetry**: 用于 Python 依赖管理。
    *   检查命令: `poetry --version`
    *   安装: 请遵循 [Poetry 官方安装指南](https://python-poetry.org/docs/#installation)。
*   **SQLite**: 用于应用程序数据库。
    *   检查命令: `sqlite3 --version`
*   **C++ 编译器**: Llama.cpp 编译所需。
    *   Linux: g++ 或 clang (例如, `sudo apt-get install build-essential`)
    *   macOS: Apple Clang (Xcode 命令行工具: `xcode-select --install`)
    *   Windows: MSVC (Visual Studio C++ workload)

## 初始设置

1.  **克隆仓库**:
    ```bash
    git clone <repository_url> # 将 <repository_url> 替换为实际的 URL
    cd <repository_name>      # 将 <repository_name> 替换为克隆的目录名称
    ```

2.  **环境配置 (`.env` 文件)**:
    本项目使用 `.env` 文件进行配置。请在项目根目录中创建一个名为 `.env` 的文件，并填入以下基本变量。根据您的本地环境需要调整路径和端口。

    ```env
    # 模型、数据和其他资源的基础目录
    # Linux/macOS 示例:
    LOCAL_BASE_DIR=./resources 
    # Windows 示例 (确保使用正斜杠或转义反斜杠):
    # LOCAL_BASE_DIR=C:/GraphRAG/resources

    # 服务端口
    LOCAL_APP_PORT=8002
    LOCAL_FRONTEND_PORT=3000

    # 数据库和日志路径 (通常相对于 LOCAL_BASE_DIR 或项目根目录)
    CHROMA_PERSIST_DIRECTORY=${LOCAL_BASE_DIR}/data/chroma_db 
    SQLITE_DB_PATH=${LOCAL_BASE_DIR}/data/sqlite/lpm.db
    LOCAL_LOG_DIR=./logs

    # --- 模型配置 (示例 - 根据您的模型需求调整) ---
    # 如果像 init_chroma.py 这样的脚本在设置过程中依赖这些变量，它们可能至关重要。
    # 如果您的设置过程依赖于特定的模型配置，请确保已设置这些变量。
    # 示例:
    # LLM_PROVIDER=ollama
    # OLLAMA_EMBEDDING_MODEL_NAME=nomic-embed-text
    # OLLAMA_BASE_URL=http://localhost:11434
    # OLLAMA_CHAT_MODEL_NAME=mistral:7b-instruct-v0.2-q4_K_M
    # OPENAI_API_KEY=your_openai_api_key_if_using_openai
    # OPENAI_CHAT_MODEL_NAME=gpt-3.5-turbo
    # OPENAI_EMBEDDING_MODEL_NAME=text-embedding-ada-002

    # 主机地址 (本地设置通常为 127.0.0.1)
    HOST_ADDRESS=127.0.0.1
    ```
    **注意**: 确保 `LOCAL_BASE_DIR` 指向一个已存在的目录，或者应用程序可以在该位置创建它。如果 `data/chroma_db` 和 `data/sqlite` 等子目录不存在，安装脚本会在此路径下创建它们。

3.  **运行设置脚本**:
    此脚本检查依赖项，使用 Poetry 设置 Python 环境，编译 Llama.cpp，并安装前端依赖项。
    ```bash
    python scripts/setup.py
    ```
    *   检查控制台输出是否有任何错误。
    *   详细日志可在 `logs/setup.log` 中找到 (如果 `setup.py` 未配置为文件日志记录，则可能仅输出到控制台；请参考其输出)。

4.  **激活 Python 环境**:
    `setup.py` 完成后，激活 Poetry 虚拟环境：
    *   **推荐**:
        ```bash
        poetry shell
        ```
    *   **备选方案**:
        *   在 Linux/macOS 上: `source activate-poetry-env.sh` (此脚本应由 `setup.py` 在项目根目录中生成)。
        *   在 Windows 上: `activate-poetry-env.bat` (此脚本应由 `setup.py` 在项目根目录中生成)。

## 启动服务

设置完成并激活 Python 环境后：

1.  **启动所有服务 (后端和前端)**:
    ```bash
    python scripts/start.py
    ```
    此命令将启动后端服务器和前端开发服务器。

2.  **仅启动后端**:
    如果您只需要后端运行 (例如，用于 API 访问)：
    ```bash
    python scripts/start.py --backend-only
    ```

3.  **验证**:
    *   `start.py` 的控制台输出将指示服务可访问的 URL (例如，后端: `http://localhost:8002`，前端: `http://localhost:3000`)。
    *   检查以下日志文件以获取详细输出和错误：
        *   `logs/start.log` (用于启动脚本本身)
        *   `logs/backend.log` (用于后端应用程序)
        *   `logs/frontend.log` (用于前端开发服务器)

## 停止服务

要停止由 `start.py` 启动的所有服务：

1.  **停止所有服务**:
    ```bash
    python scripts/stop.py
    ```
    此脚本会停止后端、前端，并尝试清理由后端启动的任何 Llama 服务器进程。

2.  **在自定义端口上停止 Llama 服务器**:
    如果 Llama 服务器 (可能由 `scripts/start.py` 调用的 `scripts/start_local.sh` 启动) 运行在非默认端口上 (`stop.py` 假定直接 Llama 服务器清理的默认端口为 8080)，您可以指定其端口：
    ```bash
    python scripts/stop.py --llama-port <your_llama_server_port>
    ```

3.  **日志文件**:
    *   检查 `logs/stop.log` 以获取有关停止过程的详细信息。

## 配置说明

*   配置应用程序 (端口、路径、模型设置) 的主要方法是通过项目根目录中的 `.env` 文件。
*   模型配置，例如模型文件的路径或特定的 LLM 参数，通常在 `.env` 文件中定义。后端服务在加载和与模型交互时会读取这些变量。请确保在启动服务之前正确设置这些变量。

## 故障排除

*   **端口冲突**:
    *   如果由于“地址已在使用中 (address already in use)”而导致服务无法启动，请检查哪个进程正在使用该端口：
        *   Linux/macOS: `sudo lsof -i :<port_number>`
        *   Windows: `netstat -ano | findstr :<port_number>` (然后在任务管理器中查找 PID)
    *   在您的 `.env` 文件中更改冲突的端口 (`LOCAL_APP_PORT`, `LOCAL_FRONTEND_PORT`) 并重新启动。
*   **构建失败 (Llama.cpp)**:
    *   确保 C++ 编译器 (g++, Clang, 或 MSVC) 和 CMake 已正确安装并在系统的 PATH 中可用。
    *   检查 `logs/setup.log` 或 `setup.py` 的控制台输出以获取特定的 CMake 或编译错误。
*   **Python/Node.js 版本问题**:
    *   验证您安装的版本是否满足先决条件。使用像 `pyenv` (用于 Python) 或 `nvm` (用于 Node.js) 这样的工具可以帮助管理多个版本。
*   **前端问题 (`npm install` 或 `npm run dev` 问题)**:
    *   确保 Node.js 和 npm 已正确安装并可访问。
    *   如果 `npm install` 无法下载包，请检查网络问题。
    *   如果 `npm run dev` 失败，请检查 `logs/frontend.log`。
    *   作为前端依赖问题的最后手段，您可以尝试删除 `lpm_frontend/node_modules` 目录和 `lpm_frontend/package-lock.json` 文件，然后重新运行 `python scripts/setup.py`，让它尝试重新安装前端依赖项。

---

本指南应能帮助您在本地运行应用程序。如需进一步协助，请参阅主要的 `README.md` 或在仓库中提交 issue。
