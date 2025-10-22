# 项目结构总结 / Project Structure Summary

## 📁 最终目录结构 / Final Directory Structure

```
duckduckgo-mcp-server-py/
├── 📄 README.md                      # 中英双语项目说明 / Bilingual project description
├── 📄 README_EN.md                   # 英文项目说明 / English project description
├── 📄 CLAUDE.md                      # 项目完整记录 / Complete project record
├── 📄 PROJECT_STRUCTURE.md           # 本文件 / This file
├── 📄 pyproject.toml                 # Python包配置 / Python package configuration
├── 📄 docker-compose.yml             # Docker编排配置 / Docker orchestration
├── 📄 Dockerfile                     # Docker镜像构建 / Docker image build
├── 📄 .env.example                   # 环境变量示例 / Environment variables example
│
├── 📂 src/                           # 核心源码 / Core source code
│   └── 📂 duckduckgo_mcp_server/
│       ├── 📄 __init__.py
│       ├── 📄 server.py              # 主服务器逻辑 / Main server logic
│       ├── 📄 transports.py          # 传输层实现 / Transport layer implementations
│       ├── 📄 search_client.py       # 搜索客户端 / Search client
│       ├── 📄 models.py              # 数据模型 / Data models
│       ├── 📄 rate_limiter.py        # 速率限制器 / Rate limiter
│       └── 📄 config.py              # 配置管理 / Configuration management
│
├── 📂 tests/                         # 测试文件 / Test files
│   ├── 📂 unit/                      # 单元测试 / Unit tests
│   ├── 📂 integration/               # 集成测试 / Integration tests
│   │   ├── 📄 test_integration.py
│   │   ├── 📄 final_test.py
│   │   ├── 📄 debug_test.py
│   │   └── 📄 test_server.py
│   └── 📂 docker/                    # Docker测试 / Docker tests
│       ├── 📄 test_docker_integration.py
│       └── 📄 simple_docker_test.py
│
├── 📂 examples/                      # 使用示例 / Usage examples
│   ├── 📄 http_client.py             # HTTP客户端示例 / HTTP client example
│   ├── 📄 sse_client.py              # SSE客户端示例 / SSE client example
│   └── 📄 docker_usage.md            # Docker使用指南 / Docker usage guide
│
├── 📂 scripts/                       # 脚本文件 / Script files
│   ├── 📄 quick_start.sh             # 快速启动脚本 / Quick start script
│   └── 📂 docker/                    # Docker相关脚本 / Docker-related scripts
│       └── 📄 docker-entrypoint.sh   # Docker入口脚本 / Docker entrypoint script
│
├── 📂 config/                        # 配置文件 / Configuration files
│   ├── 📂 nginx/                     # Nginx配置 / Nginx configuration
│   │   └── 📄 nginx.conf              # Nginx主配置 / Nginx main configuration
│   └── 📂 docker/                    # Docker配置 / Docker configuration
│
├── 📂 docs/                          # 文档目录 / Documentation directory
│   ├── 📂 zh/                        # 中文文档 / Chinese documentation
│   │   ├── 📂 api/                   # API文档 / API documentation
│   │   │   └── 📄 README.md
│   │   ├── 📂 deployment/            # 部署文档 / Deployment documentation
│   │   │   └── 📄 README.md
│   │   └── 📂 development/           # 开发文档 / Development documentation
│   │       └── 📄 README.md
│   └── 📂 en/                        # 英文文档 / English documentation
│       ├── 📂 api/                   # API documentation
│       │   └── 📄 README.md
│       ├── 📂 deployment/            # Deployment documentation
│       │   └── 📄 README.md
│       └── 📂 development/           # Development documentation
│           └── 📄 README.md
│
├── 📂 DOCKER_USAGE.md               # Docker使用文档 / Docker usage documentation
├── 📂 src/duckduckgo_mcp_server.egg-info/  # Python包信息 / Python package info
```

## 🏗️ 架构层次 / Architecture Layers

### 1. 核心层 / Core Layer
- **服务器核心 / Server Core**: `server.py` - MCP协议处理和服务器生命周期管理
- **传输层 / Transport Layer**: `transports.py` - 多种传输协议实现(STDIO/HTTP/SSE/Hybrid)
- **搜索引擎 / Search Engine**: `search_client.py` - DuckDuckGo搜索功能和duck-duck-scrape-py集成
- **数据模型 / Data Models**: `models.py` - Pydantic数据验证和序列化
- **速率限制 / Rate Limiting**: `rate_limiter.py` - 智能请求频率控制
- **配置管理 / Configuration**: `config.py` - 集中配置管理

