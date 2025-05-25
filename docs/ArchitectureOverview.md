# Architecture Overview

This document provides a high-level overview of the system's architecture, focusing on its layered approach to AI functionalities, primarily housed within the `lpm_kernel`. The architecture is designed in layers (L0, L1, L2) to separate concerns and build increasingly sophisticated AI capabilities.

## L0 - Core AI Layer

*   **Purpose**: The L0 layer is responsible for direct interaction with Large Language Models (LLMs). It handles fundamental tasks such as prompt construction, sending requests to various LLM backends (local or API-based, e.g., Ollama, OpenAI), and receiving the raw LLM-generated responses.
*   **Key Components (examples from `lpm_kernel/L0/`)**:
    *   `l0_generator.py`: Contains the core logic for generating text. It likely abstracts the complexities of different LLM providers and manages the request/response cycle.
    *   `prompt.py`: Provides utilities and templates for creating, formatting, and customizing prompts sent to the LLMs.
    *   `models.py`: Defines data structures for L0 inputs (e.g., prompt configurations) and outputs (e.g., raw LLM responses).
*   **Interaction**: L0 receives generation requests from higher layers (L1, L2) or directly from API services. It then interacts with the configured LLM and returns the unprocessed or minimally processed output.

## L1 - Persona & Agent Layer

*   **Purpose**: The L1 layer builds upon L0 to implement more specialized and persona-driven AI behaviors. It focuses on endowing the AI with a consistent character, generating content aligned with that persona (like biographies, status updates, or topical responses), and potentially managing agent-like interactions or decision-making.
*   **Key Components (examples from `lpm_kernel/L1/`)**:
    *   `l1_generator.py`: Orchestrates the various L1 functionalities, combining L0 outputs with persona constraints.
    *   `bio.py`, `status_bio_generator.py`, `topics_generator.py`, `shade_generator.py`: These modules are likely responsible for generating specific aspects of an AI's persona or character, such as its background story, current status, areas of expertise, or even nuanced personality traits ("shades").
    *   `prompt.py`: Contains L1-specific prompt engineering techniques, tailoring L0 prompts to elicit persona-consistent responses from the LLM.
*   **Interaction**: L1 utilizes L0 for core LLM generation tasks. It receives requests (e.g., "generate a bio for persona X") and provides more structured, persona-aware outputs to higher layers (L2) or directly to the application's APIs.

## L2 - Knowledge & Memory Layer

*   **Purpose**: The L2 layer is crucial for enabling the AI to learn, remember, and provide contextually relevant responses over time. It deals with long-term memory, knowledge retrieval from various data sources, data processing pipelines for ingesting and structuring knowledge, and potentially model fine-tuning (e.g., using Direct Preference Optimization - DPO) to align LLM behavior with user preferences or specific knowledge domains.
*   **Key Components (examples from `lpm_kernel/L2/` and `lpm_kernel/file_data/`)**:
    *   `l2_generator.py`: Orchestrates L2 functionalities, particularly for chat interactions that require memory retrieval and contextual understanding.
    *   `memory_manager.py`: A core component responsible for managing and accessing the AI's memories. This likely involves interaction with vector databases (ChromaDB) for semantic search and relational databases (SQLite) for structured memory or metadata.
    *   `data_pipeline/`: Contains tools and scripts for processing raw data (e.g., user documents) into usable knowledge. This includes sub-modules like `graphrag_indexing/` for creating knowledge graphs or structured indexes.
    *   `dpo/`: Includes scripts and modules related to Direct Preference Optimization, allowing for fine-tuning of LLMs based on collected preference data.
    *   `file_data/` (a closely related module that feeds L2):
        *   `embedding_service.py`: Generates vector embeddings for text data.
        *   `document_service.py`: Manages document processing and storage.
        *   `chunker.py`: Splits documents into manageable, semantically relevant chunks for embedding and retrieval.
*   **Interaction**: L2 interacts with L0/L1 for generating responses that are augmented with retrieved knowledge. It uses storage backends (SQLite for structured data/metadata, ChromaDB for vector embeddings) to persist and query memories. It provides high-level chat and interaction functionalities to the application API, enabling context-aware conversations.

## Data Flow Diagrams

Below are Mermaid.js diagrams illustrating typical data flows within the system.

### Memory Ingestion Flow

This diagram shows how a user-uploaded document is processed and stored for later retrieval.

```mermaid
graph LR
    A[User Upload via API] --> B(lpm_kernel/api/);
    B --> C{file_data Module};
    C -- Text Extraction, Chunking --> D(embedding_service.py);
    D -- Generates Embeddings --> E{L2 Layer};
    E -- Stores Chunks & Embeddings --> F(memory_manager.py);
    F --> G[ChromaDB (Vector Store)];
    F --> H[SQLite DB (Metadata)];
```

### Chat Interaction Flow

This diagram illustrates how a user query is processed using the layered architecture to generate a contextually relevant and persona-aware response.

```mermaid
graph LR
    subgraph User Interaction
        A[User Query via API]
    end

    subgraph System Processing
        A --> B(lpm_kernel/api/);
        B --> C{L2 Layer - l2_generator.py};
        C -- Query for Context --> D(memory_manager.py);
        D -- Retrieves Relevant Chunks --> C;
        C -- Enriched Context & Query --> E{L1 Layer - l1_generator.py};
        E -- Constructs Persona-Aware Prompt --> F{L0 Layer - l0_generator.py};
        F -- Sends Prompt to LLM --> G[LLM (Local/Remote)];
        G -- Raw LLM Response --> F;
        F -- Returns Response to L1 --> E;
        E -- Post-processes & Structures Response --> C;
        C -- Final Response Preparation --> B;
    end

    subgraph API Response
        B --> H[API Response to User]
    end
```

## Supporting Components

While the L0, L1, and L2 layers form the core AI logic, several other components support their operation:

*   **`lpm_kernel/api/`**: This module serves as the primary entry point for the functionalities provided by the L0, L1, and L2 layers. It exposes HTTP APIs that the frontend or other external services can interact with.
*   **`lpm_kernel/common/`**: Contains shared utilities and abstractions used across different layers. This might include wrappers for LLM interactions, database session management, common data structures, and logging utilities.
*   **`lpm_kernel/configs/`**: Manages system-wide configurations, such as paths, LLM settings, database connection details, and other operational parameters, often loaded from `.env` files or other configuration sources.

This layered architecture allows for modular development, easier maintenance, and the ability to progressively enhance the AI's capabilities by building upon foundational components.
