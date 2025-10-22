# 开发文档 / Development Guide

[中文](development_zh.md) | [English](development_en.md)

## 概述 / Overview

本文档为开发者提供了 DuckDuckGo MCP Server 的详细开发指南，包括项目架构、代码规范、测试方法和贡献流程。

This document provides a detailed development guide for DuckDuckGo MCP Server, including project architecture, coding standards, testing methods, and contribution processes.

## 🏗️ 项目架构 / Project Architecture

### 目录结构 / Directory Structure

```
duckduckgo-mcp-server-py/
├── src/duckduckgo_mcp_server/          # 核心包 / Core Package
│   ├── __init__.py                     # 包初始化 / Package initialization
│   ├── server.py                       # 主服务器实现 / Main server implementation
│   ├── transports.py                   # 传输层实现 / Transport layer implementations
│   ├── search_client.py                # 搜索客户端 / Search client
│   ├── models.py                       # 数据模型 / Data models
│   ├── rate_limiter.py                 # 速率限制器 / Rate limiter
│   └── config.py                       # 配置管理 / Configuration management
├── tests/                              # 测试文件 / Test files
│   ├── unit/                           # 单元测试 / Unit tests
│   ├── integration/                    # 集成测试 / Integration tests
│   └── docker/                         # Docker 测试 / Docker tests
├── examples/                           # 使用示例 / Usage examples
├── scripts/                            # 脚本文件 / Script files
├── config/                             # 配置文件 / Configuration files
├── docs/                               # 文档 / Documentation
├── pyproject.toml                      # 项目配置 / Project configuration
└── README.md                           # 项目说明 / Project description
```

### 核心组件 / Core Components

#### 1. 服务器主逻辑 / Main Server Logic

**文件 / File**: [`src/duckduckgo_mcp_server/server.py`](../src/duckduckgo_mcp_server/server.py)

主要功能 / Main Functions:
- MCP 协议处理 / MCP protocol handling
- 传输层管理 / Transport layer management
- 工具注册和调用 / Tool registration and invocation
- 错误处理和日志记录 / Error handling and logging

```python
class MCPServer:
    """MCP 服务器主类 / Main MCP server class"""

    def __init__(self, transport: str = "stdio"):
        self.transport = self._create_transport(transport)
        self.search_client = DuckDuckGoSearchClient()
        self.rate_limiter = RateLimiter()

    async def start(self):
        """启动服务器 / Start the server"""
        await self.transport.start()

    async def handle_request(self, request):
        """处理 MCP 请求 / Handle MCP request"""
        # 实现 MCP 协议逻辑 / Implement MCP protocol logic
        pass
```

#### 2. 传输层实现 / Transport Layer Implementation

**文件 / File**: [`src/duckduckgo_mcp_server/transports.py`](../src/duckduckgo_mcp_server/transports.py)

支持的传输模式 / Supported Transport Modes:
- **STDIO**: 标准输入输出，用于 Claude Desktop / Standard I/O for Claude Desktop
- **HTTP**: REST API 端点 / REST API endpoints
- **SSE**: 服务器发送事件 / Server-Sent Events
- **Hybrid**: 多传输模式组合 / Multi-transport combination

```python
class BaseTransport:
    """传输层基类 / Base transport class"""

    async def start(self):
        """启动传输服务 / Start transport service"""
        raise NotImplementedError

    async def handle_request(self, request):
        """处理请求 / Handle request"""
        raise NotImplementedError

class HTTPTransport(BaseTransport):
    """HTTP 传输实现 / HTTP transport implementation"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.app = FastAPI()
        self.setup_routes()

    def setup_routes(self):
        """设置路由 / Setup routes"""
        @self.app.post("/mcp")
        async def mcp_endpoint(request: MCPRequest):
            return await self.handle_mcp_request(request)
```

#### 3. 搜索客户端 / Search Client

**文件 / File**: [`src/duckduckgo_mcp_server/search_client.py`](../src/duckduckgo_mcp_server/search_client.py)

搜索功能 / Search Features:
- DuckDuckGo Web 搜索 / DuckDuckGo web search
- 安全搜索级别控制 / Safe search level control
- URL 重定向清理 / URL redirect cleanup
- 错误处理和重试 / Error handling and retry

