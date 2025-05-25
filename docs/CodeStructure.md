# Code Structure Overview

This document provides a guide to the code structure of the project, primarily focusing on the `lpm_kernel` (backend and AI logic) and `lpm_frontend` (user interface). Its goal is to serve as a map for navigating the codebase.

## 1. `lpm_kernel` Code Structure

The `lpm_kernel` directory contains the core backend services, AI logic, and data processing pipelines of the application.

### Introduction

`lpm_kernel` is the heart of the system, housing the layered AI architecture (L0, L1, L2), API definitions, data handling, and common utilities necessary for the application's backend operations.

### Key Subdirectories

*   **`L0/`**:
    *   **Description**: Houses the L0 AI Layer components. This layer is responsible for fundamental Large Language Model (LLM) interactions, including prompt generation, interfacing with various LLM backends, and handling raw responses.
    *   **Examples**: `l0_generator.py`, `prompt.py`.

*   **`L1/`**:
    *   **Description**: Contains the L1 AI Layer. This layer builds upon L0 to manage personas, generate specialized content (like biographies, status updates, topics of interest), and implement more nuanced agent-like behaviors.
    *   **Examples**: `l1_generator.py`, `bio.py`, `shade_generator.py`, `topics_generator.py`.

*   **`L2/`**:
    *   **Description**: Implements the L2 AI Layer. This layer is concerned with knowledge acquisition, long-term memory management, and advanced AI functionalities. It includes components for data processing pipelines (like `data_pipeline/` which may contain `graphrag_indexing/` for knowledge graph creation) and potentially model fine-tuning techniques (such as those in `dpo/` for Direct Preference Optimization).
    *   **Examples**: `memory_manager.py`, `l2_generator.py`.

*   **`api/`**:
    *   **Description**: Defines the external API endpoints that the frontend and other services interact with, likely built using a web framework like Flask or FastAPI. It's typically organized into subdomains based on functionality.
    *   **Examples**: Subdirectories like `documents/`, `kernel/`, `memories/`, `space/`, `upload/`. The main application setup (e.g., `app.py` for Flask) and specific request handlers for each domain reside here.

*   **`common/`**:
    *   **Description**: Provides shared utilities, modules, and base classes used across the `lpm_kernel`. This promotes code reuse and consistent design patterns.
    *   **Examples**: `llm.py` (for centralized LLM interaction logic), `repository/database_session.py` (for database connection management), base repository patterns, and common strategies like `strategy_openai.py` or `strategy_huggingface.py`.

*   **`configs/`**:
    *   **Description**: Manages system-wide configurations, including application settings, logging setup, paths, and external service credentials.
    *   **Examples**: `config.py`, `logging.py`.

*   **`database/`**:
    *   **Description**: Handles database-specific operations. This includes managing database connections (if not solely handled by `common/repository/`), schema definitions (especially if not using an ORM that defines models elsewhere), and database migration scripts and management.
    *   **Examples**: `migrations/` (containing schema migration files), `migration_manager.py`.

*   **`file_data/`**:
    *   **Description**: Responsible for all aspects of file processing. This includes handling uploads, extracting text, chunking content into manageable pieces, generating vector embeddings for semantic search, and interacting with vector databases like ChromaDB.
    *   **Examples**: `document_service.py` (for orchestrating file processing), `embedding_service.py` (for generating embeddings), `chunker.py` (for splitting text), and various `processors/` tailored for different file types (PDF, Markdown, etc.).

*   **`kernel/`**:
    *   **Description**: Contains core application logic and services that might orchestrate functions from the L0-L2 layers or provide specific business logic not fitting directly into those layers. It acts as a bridge or a service layer above the AI primitives.
    *   **Examples**: `note_service.py`, `chunk_service.py`, `l1_manager.py` (orchestrating L1 persona generation).

*   **`models/`**:
    *   **Description**: This directory (or subdirectories like `api/models/`, `file_data/models.py`) typically contains data model definitions. These can be ORM models (e.g., SQLAlchemy for relational database interactions) or Pydantic models used for API request/response validation and data structuring.
    *   **Note**: Based on the provided file list, specific model definitions might be co-located within their respective modules (e.g., `lpm_kernel/api/domains/space/models.py`).

### Key Files (Examples)

While many important files reside within the subdirectories listed above, some notable examples to reiterate include:

