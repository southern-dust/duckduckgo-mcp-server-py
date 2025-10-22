# DuckDuckGo MCP Server Python Implementation

[English](README_EN.md) | [中文](README.md)

## 项目概述 / Project Overview

这是一个功能完整的 DuckDuckGo 搜索 MCP (Model Context Protocol) 服务器的 Python 实现，支持多种传输方式和生产级部署配置。

This is a comprehensive Python implementation of a DuckDuckGo Search MCP (Model Context Protocol) server with multi-transport support and production-ready deployment configurations.

## ✨ 主要特性 / Key Features

- 🔍 **DuckDuckGo 搜索集成** / **DuckDuckGo Search Integration**: 无需 API 密钥的 Web 搜索功能 / Web search functionality without API keys
- 🚀 **多传输协议支持** / **Multi-Transport Support**: STDIO, HTTP, SSE, and Hybrid modes
- 🐳 **Docker 部署就绪** / **Docker Ready**: 完整的容器化部署方案 / Complete containerized deployment solution
- 🛡️ **速率限制** / **Rate Limiting**: 内置的智能速率控制 / Built-in intelligent rate control
- 🔄 **高可用性** / **High Availability**: 优雅降级和错误恢复机制 / Graceful degradation and error recovery
- 📊 **监控就绪** / **Monitoring Ready**: 健康检查和状态监控端点 / Health checks and status monitoring endpoints

## Transport Modes

### 1. STDIO Transport
- **Use Case**: Direct integration with MCP clients (like Claude Desktop)
- **Command Line**: `duckduckgo-mcp-server --transport stdio`
- **Docker Profile**: `stdio`

### 2. HTTP Transport
- **Use Case**: REST API integration, web applications
- **Endpoint**: `POST /mcp`
- **Port**: 8080
- **Docker Profile**: `http`

### 3. SSE Transport
- **Use Case**: Real-time web applications, event-driven architectures
- **Endpoints**: `GET /sse`, `POST /sse/request`
- **Port**: 8081
- **Docker Profile**: `sse`

### 4. Hybrid Mode
- **Use Case**: Production deployments needing multiple transport options
- **Ports**: 8080 (HTTP), 8081 (SSE)
- **Docker Profile**: `hybrid`, `production`

## Quick Start

### Using Docker Compose

1. **STDIO Transport (for local development):**
   ```bash
   docker-compose --profile stdio up
   ```

2. **HTTP Transport:**
   ```bash
   docker-compose --profile http up
   ```

3. **SSE Transport:**
   ```bash
   docker-compose --profile sse up
   ```

4. **Hybrid Mode (recommended for production):**
   ```bash
   docker-compose --profile production up
   ```

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Run with different transports:**
   ```bash
   # STDIO (default)
   python -m duckduckgo_mcp_server.server

   # HTTP
   python -m duckduckgo_mcp_server.server --transport http

   # SSE
   python -m duckduckgo_mcp_server.server --transport sse

   # Hybrid (all transports)
   python -m duckduckgo_mcp_server.server --transport hybrid
   ```

## API Usage

### Tool Schema

The server provides one tool: `duckduckgo_web_search`

**Parameters:**
- `query` (required, string): Search query (max 400 characters)
- `count` (optional, integer): Number of results (1-20, default 10)
- `safeSearch` (optional, string): Safe search level ("strict", "moderate", "off")

### Example Requests

#### HTTP Transport
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "duckduckgo_web_search",
      "arguments": {
        "query": "Python async programming",
        "count": 5,
        "safeSearch": "moderate"
      }
    }
  }'
```

#### SSE Transport
```bash
# Start SSE connection
curl -N http://localhost:8081/sse

# Make search request
curl -X POST http://localhost:8081/sse/request \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "duckduckgo_web_search",
      "arguments": {
        "query": "Docker containers"
      }
    }
  }'
```

## Claude Desktop Configuration

### STDIO Transport (Local)
```json
{
  "mcpServers": {
    "duckduckgo-search": {
      "command": "python",
      "args": [
        "-m", "duckduckgo_mcp_server.server",
        "--transport", "stdio"
      ]
    }
  }
}
```

### HTTP Transport (Remote)
```json
{
  "mcpServers": {
    "duckduckgo-search": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "http://localhost:8080/mcp",
        "-H", "Content-Type: application/json",
        "-d", "@-"
      ]
    }
  }
}
```

## Docker Deployment

### Building the Image
```bash
docker build -t duckduckgo-mcp-server:latest .
```

### Running with Different Profiles

1. **Development (STDIO only):**
   ```bash
   docker-compose --profile stdio up duckduckgo-stdio
   ```

2. **HTTP API:**
   ```bash
   docker-compose --profile http up duckduckgo-http
   ```

3. **Real-time (SSE):**
   ```bash
   docker-compose --profile sse up duckduckgo-sse
   ```

4. **Production (Hybrid + Nginx):**
   ```bash
   docker-compose --profile production up
   ```

5. **Enhanced (with Redis):**
   ```bash
   docker-compose --profile enhanced up
   ```

## Health Monitoring

All HTTP/SSE endpoints include health checks:

```bash
# HTTP health check
curl http://localhost:8080/health

# SSE health check
curl http://localhost:8081/health

# Nginx health check (production mode)
curl http://localhost/health
```

## Rate Limiting

The server implements rate limiting to prevent abuse:
- **Per Second**: 1 request
- **Per Month**: 15,000 requests
- **Headers**: Rate limit information included in responses

## Environment Variables

- `PYTHONPATH`: Python module path (default: `/app/src`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `HTTP_HOST`: HTTP server host (default: `0.0.0.0`)
- `HTTP_PORT`: HTTP server port (default: `8080`)
- `SSE_HOST`: SSE server host (default: `0.0.0.0`)
- `SSE_PORT`: SSE server port (default: `8081`)

## Development

### Project Structure
```
src/duckduckgo_mcp_server/
├── __init__.py          # Package initialization
├── server.py            # Main server implementation
├── transports.py        # Transport layer implementations
├── search_client.py     # DuckDuckGo search client
├── rate_limiter.py      # Rate limiting functionality
├── models.py            # Data models
└── config.py            # Configuration settings
```

### Running Tests
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=duckduckgo_mcp_server
```

### Code Quality
```bash
# Format code
black src/
isort src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## Production Deployment

### Using Nginx Reverse Proxy
The provided Nginx configuration handles:
- Load balancing
- SSL termination
- HTTP/2 support
- Proper SSE proxying
- Health checks

### SSL Setup
1. Place SSL certificates in `./ssl/` directory:
   - `cert.pem`: SSL certificate
   - `key.pem`: Private key

2. Update Nginx configuration with your domain

### Monitoring
- **Health endpoints**: `/health` on all services
- **Logs**: Structured logging with configurable levels
- **Metrics**: Rate limiting status available via API

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/zhsama/duckduckgo-mcp-server/issues)
- Documentation: [Wiki](https://github.com/zhsama/duckduckgo-mcp-server/wiki)