### 2. 测试层 / Testing Layer
- **单元测试 / Unit Tests**: 测试单个组件功能
- **集成测试 / Integration Tests**: 测试组件间协作
- **Docker测试 / Docker Tests**: 测试容器化部署

### 3. 部署层 / Deployment Layer
- **Docker容器化 / Docker Containerization**: 完整的容器化解决方案
- **多环境配置 / Multi-environment Config**: 开发、测试、生产环境配置
- **反向代理 / Reverse Proxy**: Nginx负载均衡和SSL终端

### 4. 文档层 / Documentation Layer
- **中英双语 / Bilingual**: 完整的中英双语文档体系
- **分类文档 / Categorized Docs**: API、部署、开发专题文档
- **示例代码 / Example Code**: 实用的客户端集成示例

## 🔄 数据流 / Data Flow

```
客户端请求 / Client Request
    ↓
MCP协议解析 / MCP Protocol Parsing
    ↓
传输层路由 / Transport Layer Routing
    ↓
工具调用处理 / Tool Call Processing
    ↓
搜索引擎集成 / Search Engine Integration
    ↓
结果格式化 / Result Formatting
    ↓
响应返回 / Response Return
```

## 🚀 部署模式 / Deployment Modes

| 模式 / Mode | 用途 / Use Case | 配置文件 / Config |
|-----------|----------------|------------------|
| **STDIO** | Claude Desktop集成 / Claude Desktop integration | `--transport stdio` |
| **HTTP** | REST API服务 / REST API service | `--transport http` |
| **SSE** | 实时事件流 / Real-time events | `--transport sse` |
| **Hybrid** | 生产多协议 / Production multi-protocol | `--transport hybrid` |
| **Docker** | 容器化部署 / Containerized deployment | `docker-compose.yml` |

## 📊 技术栈 / Technology Stack

### 后端技术 / Backend Technologies
- **Python 3.8+**: 主要开发语言 / Main development language
- **FastAPI**: HTTP API框架 / HTTP API framework
- **MCP SDK**: 模型上下文协议SDK / Model Context Protocol SDK
- **Pydantic**: 数据验证 / Data validation
- **asyncio**: 异步编程 / Asynchronous programming

### 搜索集成 / Search Integration
- **DuckDuckGo**: 主搜索引擎 / Main search engine
- **duck-duck-scrape-py**: 专业搜索库 / Professional search library
- **httpx**: HTTP客户端 / HTTP client

### 部署技术 / Deployment Technologies
- **Docker**: 容器化 / Containerization
- **Docker Compose**: 服务编排 / Service orchestration
- **Nginx**: 反向代理 / Reverse proxy
- **Redis**: 缓存和速率限制 / Caching and rate limiting

### 开发工具 / Development Tools
- **pytest**: 测试框架 / Testing framework
- **Black**: 代码格式化 / Code formatting
- **MyPy**: 类型检查 / Type checking
- **pre-commit**: Git钩子 / Git hooks

## 🔧 配置管理 / Configuration Management

### 环境变量 / Environment Variables
```bash
MCP_SERVER_TRANSPORT=hybrid        # 传输模式 / Transport mode
MCP_SERVER_HOST=0.0.0.0           # 服务器主机 / Server host
MCP_SERVER_PORT=8080              # HTTP端口 / HTTP port
MCP_SSE_PORT=8081                 # SSE端口 / SSE port
MCP_LOG_LEVEL=INFO                # 日志级别 / Log level
```

### Docker配置 / Docker Configuration
- **开发环境 / Development**: `docker-compose --profile http up`
- **生产环境 / Production**: `docker-compose --profile production up -d`
- **增强环境 / Enhanced**: `docker-compose --profile enhanced up -d`

## 📈 性能特点 / Performance Characteristics

### 优势 / Advantages
- **异步架构 / Async Architecture**: 高并发处理能力 / High concurrency capability
- **多传输支持 / Multi-transport Support**: 灵活的部署选项 / Flexible deployment options
- **智能回退 / Smart Fallback**: 高可用性保证 / High availability guarantee
- **速率限制 / Rate Limiting**: 防止API滥用 / Prevent API abuse
- **容器就绪 / Container Ready**: 现代化部署方式 / Modern deployment approach

### 扩展性 / Extensibility
- **模块化设计 / Modular Design**: 易于扩展和维护 / Easy to extend and maintain
- **插件架构 / Plugin Architecture**: 支持新传输协议和搜索引擎 / Support new transports and search engines
- **配置驱动 / Configuration Driven**: 灵活的运行时配置 / Flexible runtime configuration

---

**文档版本 / Documentation Version**: v0.1.2
**创建时间 / Created**: 2025-10-22
**维护者 / Maintainer**: Claude Code Assistant