*   **`app.py`** (likely in `lpm_kernel/` or `lpm_kernel/api/`): The main application entry point, especially if using Flask or FastAPI, responsible for initializing and running the web server.
*   **`lpm_kernel/common/llm.py`**: Centralizes logic for interacting with different LLM providers.
*   **`lpm_kernel/L2/memory_manager.py`**: Core component for managing the AI's long-term memory, interacting with databases like SQLite and ChromaDB.
*   **`lpm_kernel/file_data/document_service.py`**: Orchestrates the processing of uploaded documents.

## 2. `lpm_frontend` Code Structure (Next.js & TypeScript)

The `lpm_frontend` directory contains the Next.js application, built with TypeScript, which serves as the user interface for the system.

### Introduction

`lpm_frontend` is responsible for rendering the user interface, managing client-side state, and interacting with the `lpm_kernel` backend to fetch and display data, as well as to trigger AI operations.

### Key `src/` Subdirectories

*   **`src/app/`**:
    *   **Description**: The core of modern Next.js (version 13+) applications using the App Router. This directory contains page definitions (e.g., `page.tsx`), layouts (`layout.tsx`), and route handlers (`route.ts`). Subfolders within `src/app/` define the application's routes.
    *   **Examples**: `src/app/dashboard/` (for dashboard pages), `src/app/home/` (for home page related components and routes).

*   **`src/components/`**:
    *   **Description**: Houses reusable UI components that are used across various pages and features of the application. These components encapsulate specific UI elements and logic.
    *   **Examples**: `chat/ChatInput.tsx`, `roleplay/RoleCard.tsx`, `Markdown/index.tsx` (for rendering Markdown content).

*   **`src/contexts/`**:
    *   **Description**: Contains React Context providers. Contexts are used for managing global state or sharing functionalities (like theme settings, authentication status, or global configurations) across different parts of the component tree without prop drilling.
    *   **Examples**: `AntdRegistry.tsx` (likely for Ant Design UI library integration).

*   **`src/hooks/`**:
    *   **Description**: Stores custom React hooks. Hooks are functions that let you “hook into” React state and lifecycle features from function components. Custom hooks allow for encapsulating and reusing stateful logic.
    *   **Examples**: `useSSE.tsx` (for handling Server-Sent Events, useful for real-time updates from the backend).

*   **`src/layouts/`**:
    *   **Description**: Defines the overall structure and layout templates for different sections of the application. These components typically wrap page content, providing consistent headers, footers, sidebars, or navigation menus.
    *   **Examples**: `DashboardLayout/`, `HeaderLayout/`.

*   **`src/service/`**:
    *   **Description**: Contains functions responsible for making API calls to the `lpm_kernel` backend. Each file often groups API calls related to a specific resource or feature. These services abstract the data fetching logic from the UI components.
    *   **Examples**: `memory.ts`, `role.ts`, `space.ts`, `upload.ts`. These typically use a utility function for making the actual HTTP requests.

*   **`src/store/`**:
    *   **Description**: Manages client-side state using a state management library. Based on filenames like `useUploadStore.ts` and `useSpaceStore.ts`, this project likely uses Zustand, a popular lightweight state management solution for React.
    *   **Examples**: `useModelConfigStore.ts`, `useTrainingStore.ts`.

*   **`src/types/`**:
    *   **Description**: Contains TypeScript type definitions and interfaces for data structures used throughout the frontend application. This helps ensure type safety and improves code maintainability.
    *   **Examples**: `chat.ts` (defining types for chat messages), `responseModal.ts` (defining types for API responses).

*   **`src/utils/`**:
    *   **Description**: A collection of utility functions and helper modules used across the frontend codebase.
    *   **Examples**: `request.ts` (a centralized utility for making HTTP API calls, often used by `src/service/` modules), `localStorage.ts` (for interacting with browser local storage), `chatStorage.ts`.

### Backend Interaction

*   The frontend (`lpm_frontend`) communicates with the `lpm_kernel` backend exclusively through HTTP API calls.
*   These API calls are typically defined and organized within the `src/service/` directory.
*   A central utility, often found at `src/utils/request.ts`, is commonly used to standardize these HTTP requests (e.g., setting headers, handling errors, managing base URLs).
*   Client-side state, including data fetched from the backend and UI-specific state, is managed by stores in `src/store/` (likely Zustand) and React Contexts/custom hooks where appropriate.

This structure provides a scalable and maintainable architecture for both the backend AI services and the frontend user interface.
