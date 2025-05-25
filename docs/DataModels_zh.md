# 数据模型概览

本文档概述了应用程序中使用的主要数据存储模型，涵盖了结构化的 SQL 数据库（使用 SQLAlchemy 管理）和用于语义搜索的 ChromaDB 向量存储。

## 1. SQL 数据库模型 (SQLAlchemy)

SQL 数据库（本地设置默认为 SQLite）存储结构化的应用程序数据、用户信息、配置以及与 AI 流程和内容相关的元数据。以下根据项目中 Python 模型文件的定义描述了关键表。

### 用户及配置模型

*   **表名**: `user_llm_configs` (源文件: `lpm_kernel/api/models/user_llm_config.py`)
    *   **用途**: 存储用户特定的大型语言模型 (LLM) 配置，包括聊天、嵌入和思考模型的独立设置。
    *   **关键列/字段**:
        *   `id`: `Integer`, PK, autoincrement。
        *   `provider_type`: `String(50)`, nullable=False, default='openai', comment='提供商类型 (例如 openai)'。
        *   `key`: `String(200)`, nullable=True, comment='用于特定提供商配置的通用 API 密钥'。
        *   `chat_endpoint`: `String(200)`, nullable=True, comment='聊天 API 端点'。
        *   `chat_api_key`: `String(200)`, nullable=True, comment='聊天 API 密钥'。
        *   `chat_model_name`: `String(200)`, nullable=True, comment='聊天模型名称'。
        *   `embedding_endpoint`: `String(200)`, nullable=True, comment='嵌入 API 端点'。
        *   `embedding_api_key`: `String(200)`, nullable=True, comment='嵌入 API 密钥'。
        *   `embedding_model_name`: `String(200)`, nullable=True, comment='嵌入模型名称'。
        *   `thinking_model_name`: `String(200)`, nullable=True, comment='思考模型名称'。
        *   `thinking_endpoint`: `String(200)`, nullable=True, comment='思考 API 端点'。
        *   `thinking_api_key`: `String(200)`, nullable=True, comment='思考 API 密钥'。
        *   `created_at`: `DateTime`, default=datetime.utcnow, comment='创建时间'。
        *   `updated_at`: `DateTime`, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间'。

*   **表名**: `loads` (源文件: `lpm_kernel/models/load.py`)
    *   **用途**: 管理个人 "Load" 数据，代表单个用户配置文件或 Persona 实例，包括头像、实例 ID 和状态。
    *   **关键列/字段**:
        *   `id`: `String(36)`, PK (预期为 UUID)。
        *   `name`: `String(255)`, nullable=False。
        *   `description`: `String`, nullable=True。
        *   `email`: `String(255)`, nullable=False, default=""。
        *   `avatar_data`: `String`, nullable=True (存储 base64 编码的头像数据)。
        *   `instance_id`: `String(255)`, nullable=True (存储上传实例 ID)。
        *   `instance_password`: `String(255)`, nullable=True (存储上传实例密码)。
        *   `status`: `Enum("active", "inactive", "deleted", name="load_status")`, nullable=False, default="active"。
        *   `created_at`: `DateTime`, nullable=False, server_default=func.now()。
        *   `updated_at`: `DateTime`, nullable=False, server_default=func.now(), onupdate=func.now()。

### L1 AI 层模型 (源文件: `lpm_kernel/models/l1.py`)

这些模型支持 AI Persona 及其生成内容的创建和管理，通常进行版本控制以支持迭代。

*   **表名**: `l1_versions`
    *   **用途**: 管理 L1 AI Persona 或其关联生成内容的不同版本。
    *   **关键列/字段**:
        *   `version`: `Integer`, PK。
        *   `create_time`: `DateTime`, nullable=False, default=datetime.now。
        *   `status`: `String(50)`, nullable=False。
        *   `description`: `String(500)`, nullable=True。
    *   **关系 (Relationships)**: 与 `L1Bio`, `L1Shade`, `L1Cluster`, `L1ChunkTopic` 存在一对多关系。

