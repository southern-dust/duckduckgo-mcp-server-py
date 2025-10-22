# API 文档 / API Documentation

[中文](api_zh.md) | [English](api_en.md)

## 概述 / Overview

DuckDuckGo MCP Server 提供了完整的 RESTful API 和 Server-Sent Events (SSE) 接口，支持多种传输协议和实时通信。

The DuckDuckGo MCP Server provides comprehensive RESTful API and Server-Sent Events (SSE) interfaces with support for multiple transport protocols and real-time communication.

## 🔍 搜索工具 / Search Tool

### 工具名称 / Tool Name
`duckduckgo_web_search`

### 描述 / Description
执行 DuckDuckGo Web 搜索并返回格式化结果。

Performs DuckDuckGo Web search and returns formatted results.

### 参数 / Parameters

| 参数名 / Parameter | 类型 / Type | 必需 / Required | 描述 / Description | 限制 / Constraints |
|-------------------|------------|----------------|-------------------|-------------------|
| `query` | string | ✅ 是 / Yes | 搜索查询字符串 / Search query string | 最大 400 字符 / Max 400 characters |
| `count` | integer | ❌ 否 / No | 返回结果数量 / Number of results to return | 1-20，默认 10 / Default 10 |
| `safeSearch` | string | ❌ 否 / No | 安全搜索级别 / Safe search level | "strict", "moderate", "off"，默认 "moderate" |

### 返回格式 / Return Format

```json
{
  "content": [
    {
      "type": "text",
      "text": "## 搜索结果：Python 编程\n\n### 1. [Python 官方网站](https://python.org)\nPython 是一种高级编程语言...\n\n### 2. [Python 教程](https://tutorial.example.com)\n详细的 Python 学习教程...\n\n..."
    }
  ]
}
```

## 🚀 传输协议 / Transport Protocols

### 1. STDIO 传输 / STDIO Transport

**用途 / Use Case**: 直接与 MCP 客户端集成（如 Claude Desktop） / Direct integration with MCP clients (like Claude Desktop)

**启动命令 / Start Command**:
```bash
python -m duckduckgo_mcp_server.server --transport stdio
```

**协议格式 / Protocol Format**: 标准 MCP JSON-RPC over STDIO / Standard MCP JSON-RPC over STDIO

### 2. HTTP 传输 / HTTP Transport

**用途 / Use Case**: REST API 集成，Web 应用程序 / REST API integration, web applications

**启动命令 / Start Command**:
```bash
python -m duckduckgo_mcp_server.server --transport http
```

**端点 / Endpoints**:
- `POST /mcp` - 主要 MCP 端点 / Main MCP endpoint
- `GET /health` - 健康检查 / Health check

**请求示例 / Request Example**:
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

**响应示例 / Response Example**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "## 搜索结果：Python async programming\n\n### 1. [Python asyncio 官方文档](https://docs.python.org/3/library/asyncio.html)\nPython asyncio 库的官方文档..."
      }
    ],
    "isError": false
  }
}
```

### 3. SSE 传输 / SSE Transport

**用途 / Use Case**: 实时 Web 应用程序，事件驱动架构 / Real-time web applications, event-driven architectures

**启动命令 / Start Command**:
```bash
python -m duckduckgo_mcp_server.server --transport sse
```

**端点 / Endpoints**:
- `GET /sse` - SSE 连接端点 / SSE connection endpoint
- `POST /sse/request` - 搜索请求端点 / Search request endpoint
- `GET /health` - 健康检查 / Health check

**SSE 连接示例 / SSE Connection Example**:
```bash
# 建立 SSE 连接
curl -N http://localhost:8081/sse
```

**搜索请求示例 / Search Request Example**:
```bash
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

### 4. 混合传输 / Hybrid Transport

**用途 / Use Case**: 需要多种传输选项的生产部署 / Production deployments needing multiple transport options

**启动命令 / Start Command**:
```bash
python -m duckduckgo_mcp_server.server --transport hybrid
```

**端口 / Ports**: HTTP (8080), SSE (8081)
**端点 / Endpoints**: 所有 HTTP 和 SSE 端点 / All HTTP and SSE endpoints

## 🛡️ 速率限制 / Rate Limiting

### 限制规则 / Rate Limit Rules

- **每秒限制 / Per Second**: 1 次请求 / 1 request
- **每月限制 / Per Month**: 15,000 次请求 / 15,000 requests
- **超限处理 / Rate Limit Exceeded**: 返回 429 状态码和重试时间 / Returns 429 status and retry time

