# 使用 Ollama 自定义模型端点指南

## 1. 先决条件：Ollama 设置

首先，请从官方网站下载并安装 Ollama：

🔗 **下载链接**: [https://ollama.com/download](https://ollama.com/download)

📚 **其他资源**:
- 官方网站: [https://ollama.com](https://ollama.com/)
- 模型库: [https://ollama.com/library](https://ollama.com/library)
- GitHub 仓库: [https://github.com/ollama/ollama/](https://github.com/ollama/ollama)

---

## 2. 基本 Ollama 命令

| 命令 (Command) | 描述 (Description) |
|------|------|
| `ollama pull model_name` | 下载一个模型 |
| `ollama serve` | 启动 Ollama 服务 |
| `ollama ps` | 列出正在运行的模型 |
| `ollama list` | 列出所有已下载的模型 |
| `ollama rm model_name` | 移除一个模型 |
| `ollama show model_name` | 显示模型详情 |

## 3. 使用 Ollama API 实现自定义模型

### OpenAI 兼容的 API (OpenAI-Compatible API)


#### 聊天请求 (Chat Request)

```bash
curl http://127.0.0.1:11434/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "qwen2.5:0.5b",
  "messages": [
    {"role": "user", "content": "Why is the sky blue?"}
  ]
}'
```

#### 嵌入请求 (Embedding Request)

```bash
curl http://127.0.0.1:11434/v1/embeddings -d '{
  "model": "snowflake-arctic-embed:110m",
  "input": "Why is the sky blue?"
}'
```

更多详情: [https://github.com/ollama/ollama/blob/main/docs/openai.md](https://github.com/ollama/ollama/blob/main/docs/openai.md)

## 4. 在 Second Me 中配置自定义嵌入 (Embedding)

1. 启动 Ollama 服务: `ollama serve`
2. 检查您的 Ollama 嵌入模型的上下文长度 (context length):

```bash
# 示例: ollama show snowflake-arctic-embed:110m
$ ollama show snowflake-arctic-embed:110m

Model
  architecture        bert       
  parameters          108.89M    
  context length      512        
  embedding length    768        
  quantization        F16        

License
  Apache License               
  Version 2.0, January 2004
```

3. 修改 `Second_Me/.env` 文件中的 `EMBEDDING_MAX_TEXT_LENGTH`，使其与您的嵌入模型的上下文窗口大小相匹配。这样可以防止文本块长度溢出，并避免服务器端错误 (500 Internal Server Error)。

```bash
# Embedding configurations

EMBEDDING_MAX_TEXT_LENGTH=embedding_model_context_length
```

4. 在设置中配置自定义嵌入 (Embedding)

```
聊天 (Chat):
模型名称 (Model Name): qwen2.5:0.5b
API 密钥 (API Key): ollama
API 端点 (API Endpoint): http://127.0.0.1:11434/v1

嵌入 (Embedding):
模型名称 (Model Name): snowflake-arctic-embed:110m
API 密钥 (API Key): ollama
API 端点 (API Endpoint): http://127.0.0.1:11434/v1
```

**当在 Docker 环境中运行 Second Me 时**，请将 API 端点中的 `127.0.0.1` 替换为 `host.docker.internal`：

```
聊天 (Chat):
模型名称 (Model Name): qwen2.5:0.5b
API 密钥 (API Key): ollama
API 端点 (API Endpoint): http://host.docker.internal:11434/v1

嵌入 (Embedding):
模型名称 (Model Name): snowflake-arctic-embed:110m
API 密钥 (API Key): ollama
API 端点 (API Endpoint): http://host.docker.internal:11434/v1
```
