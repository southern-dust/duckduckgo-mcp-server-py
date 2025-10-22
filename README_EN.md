# DuckDuckGo MCP Server Python Implementation

[English](README_EN.md) | [中文](README.md)

## Project Overview

This is a comprehensive Python implementation of a DuckDuckGo Search MCP (Model Context Protocol) server with multi-transport support and production-ready deployment configurations.

## ✨ Key Features

- 🔍 **DuckDuckGo Search Integration**: Web search functionality without API keys
- 🚀 **Multi-Transport Support**: STDIO, HTTP, SSE, and Hybrid modes
- 🐳 **Docker Ready**: Complete containerized deployment solution
- 🛡️ **Rate Limiting**: Built-in intelligent rate control
- 🔄 **High Availability**: Graceful degradation and error recovery
- 📊 **Monitoring Ready**: Health checks and status monitoring endpoints

## 🏗️ Project Architecture

```
Project Structure:
├── src/duckduckgo_mcp_server/          # Core Package
│   ├── server.py                       # Main Server
│   ├── transports.py                   # Transport Implementations
│   ├── search_client.py                # Search Client
│   ├── models.py                       # Data Models
│   ├── rate_limiter.py                 # Rate Limiter
│   └── config.py                       # Configuration
├── tests/                              # Tests
│   ├── unit/                           # Unit Tests
│   ├── integration/                    # Integration Tests
│   └── docker/                         # Docker Tests
├── examples/                           # Examples
├── scripts/                            # Scripts
├── config/                             # Configurations
├── docs/                               # Documentation
│   ├── zh/                             # Chinese Docs
│   └── en/                             # English Docs
├── docker-compose.yml                  # Docker Compose Configuration
├── Dockerfile                          # Docker Image Build
└── pyproject.toml                      # Python Package Configuration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker (optional)
- pip or poetry

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd duckduckgo-mcp-server-py

# Install dependencies
pip install -e .

# If duck-duck-scrape-py integration is needed
pip install -e /path/to/duck-duck-scrape-py
```

### Running the Server

```bash
# STDIO transport (default, for Claude Desktop)
python -m duckduckgo_mcp_server.server

# HTTP API service
python -m duckduckgo_mcp_server.server --transport http

# SSE event stream service
python -m duckduckgo_mcp_server.server --transport sse

# Hybrid mode (HTTP + SSE)
python -m duckduckgo_mcp_server.server --transport hybrid
```

## 📚 Documentation

- [API Documentation](docs/en/api/README.md)
- [Deployment Guide](docs/en/deployment/README.md)
- [Development Guide](docs/en/development/README.md)

## 🐳 Docker Deployment

```bash
# Development
docker-compose --profile http up

# Production
docker-compose --profile production up -d

# Full features (with Redis)
docker-compose --profile enhanced up
```

## 🔧 Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MCP_SERVER_HOST` | `0.0.0.0` | HTTP server host |
| `MCP_SERVER_PORT` | `8080` | HTTP server port |
| `MCP_SSE_PORT` | `8081` | SSE server port |
| `MCP_LOG_LEVEL` | `INFO` | Log level |
| `MCP_RATE_LIMIT_PER_SEC` | `1` | Requests per second limit |
| `MCP_RATE_LIMIT_PER_MONTH` | `15000` | Requests per month limit |

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Integration tests
python tests/integration/test_integration.py

# Docker tests
python tests/docker/test_docker_integration.py
```

## 📊 Transport Modes Comparison

| Mode | Port | Use Case | Endpoints |
|------|------|----------|-----------|
| STDIO | - | Claude Desktop integration | - |
| HTTP | 8080 | REST API | `/mcp`, `/health` |
| SSE | 8081 | Real-time events | `/sse`, `/sse/request` |
| Hybrid | 8080/8081 | Production multi-protocol | All endpoints |

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🔗 Related Links

- [Original TypeScript version](https://github.com/felix-dingduckduckgo-mcp-server)
- [duck-duck-scrape-py library](https://github.com/felix-ding/duck-duck-scrape-py)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)

## 📞 Support

For questions or suggestions, please submit an Issue or contact the maintainer.

---

**Project Status**: ✅ Production Ready
**Last Updated**: 2025-10-22
**Maintainer**: Claude Code Assistant