```python
class DuckDuckGoSearchClient:
    """DuckDuckGo 搜索客户端 / DuckDuckGo search client"""

    def __init__(self):
        self.session = None
        self.use_duck_scrape = self._check_duck_scrape_available()

    async def search(self, query: str, count: int = 10, safe_search: str = "moderate"):
        """执行搜索 / Perform search"""
        try:
            if self.use_duck_scrape:
                return await self._duck_scrape_search(query, count, safe_search)
            else:
                return await self._html_search(query, count, safe_search)
        except Exception as e:
            logger.error(f"搜索失败 / Search failed: {e}")
            return await self._fallback_search(query, count, safe_search)
```

#### 4. 数据模型 / Data Models

**文件 / File**: [`src/duckduckgo_mcp_server/models.py`](../src/duckduckgo_mcp_server/models.py)

使用 Pydantic 进行数据验证和序列化 / Using Pydantic for data validation and serialization:

```python
class SearchRequest(BaseModel):
    """搜索请求模型 / Search request model"""
    query: str = Field(..., max_length=400, description="搜索查询 / Search query")
    count: int = Field(10, ge=1, le=20, description="结果数量 / Result count")
    safeSearch: str = Field("moderate", regex="^(strict|moderate|off)$")

class SearchResult(BaseModel):
    """搜索结果模型 / Search result model"""
    title: str
    url: str
    description: str
    snippet: Optional[str] = None
```

## 🛠️ 开发环境设置 / Development Environment Setup

### 环境要求 / Prerequisites

- Python 3.8+
- Git
- pip 或 poetry / pip or poetry
- Docker (可选 / optional)
- VS Code 或其他 IDE / VS Code or other IDE

### 克隆和设置 / Clone and Setup

```bash
# 克隆仓库 / Clone repository
git clone <repository-url>
cd duckduckgo-mcp-server-py

# 创建虚拟环境 / Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 / or
venv\Scripts\activate     # Windows

# 安装开发依赖 / Install development dependencies
pip install -e ".[dev]"

# 安装 pre-commit hooks / Install pre-commit hooks
pre-commit install
```

### 开发工具配置 / Development Tools Configuration

#### VS Code 配置 / VS Code Configuration

**.vscode/settings.json**:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