*   **表名**: `l1_bios`
    *   **用途**: 存储为 AI Persona 生成的个人简介，关联到特定的 L1 版本。
    *   **关键列/字段**:
        *   `id`: `Integer`, PK, autoincrement。
        *   `version`: `Integer`, FK to `l1_versions.version`, nullable=False。
        *   `content`: `String(10000)`, nullable=True。
        *   `content_third_view`: `String(10000)`, nullable=True。
        *   `summary`: `String(2000)`, nullable=True。
        *   `summary_third_view`: `String(2000)`, nullable=True。
        *   `create_time`: `DateTime`, nullable=False, default=datetime.now。
    *   **关系 (Relationships)**: 从属于 `L1Version`。

*   **表名**: `l1_shades`
    *   **用途**: 存储 AI Persona 的个性化特征 ("shades") 或特定行为特质，关联到 L1 版本。
    *   **关键列/字段**:
        *   `id`: `Integer`, PK, autoincrement。
        *   `version`: `Integer`, FK to `l1_versions.version`, nullable=False。
        *   `name`: `String(200)`, nullable=True。
        *   `aspect`: `String(200)`, nullable=True。
        *   `icon`: `String(100)`, nullable=True。
        *   `desc_third_view`: `String(1000)`, nullable=True。
        *   `content_third_view`: `String(2000)`, nullable=True。
        *   `desc_second_view`: `String(1000)`, nullable=True。
        *   `content_second_view`: `String(2000)`, nullable=True。
        *   `create_time`: `DateTime`, nullable=False, default=datetime.now。
    *   **关系 (Relationships)**: 从属于 `L1Version`。

*   **表名**: `l1_clusters`
    *   **用途**: 存储与 Persona 相关的集群化主题或概念，关联到 L1 版本。这些集群可包含关联的记忆 ID 和集群中心表示。
    *   **关键列/字段**:
        *   `id`: `Integer`, PK, autoincrement。
        *   `version`: `Integer`, FK to `l1_versions.version`, nullable=False。
        *   `cluster_id`: `String(100)`, nullable=True。
        *   `memory_ids`: `JSON`, nullable=True (存储记忆标识符列表)。
        *   `cluster_center`: `JSON`, nullable=True (存储集群中心的向量或表示)。
        *   `create_time`: `DateTime`, nullable=False, default=datetime.now。
    *   **关系 (Relationships)**: 从属于 `L1Version`。

*   **表名**: `l1_chunk_topics`
    *   **用途**: 将主题和标签与特定的文档块关联，关联到 L1 版本，用于主题分析或检索。
    *   **关键列/字段**:
        *   `id`: `Integer`, PK, autoincrement。
        *   `version`: `Integer`, FK to `l1_versions.version`, nullable=False。
        *   `chunk_id`: `String(100)`, nullable=True (文档块的标识符)。
        *   `topic`: `String(500)`, nullable=True。
        *   `tags`: `JSON`, nullable=True。
        *   `create_time`: `DateTime`, nullable=False, default=datetime.now。
    *   **关系 (Relationships)**: 从属于 `L1Version`。

### 特定内容模型

*   **表名**: `status_biography` (源文件: `lpm_kernel/models/status_biography.py`)
    *   **用途**: 存储状态更新或简短的个人简介。与 `L1Bio` 不同，这似乎是更通用或当前的状态。
    *   **关键列/字段**:
        *   `id`: `Integer`, PK, autoincrement=True。
        *   `content`: `Text`, nullable=False。
        *   `content_third_view`: `Text`, nullable=False。
        *   `summary`: `Text`, nullable=False。
        *   `summary_third_view`: `Text`, nullable=False。
        *   `create_time`: `DateTime`, nullable=False, server_default=func.now()。
        *   `update_time`: `DateTime`, nullable=False, server_default=func.now(), onupdate=func.now()。

### 文档及基于文件的记忆模型

这些表是摄取、处理和管理文档及其派生数据以用于记忆和检索的核心。