### 响应头 / Response Headers

```http
X-RateLimit-Limit: 1;w=1
X-RateLimit-Limit-Month: 15000;w=2592000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1634567890
X-RateLimit-Month-Remaining: 14999
```

### 错误响应 / Error Response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Rate limit exceeded. Please try again later.",
    "data": {
      "retryAfter": 60
    }
  }
}
```

## 🔧 错误处理 / Error Handling

### 常见错误码 / Common Error Codes

| 错误码 / Code | 描述 / Description | 解决方案 / Solution |
|-------------|-------------------|-------------------|
| -32602 | 无效参数 / Invalid params | 检查参数格式和值 / Check parameter format and values |
| -32000 | 服务器错误 / Server error | 查看服务器日志 / Check server logs |
| -32001 | 速率限制 / Rate limited | 等待后重试 / Wait and retry |
| -32601 | 方法不存在 / Method not found | 检查方法名称 / Check method name |

### 参数验证错误 / Parameter Validation Errors

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params: query must be a string",
    "data": {
      "field": "query",
      "expected": "string",
      "received": "number"
    }
  }
}
```

## 📊 监控和健康检查 / Monitoring and Health Checks

### 健康检查端点 / Health Check Endpoints

```bash
# HTTP 健康检查
curl http://localhost:8080/health

# SSE 健康检查
curl http://localhost:8081/health
```

**健康检查响应 / Health Check Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-22T10:30:00Z",
  "version": "0.1.2",
  "transport": "http",
  "rateLimit": {
    "remaining": 1,
    "resetTime": 1634567890,
    "monthlyRemaining": 14999
  },
  "search": {
    "status": "ready",
    "lastSearch": null
  }
}
```

## 🌐 客户端集成示例 / Client Integration Examples

### Python 客户端 / Python Client

```python
import asyncio
import aiohttp

async def search_duckduckgo(query: str):
    """使用 HTTP API 搜索 DuckDuckGo"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "duckduckgo_web_search",
                "arguments": {
                    "query": query,
                    "count": 5
                }
            }
        }

        async with session.post(
            "http://localhost:8080/mcp",
            json=payload
        ) as response:
            result = await response.json()
            return result["result"]["content"][0]["text"]

# 使用示例 / Usage example
result = asyncio.run(search_duckduckgo("Python 编程"))
print(result)
```

### JavaScript 客户端 / JavaScript Client

```javascript
// 使用 Fetch API
async function searchDuckDuckGo(query) {
    const response = await fetch('http://localhost:8080/mcp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            id: 1,
            method: 'tools/call',
            params: {
                name: 'duckduckgo_web_search',
                arguments: {
                    query: query,
                    count: 5
                }
            }
        })
    });

    const result = await response.json();
    return result.result.content[0].text;
}

// 使用示例 / Usage example
searchDuckDuckGo('JavaScript async').then(console.log);
```

## 🔒 安全考虑 / Security Considerations

- **输入验证 / Input Validation**: 所有输入参数都经过严格验证 / All input parameters are strictly validated
- **速率限制 / Rate Limiting**: 防止 API 滥用 / Prevents API abuse
- **错误信息 / Error Messages**: 不暴露敏感的系统信息 / Does not expose sensitive system information
- **日志记录 / Logging**: 详细的安全事件日志 / Detailed security event logging

## 📝 更新日志 / Changelog

### v0.1.2 (2025-10-22)
- ✅ 集成 duck-duck-scrape-py 库 / Integrated duck-duck-scrape-py library
- ✅ 添加 URL 重定向清理功能 / Added URL redirect cleanup functionality
- ✅ 改进错误处理机制 / Improved error handling mechanisms

### v0.1.1 (2025-10-20)
- ✅ 添加多传输协议支持 / Added multi-transport protocol support
- ✅ 完善速率限制功能 / Enhanced rate limiting functionality
- ✅ 添加健康检查端点 / Added health check endpoints

### v0.1.0 (2025-10-15)
- ✅ 初始版本发布 / Initial release
- ✅ 基础搜索功能 / Basic search functionality
- ✅ MCP 协议支持 / MCP protocol support

---

**文档版本 / Documentation Version**: v0.1.2
**最后更新 / Last Updated**: 2025-10-22
**维护者 / Maintainer**: Claude Code Assistant