**.vscode/launch.json**:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug MCP Server",
            "type": "python",
            "request": "launch",
            "program": "-m",
            "args": ["duckduckgo_mcp_server.server", "--transport", "http"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

#### 代码质量工具 / Code Quality Tools

**pyproject.toml** 配置 / Configuration:
```toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
```

## 🧪 测试 / Testing

### 测试结构 / Test Structure

```
tests/
├── unit/                           # 单元测试 / Unit tests
│   ├── test_search_client.py       # 搜索客户端测试
│   ├── test_models.py              # 数据模型测试
│   ├── test_rate_limiter.py        # 速率限制测试
│   └── test_transports.py          # 传输层测试
├── integration/                    # 集成测试 / Integration tests
│   ├── test_integration.py         # 基础集成测试
│   ├── test_server.py              # 服务器端点测试
│   └── test_docker_integration.py  # Docker 集成测试
└── docker/                         # Docker 测试 / Docker tests
    └── test_docker_deployment.py   # Docker 部署测试
```

### 运行测试 / Running Tests

```bash
# 运行所有测试 / Run all tests
pytest

# 运行特定测试 / Run specific tests
pytest tests/unit/
pytest tests/integration/

# 运行带覆盖率的测试 / Run tests with coverage
pytest --cov=duckduckgo_mcp_server --cov-report=html

# 运行性能测试 / Run performance tests
pytest tests/performance/ -v

# 生成测试报告 / Generate test report
pytest --html=reports/test_report.html --self-contained-html
```

### 测试示例 / Test Examples

#### 单元测试 / Unit Test

```python
# tests/unit/test_search_client.py
import pytest
from duckduckgo_mcp_server.search_client import DuckDuckGoSearchClient

@pytest.mark.asyncio
class TestDuckDuckGoSearchClient:

    @pytest.fixture
    async def client(self):
        return DuckDuckGoSearchClient()

    async def test_search_basic(self, client):
        """测试基础搜索功能 / Test basic search functionality"""
        results = await client.search("Python programming", count=5)

        assert len(results) <= 5
        assert all(result.title for result in results)
        assert all(result.url for result in results)

    async def test_search_empty_query(self, client):
        """测试空查询处理 / Test empty query handling"""
        results = await client.search("", count=5)
        assert results == []

    async def test_search_long_query(self, client):
        """测试长查询处理 / Test long query handling"""
        long_query = "test " * 100
        results = await client.search(long_query, count=5)
        # 应该截断或返回错误 / Should truncate or return error
```

#### 集成测试 / Integration Test

```python
# tests/integration/test_integration.py
import pytest
import aiohttp
from duckduckgo_mcp_server.server import MCPServer

@pytest.mark.asyncio
class TestServerIntegration:

    @pytest.fixture
    async def server(self):
        server = MCPServer(transport="http")
        await server.start()
        yield server
        await server.stop()

    async def test_search_endpoint(self, server):
        """测试搜索端点 / Test search endpoint"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "duckduckgo_web_search",
                    "arguments": {
                        "query": "Python async",
                        "count": 3
                    }
                }
            }

            async with session.post(
                "http://localhost:8080/mcp",
                json=payload
            ) as response:
                assert response.status == 200
                result = await response.json()

                assert "result" in result
                assert "content" in result["result"]
```

## 📝 代码规范 / Coding Standards

### Python 代码风格 / Python Code Style

遵循 PEP 8 和 Black 格式化标准 / Follow PEP 8 and Black formatting standards:

```python
# 好的示例 / Good example
class SearchService:
    """搜索服务类 / Search service class"""

    def __init__(self, client: DuckDuckGoSearchClient):
        self.client = client
        self.logger = logging.getLogger(__name__)

    async def search_with_retry(
        self,
        query: str,
        max_retries: int = 3
    ) -> List[SearchResult]:
        """带重试的搜索 / Search with retry"""
        for attempt in range(max_retries):
            try:
                return await self.client.search(query)
            except Exception as e:
                self.logger.warning(f"搜索失败，重试 {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避

        return []
```

### 文档字符串 / Docstrings

使用 Google 风格的文档字符串 / Use Google-style docstrings:

```python
def process_search_results(
    results: List[SearchResult],
    max_count: int = 10
) -> List[Dict[str, str]]:
    """处理搜索结果并返回格式化数据。

    Args:
        results: 原始搜索结果列表 / List of raw search results
        max_count: 最大返回数量 / Maximum number of results to return

    Returns:
        格式化的搜索结果列表 / List of formatted search results

    Raises:
        ValueError: 当结果数量为负数时 / When result count is negative

    Example:
        >>> results = await search_client.search("Python")
        >>> formatted = process_search_results(results, 5)
        >>> len(formatted)
        5
    """
    if max_count < 0:
        raise ValueError("max_count must be non-negative")

    return [
        {
            "title": result.title,
            "url": result.url,
            "description": result.description
        }
        for result in results[:max_count]
    ]
```

### 错误处理 / Error Handling

```python
# 好的错误处理 / Good error handling
class SearchError(Exception):
    """搜索相关错误 / Search-related error"""
    pass

class RateLimitError(SearchError):
    """速率限制错误 / Rate limit error"""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")

async def safe_search(query: str) -> List[SearchResult]:
    """安全的搜索函数 / Safe search function"""
    try:
        return await search_client.search(query)
    except RateLimitError as e:
        logger.warning(f"速率限制，等待 {e.retry_after} 秒")
        await asyncio.sleep(e.retry_after)
        return await safe_search(query)
    except SearchError as e:
        logger.error(f"搜索失败: {e}")
        return []
    except Exception as e:
        logger.exception(f"未预期的错误: {e}")
        raise
```

## 🔄 CI/CD 流程 / CI/CD Pipeline

### GitHub Actions 工作流 / GitHub Actions Workflow

**.github/workflows/ci.yml**:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Run tests
      run: |
        pytest --cov=duckduckgo_mcp_server --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  docker:
    runs-on: ubuntu-latest
    needs: test

    steps:
    - uses: actions/checkout@v3

    - name: Build Docker image
      run: |
        docker build -t duckduckgo-mcp-server:${{ github.sha }} .
        docker tag duckduckgo-mcp-server:${{ github.sha }} duckduckgo-mcp-server:latest

    - name: Run Docker tests
      run: |
        docker-compose --profile test up --abort-on-container-exit

    - name: Push to registry (if main branch)
      if: github.ref == 'refs/heads/main'
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push duckduckgo-mcp-server:latest
```

## 🤝 贡献指南 / Contributing Guidelines

### 开发流程 / Development Workflow

1. **Fork 项目 / Fork the project**
2. **创建功能分支 / Create feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **编写代码和测试 / Write code and tests**
4. **运行测试套件 / Run test suite**
   ```bash
   pytest
   black src/ tests/
   isort src/ tests/
   mypy src/
   ```
5. **提交更改 / Commit changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
6. **推送分支 / Push branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **创建 Pull Request / Create Pull Request**

### 提交信息规范 / Commit Message Convention

使用 Conventional Commits 格式 / Use Conventional Commits format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型 / Types:
- `feat`: 新功能 / New feature
- `fix`: 错误修复 / Bug fix
- `docs`: 文档更新 / Documentation update
- `style`: 代码格式化 / Code formatting
- `refactor`: 代码重构 / Code refactoring
- `test`: 测试相关 / Test related
- `chore`: 构建或辅助工具变更 / Build or tooling changes

示例 / Examples:
```bash
git commit -m "feat(search): add image search support"
git commit -m "fix(rate-limiter): handle redis connection errors"
git commit -m "docs(api): update SSE endpoint documentation"
```

### 代码审查清单 / Code Review Checklist

- [ ] 代码符合项目规范 / Code follows project standards
- [ ] 包含适当的测试 / Includes appropriate tests
- [ ] 文档已更新 / Documentation is updated
- [ ] 无安全漏洞 / No security vulnerabilities
- [ ] 性能影响可接受 / Performance impact is acceptable
- [ ] 向后兼容性 / Backward compatibility maintained

## 🔧 调试和性能分析 / Debugging and Performance Analysis

### 调试工具 / Debugging Tools

#### 日志配置 / Logging Configuration

```python
# config/logging.py
import logging
import sys

def setup_logging(level: str = "INFO"):
    """设置日志配置 / Setup logging configuration"""

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )

    # 设置第三方库日志级别 / Set third-party library log levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