*   **表名**: `document` (源文件: `lpm_kernel/file_data/models.py`, 类 `DocumentModel`)
    *   **用途**: 存储已上传或已处理文档的元数据。
    *   **关键列/字段**:
        *   `id`: `Integer`, PK, autoincrement=True。
        *   `name`: `String(255)`, nullable=False。
        *   `title`: `String(255)`, nullable=True。
        *   `mime_type`: `String(100)`, nullable=True。
        *   `user_description`: `Text`, nullable=True。
        *   `url`: `String(1024)`, nullable=True。
        *   `document_size`: `Integer`, default=0。
        *   `raw_content`: `Text`, nullable=True。
        *   `insight`: `JSON`, nullable=True。
        *   `summary`: `JSON`, nullable=True。
        *   `keywords`: `JSON`, nullable=True。
        *   `extract_status`: `SQLAlchemyEnum(ProcessStatus)`, default=ProcessStatus.INITIALIZED。
        *   `embedding_status`: `SQLAlchemyEnum(ProcessStatus)`, default=ProcessStatus.INITIALIZED。
        *   `create_time`: `DateTime`, default=datetime.now。
        *   `update_time`: `DateTime`, default=datetime.utcnow, onupdate=datetime.utcnow。
    *   **关系 (Relationships)**: 与 `ChunkModel` 存在一对多关系。

*   **表名**: `chunk` (源文件: `lpm_kernel/file_data/models.py`, 类 `ChunkModel`)
    *   **用途**: 存储从文档中提取的单个文本块，这些文本块随后用于嵌入。
    *   **关键列/字段**:
        *   `id`: `BigInteger`, PK。
        *   `document_id`: `BigInteger`, FK to `document.id`, nullable=False。
        *   `content`: `Text`, nullable=False。
        *   `has_embedding`: `Boolean`, default=False。
        *   `tags`: `JSON`, nullable=True。
        *   `topic`: `String(255)`, nullable=True。
        *   `create_time`: `DateTime`, default=datetime.utcnow。
    *   **关系 (Relationships)**: 从属于 `DocumentModel`。

*   **表名**: `memories` (源文件: `lpm_kernel/models/memory.py`)
    *   **用途**: 存储构成某种形式“记忆”的文件的元数据，可能是原始内容或数据文件。
    *   **关键列/字段**:
        *   `id`: `String(36)`, PK (预期为 UUID)。
        *   `name`: `String(255)`, nullable=False。
        *   `size`: `BigInteger`, nullable=False。
        *   `type`: `String(50)`, nullable=False (从文件扩展名派生)。
        *   `path`: `String(1024)`, nullable=False。
        *   `meta_data`: `JSON`, nullable=True。
        *   `document_id`: `String(36)`, nullable=True (关联的文档 ID)。
        *   `created_at`: `DateTime`, server_default=func.now()。
        *   `updated_at`: `DateTime`, server_default=func.now(), onupdate=func.now()。
        *   `status`: `Enum("active", "deleted")`, nullable=False, default="active"。

### 协作/空间模型 (源文件: `lpm_kernel/models/space.py`)

这些表支持多用户协作、聊天室或不同的交互“空间”。

*   **表名**: `spaces`
    *   **用途**: 定义用于讨论的独立环境或“空间”，包括参与者和目标。
    *   **关键列/字段**:
        *   `id`: `String`, PK。
        *   `space_share_id`: `String`, nullable=True。
        *   `title`: `String`, nullable=False (讨论主题)。
        *   `objective`: `String`, nullable=False (讨论目标)。
        *   `participants`: `JSON`, nullable=False (参与者端点列表)。
        *   `host`: `String`, nullable=False (主持人端点)。
        *   `create_time`: `DateTime`, nullable=False。
        *   `status`: `Integer`, default=1 (讨论状态：1-讨论中，2-讨论结束)。
        *   `conclusion`: `String`, nullable=True (讨论结论)。
    *   **关系 (Relationships)**: 与 `SpaceMessage` 存在一对多关系。

*   **表名**: `space_messages`
    *   **用途**: 存储在特定空间内交换的消息。
    *   **关键列/字段**:
        *   `id`: `String`, PK。
        *   `space_id`: `String`, FK to `spaces.id`, nullable=False。
        *   `sender_endpoint`: `String`, nullable=False (发送者端点)。
        *   `content`: `String`, nullable=False (消息内容)。
        *   `message_type`: `String`, nullable=False。
        *   `round`: `Integer`, default=0 (消息轮次)。
        *   `create_time`: `DateTime`, nullable=False。
        *   `role`: `String`, default="participant" (消息发送者角色)。
    *   **关系 (Relationships)**: 从属于 `Space`。

