# Data Models Overview

This document outlines the primary data storage models used in the application, covering both the structured SQL database (managed with SQLAlchemy) and the ChromaDB vector store used for semantic search.

## 1. SQL Database Models (SQLAlchemy)

The SQL database (SQLite by default for local setup) stores structured application data, user information, configurations, and metadata related to AI processes and content. The following describes key tables based on their definitions in the project's Python model files.

### User and Configuration Models

*   **Table Name**: `user_llm_configs` (Source: `lpm_kernel/api/models/user_llm_config.py`)
    *   **Purpose**: Stores user-specific configurations for Large Language Models (LLMs), including separate settings for chat, embedding, and thinking models.
    *   **Key Columns/Fields**:
        *   `id`: `Integer`, PK, autoincrement.
        *   `provider_type`: `String(50)`, nullable=False, default='openai', comment='Provider type (e.g., openai)'.
        *   `key`: `String(200)`, nullable=True, comment='Common API key for provider-specific configurations'.
        *   `chat_endpoint`: `String(200)`, nullable=True, comment='Chat API endpoint'.
        *   `chat_api_key`: `String(200)`, nullable=True, comment='Chat API key'.
        *   `chat_model_name`: `String(200)`, nullable=True, comment='Chat model name'.
        *   `embedding_endpoint`: `String(200)`, nullable=True, comment='Embedding API endpoint'.
        *   `embedding_api_key`: `String(200)`, nullable=True, comment='Embedding API key'.
        *   `embedding_model_name`: `String(200)`, nullable=True, comment='Embedding model name'.
        *   `thinking_model_name`: `String(200)`, nullable=True, comment='Thinking model name'.
        *   `thinking_endpoint`: `String(200)`, nullable=True, comment='Thinking API endpoint'.
        *   `thinking_api_key`: `String(200)`, nullable=True, comment='Thinking API key'.
        *   `created_at`: `DateTime`, default=datetime.utcnow, comment='Creation time'.
        *   `updated_at`: `DateTime`, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Update time'.
    *   **Note**: The `thinking_fields` mentioned in the previous version (related to migration `V20250420221300`) are not directly present as columns in this specific `UserLLMConfig` model class but might be handled dynamically or in a different related model if that migration applies to a different table or structure. This model focuses on provider endpoints and API keys.

*   **Table Name**: `loads` (Source: `lpm_kernel/models/load.py`)
    *   **Purpose**: Manages personal "Load" data, representing individual user profiles or persona instances, including avatar, instance ID, and status.
    *   **Key Columns/Fields**:
        *   `id`: `String(36)`, PK (intended as UUID).
        *   `name`: `String(255)`, nullable=False.
        *   `description`: `String`, nullable=True.
        *   `email`: `String(255)`, nullable=False, default="".
        *   `avatar_data`: `String`, nullable=True (stores base64 encoded avatar data).
        *   `instance_id`: `String(255)`, nullable=True (stores upload instance ID).
        *   `instance_password`: `String(255)`, nullable=True (stores upload instance password).
        *   `status`: `Enum("active", "inactive", "deleted", name="load_status")`, nullable=False, default="active".
        *   `created_at`: `DateTime`, nullable=False, server_default=func.now().
        *   `updated_at`: `DateTime`, nullable=False, server_default=func.now(), onupdate=func.now().

### L1 AI Layer Models (Source: `lpm_kernel/models/l1.py`)

These models support the creation and management of AI personas and their generated content, versioned for iteration.

*   **Table Name**: `l1_versions`
    *   **Purpose**: Manages different versions of L1 AI personas or their associated generated content.
    *   **Key Columns/Fields**:
        *   `version`: `Integer`, PK.
        *   `create_time`: `DateTime`, nullable=False, default=datetime.now.
        *   `status`: `String(50)`, nullable=False.
        *   `description`: `String(500)`, nullable=True.
    *   **Relationships**: Has one-to-many relationships with `L1Bio`, `L1Shade`, `L1Cluster`, `L1ChunkTopic`.

*   **Table Name**: `l1_bios`
    *   **Purpose**: Stores generated biographies for AI personas, linked to a specific L1 version.
    *   **Key Columns/Fields**:
        *   `id`: `Integer`, PK, autoincrement.
        *   `version`: `Integer`, FK to `l1_versions.version`, nullable=False.
        *   `content`: `String(10000)`, nullable=True.
        *   `content_third_view`: `String(10000)`, nullable=True.
        *   `summary`: `String(2000)`, nullable=True.
        *   `summary_third_view`: `String(2000)`, nullable=True.
        *   `create_time`: `DateTime`, nullable=False, default=datetime.now.
    *   **Relationships**: Belongs to `L1Version`.