```

#### 性能监控 / Performance Monitoring

```python
# src/duckduckgo_mcp_server/monitoring.py
import time
import functools
from typing import Callable

def monitor_performance(func: Callable) -> Callable:
    """性能监控装饰器 / Performance monitoring decorator"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"{func.__name__} 执行时间 / execution time: {duration:.2f}s")

    return wrapper

# 使用示例 / Usage example
@monitor_performance
async def search_with_monitoring(query: str) -> List[SearchResult]:
    return await search_client.search(query)
```

## 📚 扩展开发 / Extension Development

### 添加新的传输模式 / Adding New Transport Modes

```python
# src/duckduckgo_mcp_server/transports.py
class WebSocketTransport(BaseTransport):
    """WebSocket 传输实现 / WebSocket transport implementation"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8082):
        self.host = host
        self.port = port
        self.connections = set()

    async def start(self):
        """启动 WebSocket 服务器 / Start WebSocket server"""
        # 实现 WebSocket 服务器逻辑 / Implement WebSocket server logic
        pass

    async def handle_message(self, websocket, message):
        """处理 WebSocket 消息 / Handle WebSocket message"""
        # 实现消息处理逻辑 / Implement message handling logic
        pass

# 注册新传输 / Register new transport
TRANSPORT_REGISTRY["websocket"] = WebSocketTransport
```

### 添加新的搜索引擎 / Adding New Search Engines

```python
# src/duckduckgo_mcp_server/search_engines/
class SearchEngine(ABC):
    """搜索引擎基类 / Base search engine class"""

    @abstractmethod
    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """执行搜索 / Perform search"""
        pass

class GoogleSearchEngine(SearchEngine):
    """Google 搜索引擎 / Google search engine"""

    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        # 实现 Google 搜索逻辑 / Implement Google search logic
        pass

# 在搜索客户端中使用 / Use in search client
class UniversalSearchClient:
    def __init__(self):
        self.engines = {
            "duckduckgo": DuckDuckGoSearchEngine(),
            "google": GoogleSearchEngine(),
        }

    async def search(self, query: str, engine: str = "duckduckgo", **kwargs):
        """使用指定引擎搜索 / Search with specified engine"""
        if engine not in self.engines:
            raise ValueError(f"Unsupported search engine: {engine}")

        return await self.engines[engine].search(query, **kwargs)
```

## 📖 学习资源 / Learning Resources

### 相关文档 / Related Documentation

- [MCP 协议规范 / MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastAPI 官方文档 / FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic 文档 / Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [asyncio 文档 / asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

### 推荐阅读 / Recommended Reading

- 《Effective Python》- Brett Slatkin
- 《Fluent Python》- Luciano Ramalho
- 《Clean Architecture》- Robert C. Martin

---

**文档版本 / Documentation Version**: v0.1.2
**最后更新 / Last Updated**: 2025-10-22
**维护者 / Maintainer**: Claude Code Assistant