## 2. ChromaDB (向量存储)

ChromaDB 被用作向量存储，以实现语义搜索功能，这对于检索增强生成 (RAG) 和长期记忆功能至关重要。它存储文本数据的向量嵌入，使系统能够基于语义相似性而不是仅仅是关键字匹配来查找相关信息。

*   **用途**:
    *   存储文本片段（块）的密集向量表示（嵌入）。
    *   实现高效的相似性搜索，以检索与用户查询或给定上下文相关的块。
    *   支持 `L2/memory_manager.py` 在生成有信息量的响应时向 LLM 提供上下文信息。

*   **关键集合 (Collections)**:
    基于 `scripts/init_chroma.py` 和常见的 RAG 模式：

    *   **`documents`**:
        *   **用途**: 此集合由 `scripts/init_chroma.py` 初始化。虽然其名称可能暗示存储完整文档的嵌入，但在 RAG 系统中，更常见的是存储文档 *块* 的嵌入以进行细粒度检索。此集合可能用于存储某种形式的文档级表示或元数据，或者如果 `document_chunks` 不是主要的集合，它实际上可能存储块嵌入（这需要通过检查 `memory_manager.py` 中的用法来澄清）。
        *   **注意**: `init_chroma.py` 明确提到了初始化一个 "documents" 集合。

    *   **`document_chunks`**:
        *   **用途**: 这通常是 RAG 的主要集合。它存储从已处理文档中提取的单个、较小文本段（块）的嵌入。存储块的嵌入允许更细致和有针对性地检索相关信息。
        *   **明确初始化**: `init_chroma.py` 确认使用特定元数据创建此集合。

*   **集合内典型数据结构**:
    ChromaDB 集合中的每个条目（尤其是 `document_chunks`）通常包括：

    *   **嵌入 (Embeddings)**:
        *   由嵌入模型（例如 OpenAI 的 `text-embedding-ada-002`，或像 `nomic-embed-text` 这样的 Ollama 模型）生成的数值向量。
        *   此向量的维度由所选的嵌入模型确定。

    *   **元数据 (Metadata)**:
        *   与每个嵌入关联的键值对字典，对于筛选和提供上下文至关重要。
        *   `source_document_id`: 块源自的文档的 ID（例如，来自 `document` SQL 表的 UUID）。
        *   `chunk_id`: 此特定文本块的 ID（例如，来自 `chunk` SQL 表的 UUID）。
        *   `text_content` (可选但常见): 块的实际文本可以与其嵌入一起存储，以便快速预览，或者如果只需要文本则避免对 SQL 数据库进行单独查找。
        *   其他相关信息: 页码、章节标题、作者、创建日期、标签等，可以包含在内以增强搜索能力或提供更丰富的上下文。

    *   **ID (IDs)**:
        *   集合中的每个条目都有一个唯一的 ID，通常对应于 `chunk_id`。

*   **集合元数据 (由 `init_chroma.py` 设置)**:
    *   `hnsw:space`: "cosine" - 指定将使用余弦相似度来衡量向量之间的距离（ وبالتالي 相似性）。
    *   `dimension`: 存储在集合中的嵌入的维度（例如，`text-embedding-ada-002` 为 1536）。这是由 `scripts/init_chroma.py` 根据配置的嵌入模型动态检测和设置的。

*   **交互**:
    *   **`lpm_kernel/file_data/embedding_service.py`**: 负责使用配置的嵌入模型从文本块生成嵌入。
    *   **`lpm_kernel/L2/memory_manager.py`**: 处理将这些嵌入（及其元数据）存储到 ChromaDB 集合中，并根据查询嵌入对这些集合执行查询以查找语义相似的块。
    *   检索到的块随后由 L2（以及后续的 L1/L0）层用于在生成响应时向 LLM 提供上下文，构成 RAG 模式的核心。

本概览应有助于对应用程序中数据的结构和管理方式有一个基本的了解。有关精确的模式详细信息，建议直接查阅 SQLAlchemy 模型类。