*   **Table Name**: `l1_shades`
    *   **Purpose**: Stores personality nuances ("shades") or specific behavioral traits for AI personas, linked to an L1 version.
    *   **Key Columns/Fields**:
        *   `id`: `Integer`, PK, autoincrement.
        *   `version`: `Integer`, FK to `l1_versions.version`, nullable=False.
        *   `name`: `String(200)`, nullable=True.
        *   `aspect`: `String(200)`, nullable=True.
        *   `icon`: `String(100)`, nullable=True.
        *   `desc_third_view`: `String(1000)`, nullable=True.
        *   `content_third_view`: `String(2000)`, nullable=True.
        *   `desc_second_view`: `String(1000)`, nullable=True.
        *   `content_second_view`: `String(2000)`, nullable=True.
        *   `create_time`: `DateTime`, nullable=False, default=datetime.now.
    *   **Relationships**: Belongs to `L1Version`.

*   **Table Name**: `l1_clusters`
    *   **Purpose**: Stores clusters of related topics or concepts for a persona, linked to an L1 version. These clusters can include associated memory IDs and a cluster center representation.
    *   **Key Columns/Fields**:
        *   `id`: `Integer`, PK, autoincrement.
        *   `version`: `Integer`, FK to `l1_versions.version`, nullable=False.
        *   `cluster_id`: `String(100)`, nullable=True.
        *   `memory_ids`: `JSON`, nullable=True (stores a list of memory identifiers).
        *   `cluster_center`: `JSON`, nullable=True (stores the vector or representation of the cluster center).
        *   `create_time`: `DateTime`, nullable=False, default=datetime.now.
    *   **Relationships**: Belongs to `L1Version`.

*   **Table Name**: `l1_chunk_topics`
    *   **Purpose**: Associates topics and tags with specific document chunks, linked to an L1 version, for thematic analysis or retrieval.
    *   **Key Columns/Fields**:
        *   `id`: `Integer`, PK, autoincrement.
        *   `version`: `Integer`, FK to `l1_versions.version`, nullable=False.
        *   `chunk_id`: `String(100)`, nullable=True (identifier of the document chunk).
        *   `topic`: `String(500)`, nullable=True.
        *   `tags`: `JSON`, nullable=True.
        *   `create_time`: `DateTime`, nullable=False, default=datetime.now.
    *   **Relationships**: Belongs to `L1Version`.

### Specific Content Models

*   **Table Name**: `status_biography` (Source: `lpm_kernel/models/status_biography.py`)
    *   **Purpose**: Stores status updates or short biographical blurbs. Unlike `L1Bio`, this seems to be a more general or current status.
    *   **Key Columns/Fields**:
        *   `id`: `Integer`, PK, autoincrement=True.
        *   `content`: `Text`, nullable=False.
        *   `content_third_view`: `Text`, nullable=False.
        *   `summary`: `Text`, nullable=False.
        *   `summary_third_view`: `Text`, nullable=False.
        *   `create_time`: `DateTime`, nullable=False, server_default=func.now().
        *   `update_time`: `DateTime`, nullable=False, server_default=func.now(), onupdate=func.now().
    *   **Note**: This model does not have an explicit `instance_id` or `persona_id` FK in its definition, suggesting it might be globally applicable or linked implicitly.

### Document & File-based Memory Models

These tables are central to ingesting, processing, and managing documents and their derived data for memory and retrieval.

