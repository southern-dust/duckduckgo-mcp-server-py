# API Documentation

[中文](api_zh.md) | [English](api_en.md)

## Overview

The DuckDuckGo MCP Server provides a unified search API supporting multiple transport protocols. All APIs follow the MCP (Model Context Protocol) specification.

## 🔍 Search Tool

### Tool Name
`duckduckgo_web_search`

### Description
Performs DuckDuckGo Web search and returns formatted results.

### Parameters

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| `query` | string | ✅ Yes | Search query string | Max 400 characters |
| `count` | integer | ❌ No | Number of results to return | 1-20, default 10 |
| `safeSearch` | string | ❌ No | Safe search level | "strict", "moderate", "off", default "moderate" |

### Return Format

```json
{
  "content": [
    {
      "type": "text",
      "text": "## Search Results: Python Programming\n\n### 1. [Python Official Website](https://python.org)\nPython is a high-level programming language...\n\n### 2. [Python Tutorial](https://tutorial.example.com)\nDetailed Python learning tutorial...\n\n..."
    }
  ]
}
```

## 🚀 Transport Protocols

### 1. STDIO Transport

**Use Case**: Direct integration with MCP clients (like Claude Desktop)

**Start Command**:
```bash
python -m duckduckgo_mcp_server.server --transport stdio
```

**Protocol Format**: Standard MCP JSON-RPC over STDIO

### 2. HTTP Transport

**Use Case**: REST API integration, web applications

**Start Command**:
```bash
python -m duckduckgo_mcp_server.server --transport http
```

**Endpoints**:
- `POST /mcp` - Main MCP endpoint
- `GET /health` - Health check

**Request Example**:
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

**Response Example**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "## Search Results: Python async programming\n\n### 1. [Python asyncio Official Documentation](https://docs.python.org/3/library/asyncio.html)\nOfficial documentation for Python asyncio library..."
      }
    ],
    "isError": false
  }
}
```

### 3. SSE Transport

**Use Case**: Real-time web applications, event-driven architectures

**Start Command**:
```bash
python -m duckduckgo_mcp_server.server --transport sse
```

**Endpoints**:
- `GET /sse` - SSE connection endpoint
- `POST /sse/request` - Search request endpoint
- `GET /health` - Health check

**SSE Connection Example**:
```bash
# Establish SSE connection
curl -N http://localhost:8081/sse
```

**Search Request Example**:
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

### 4. Hybrid Transport

**Use Case**: Production deployments needing multiple transport options

**Start Command**:
```bash
python -m duckduckgo_mcp_server.server --transport hybrid
```

**Ports**: HTTP (8080), SSE (8081)
**Endpoints**: All HTTP and SSE endpoints

## 🛡️ Rate Limiting

### Rate Limit Rules

- **Per Second**: 1 request
- **Per Month**: 15,000 requests
- **Rate Limit Exceeded**: Returns 429 status and retry time

### Response Headers

```http
X-RateLimit-Limit: 1;w=1
X-RateLimit-Limit-Month: 15000;w=2592000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1634567890
X-RateLimit-Month-Remaining: 14999
```

### Error Response

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

## 🔧 Error Handling

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| -32602 | Invalid params | Check parameter format and values |
| -32000 | Server error | Check server logs |
| -32001 | Rate limited | Wait and retry |
| -32601 | Method not found | Check method name |

### Parameter Validation Errors

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

## 📊 Monitoring and Health Checks

### Health Check Endpoints

```bash
# HTTP health check
curl http://localhost:8080/health

# SSE health check
curl http://localhost:8081/health
```

**Health Check Response**:
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

## 🌐 Client Integration Examples

### Python Client

```python
import asyncio
import aiohttp

async def search_duckduckgo(query: str):
    """Search DuckDuckGo using HTTP API"""
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

# Usage example
result = asyncio.run(search_duckduckgo("Python programming"))
print(result)
```

### JavaScript Client

```javascript
// Using Fetch API
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

// Usage example
searchDuckDuckGo('JavaScript async').then(console.log);
```

## 🔒 Security Considerations

- **Input Validation**: All input parameters are strictly validated
- **Rate Limiting**: Prevents API abuse
- **Error Messages**: Does not expose sensitive system information
- **Logging**: Detailed security event logging

## 📝 Changelog

### v0.1.2 (2025-10-22)
- ✅ Integrated duck-duck-scrape-py library
- ✅ Added URL redirect cleanup functionality
- ✅ Improved error handling mechanisms

### v0.1.1 (2025-10-20)
- ✅ Added multi-transport protocol support
- ✅ Enhanced rate limiting functionality
- ✅ Added health check endpoints

### v0.1.0 (2025-10-15)
- ✅ Initial release
- ✅ Basic search functionality
- ✅ MCP protocol support

---

**Documentation Version**: v0.1.2
**Last Updated**: 2025-10-22
**Maintainer**: Claude Code Assistant