*   **Table Name**: `document` (Source: `lpm_kernel/file_data/models.py`, class `DocumentModel`)
    *   **Purpose**: Stores metadata about uploaded or processed documents.
    *   **Key Columns/Fields**:
        *   `id`: `Integer`, PK, autoincrement=True.
        *   `name`: `String(255)`, nullable=False.
        *   `title`: `String(255)`, nullable=True.
        *   `mime_type`: `String(100)`, nullable=True.
        *   `user_description`: `Text`, nullable=True.
        *   `url`: `String(1024)`, nullable=True.
        *   `document_size`: `Integer`, default=0.
        *   `raw_content`: `Text`, nullable=True.
        *   `insight`: `JSON`, nullable=True.
        *   `summary`: `JSON`, nullable=True.
        *   `keywords`: `JSON`, nullable=True.
        *   `extract_status`: `SQLAlchemyEnum(ProcessStatus)`, default=ProcessStatus.INITIALIZED.
        *   `embedding_status`: `SQLAlchemyEnum(ProcessStatus)`, default=ProcessStatus.INITIALIZED.
        *   `create_time`: `DateTime`, default=datetime.now.
        *   `update_time`: `DateTime`, default=datetime.utcnow, onupdate=datetime.utcnow.
    *   **Relationships**: Has a one-to-many relationship with `ChunkModel`.
    *   **Note**: The previous documentation mentioned `space_id`, `instance_id`, `user_id`, and `metadata_` which are not present in this `DocumentModel` definition. It seems `DocumentModel` is more generic.

*   **Table Name**: `chunk` (Source: `lpm_kernel/file_data/models.py`, class `ChunkModel`)
    *   **Purpose**: Stores individual chunks of text extracted from documents, which are then used for embeddings.
    *   **Key Columns/Fields**:
        *   `id`: `BigInteger`, PK.
        *   `document_id`: `BigInteger`, FK to `document.id`, nullable=False.
        *   `content`: `Text`, nullable=False.
        *   `has_embedding`: `Boolean`, default=False.
        *   `tags`: `JSON`, nullable=True.
        *   `topic`: `String(255)`, nullable=True.
        *   `create_time`: `DateTime`, default=datetime.utcnow.
    *   **Relationships**: Belongs to `DocumentModel`.
    *   **Note**: The previous documentation mentioned `index`, `page_number`, `status`, and `metadata_` which are not directly present in this `ChunkModel` definition. `has_embedding` serves as a status for embeddings.

*   **Table Name**: `memories` (Source: `lpm_kernel/models/memory.py`)
    *   **Purpose**: Stores metadata about files that constitute a form of "memory," possibly raw content or data files.
    *   **Key Columns/Fields**:
        *   `id`: `String(36)`, PK (intended as UUID).
        *   `name`: `String(255)`, nullable=False.
        *   `size`: `BigInteger`, nullable=False.
        *   `type`: `String(50)`, nullable=False (derived from file extension).
        *   `path`: `String(1024)`, nullable=False.
        *   `meta_data`: `JSON`, nullable=True.
        *   `document_id`: `String(36)`, nullable=True (associated document ID).
        *   `created_at`: `DateTime`, server_default=func.now().
        *   `updated_at`: `DateTime`, server_default=func.now(), onupdate=func.now().
        *   `status`: `Enum("active", "deleted")`, nullable=False, default="active".
    *   **Note**: The previous documentation mentioned `instance_id`. This is not directly in the model but could be part of `meta_data` or linked via `document_id` if documents are instance-specific.

### Collaboration/Space Models (Source: `lpm_kernel/models/space.py`)

These tables support multi-user collaboration, chat rooms, or distinct "spaces" for interaction.

*   **Table Name**: `spaces`
    *   **Purpose**: Defines distinct environments or "spaces" for discussions, including participants and objectives.
    *   **Key Columns/Fields**:
        *   `id`: `String`, PK.
        *   `space_share_id`: `String`, nullable=True.
        *   `title`: `String`, nullable=False (discussion topic).
        *   `objective`: `String`, nullable=False (discussion objective).
        *   `participants`: `JSON`, nullable=False (list of participants' endpoints).
        *   `host`: `String`, nullable=False (host's endpoint).
        *   `create_time`: `DateTime`, nullable=False.
        *   `status`: `Integer`, default=1 (discussion status: 1-discussion, 2-discussion ended).
        *   `conclusion`: `String`, nullable=True (discussion conclusion).
    *   **Relationships**: Has a one-to-many relationship with `SpaceMessage`.
    *   **Note**: The previous documentation mentioned `name`, `description`, `instance_id`, `user_id`, and `meta_data`. The current model uses `title` and `objective` for descriptive purposes and `participants`/`host` for user-like roles. `instance_id` is not directly present.

*   **Table Name**: `space_messages`
    *   **Purpose**: Stores messages exchanged within a specific space.
    *   **Key Columns/Fields**:
        *   `id`: `String`, PK.
        *   `space_id`: `String`, FK to `spaces.id`, nullable=False.
        *   `sender_endpoint`: `String`, nullable=False (sender's endpoint).
        *   `content`: `String`, nullable=False (message content).
        *   `message_type`: `String`, nullable=False.
        *   `round`: `Integer`, default=0 (message round).
        *   `create_time`: `DateTime`, nullable=False.
        *   `role`: `String`, default="participant" (message sender's role).
    *   **Relationships**: Belongs to `Space`.
    *   **Note**: The previous documentation mentioned `sender` (now `sender_endpoint` and `role`), `message` (now `content`), `raw_message`, `search_record`, and `meta_data`. Some of these (like `raw_message`, `search_record`) might be part of the `content` if it's JSON, or handled differently.

## 2. ChromaDB (Vector Store)

ChromaDB is utilized as a vector store to enable semantic search capabilities, which are fundamental for Retrieval Augmented Generation (RAG) and long-term memory functionalities. It stores vector embeddings of text data, allowing the system to find relevant information based on semantic similarity rather than just keyword matching.

*   **Purpose**:
    *   Store dense vector representations (embeddings) of text segments (chunks).
    *   Enable efficient similarity searches to retrieve chunks relevant to a user's query or a given context.
    *   Support the `L2/memory_manager.py` in providing contextual information to the LLM for generating informed responses.

*   **Key Collections**:
    Based on `scripts/init_chroma.py` and common RAG patterns:

    *   **`documents`**:
        *   **Purpose**: This collection is initialized by `scripts/init_chroma.py`. While its name might suggest storage of full document embeddings, in RAG systems, it's more common to store embeddings of *chunks* of documents for granular retrieval. This collection might be used for storing some form of document-level representation or metadata, or it could be a misnomer and actually store chunk embeddings if `document_chunks` is not the primary one. Given `document_chunks` is also initialized, the distinction needs to be clarified by examining usage in `memory_manager.py`.
        *   **Note**: `init_chroma.py` explicitly mentions initializing a "documents" collection.

    *   **`document_chunks`**:
        *   **Purpose**: This is typically the primary collection for RAG. It stores embeddings for individual, smaller segments (chunks) of text extracted from processed documents. Storing embeddings of chunks allows for more granular and targeted retrieval of relevant information.
        *   **Explicitly Initialized**: `init_chroma.py` confirms the creation of this collection with specific metadata.

*   **Typical Data Structure within Collections**:
    Each entry in a ChromaDB collection (especially `document_chunks`) typically consists of:

    *   **Embeddings**:
        *   The numerical vector generated by an embedding model (e.g., OpenAI's `text-embedding-ada-002`, or a model from Ollama like `nomic-embed-text`).
        *   The dimensionality of this vector is determined by the chosen embedding model.

    *   **Metadata**:
        *   A dictionary of key-value pairs associated with each embedding, crucial for filtering and providing context.
        *   `source_document_id`: The ID (e.g., from the `document` SQL table) of the document from which the chunk originated.
        *   `chunk_id`: The ID (e.g., from the `chunk` SQL table) of this specific text chunk.
        *   `text_content` (optional but common): The actual text of the chunk can be stored alongside its embedding for quick previews or to avoid a separate lookup to the SQL database if only the text is needed.
        *   Other relevant information: Page numbers, section titles, author, creation date, tags, etc., can be included to enhance search capabilities or provide richer context.

    *   **IDs**:
        *   Each entry in the collection has a unique ID, often corresponding to the `chunk_id`.

*   **Collection Metadata (as set by `init_chroma.py`)**:
    *   `hnsw:space`: "cosine" - Specifies that cosine similarity will be used to measure the distance (and thus similarity) between vectors.
    *   `dimension`: The dimensionality of the embeddings stored in the collection (e.g., 1536 for `text-embedding-ada-002`). This is dynamically detected and set by `scripts/init_chroma.py` based on the configured embedding model.

*   **Interaction**:
    *   **`lpm_kernel/file_data/embedding_service.py`**: Responsible for generating embeddings from text chunks using the configured embedding model.
    *   **`lpm_kernel/L2/memory_manager.py`**: Handles the storage of these embeddings (along with their metadata) into ChromaDB collections and executes queries against these collections to find semantically similar chunks based on a query embedding.
    *   The retrieved chunks are then used by the L2 (and subsequently L1/L0) layers to provide context to the LLM when generating responses, forming the core of the RAG pattern.

This overview should provide a foundational understanding of how data is structured and managed within the application. For precise schema details beyond what's inferred from model file paths and common field names, direct inspection of SQLAlchemy model classes is recommended.
