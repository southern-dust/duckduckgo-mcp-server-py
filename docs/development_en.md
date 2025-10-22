# Development Guide

[中文](development_zh.md) | [English](development_en.md)

## Overview

This document provides a detailed development guide for DuckDuckGo MCP Server, including project architecture, coding standards, testing methods, and contribution processes.

## 🏗️ Project Architecture

### Directory Structure

```
duckduckgo-mcp-server-py/
├── src/duckduckgo_mcp_server/          # Core Package
│   ├── __init__.py                     # Package initialization
│   ├── server.py                       # Main server implementation
│   ├── transports.py                   # Transport layer implementations
│   ├── search_client.py                # Search client
│   ├── models.py                       # Data models
│   ├── rate_limiter.py                 # Rate limiter
│   └── config.py                       # Configuration management
├── tests/                              # Test files
│   ├── unit/                           # Unit tests
│   ├── integration/                    # Integration tests
│   └── docker/                         # Docker tests
├── examples/                           # Usage examples
├── scripts/                            # Script files
├── config/                             # Configuration files
├── docs/                               # Documentation
├── pyproject.toml                      # Project configuration
└── README.md                           # Project description
```

### Core Components

#### 1. Main Server Logic

**File**: [`src/duckduckgo_mcp_server/server.py`](../src/duckduckgo_mcp_server/server.py)

Main Functions:
- MCP protocol handling
- Transport layer management
- Tool registration and invocation
- Error handling and logging

```python
class MCPServer:
    """Main MCP server class"""

    def __init__(self, transport: str = "stdio"):
        self.transport = self._create_transport(transport)
        self.search_client = DuckDuckGoSearchClient()
        self.rate_limiter = RateLimiter()

    async def start(self):
        """Start the server"""
        await self.transport.start()

    async def handle_request(self, request):
        """Handle MCP request"""
        # Implement MCP protocol logic
        pass
```

#### 2. Transport Layer Implementation

**File**: [`src/duckduckgo_mcp_server/transports.py`](../src/duckduckgo_mcp_server/transports.py)

Supported Transport Modes:
- **STDIO**: Standard I/O for Claude Desktop
- **HTTP**: REST API endpoints
- **SSE**: Server-Sent Events
- **Hybrid**: Multi-transport combination

```python
class BaseTransport:
    """Base transport class"""

    async def start(self):
        """Start transport service"""
        raise NotImplementedError

    async def handle_request(self, request):
        """Handle request"""
        raise NotImplementedError

class HTTPTransport(BaseTransport):
    """HTTP transport implementation"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.app = FastAPI()
        self.setup_routes()

    def setup_routes(self):
        """Setup routes"""
        @self.app.post("/mcp")
        async def mcp_endpoint(request: MCPRequest):
            return await self.handle_mcp_request(request)
```

#### 3. Search Client

**File**: [`src/duckduckgo_mcp_server/search_client.py`](../src/duckduckgo_mcp_server/search_client.py)

Search Features:
- DuckDuckGo web search
- Safe search level control
- URL redirect cleanup
- Error handling and retry

```python
class DuckDuckGoSearchClient:
    """DuckDuckGo search client"""

    def __init__(self):
        self.session = None
        self.use_duck_scrape = self._check_duck_scrape_available()

    async def search(self, query: str, count: int = 10, safe_search: str = "moderate"):
        """Perform search"""
        try:
            if self.use_duck_scrape:
                return await self._duck_scrape_search(query, count, safe_search)
            else:
                return await self._html_search(query, count, safe_search)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return await self._fallback_search(query, count, safe_search)
```

#### 4. Data Models

**File**: [`src/duckduckgo_mcp_server/models.py`](../src/duckduckgo_mcp_server/models.py)

Using Pydantic for data validation and serialization:

```python
class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., max_length=400, description="Search query")
    count: int = Field(10, ge=1, le=20, description="Result count")
    safeSearch: str = Field("moderate", regex="^(strict|moderate|off)$")

class SearchResult(BaseModel):
    """Search result model"""
    title: str
    url: str
    description: str
    snippet: Optional[str] = None
```

## 🛠️ Development Environment Setup

### Prerequisites

- Python 3.8+
- Git
- pip or poetry
- Docker (optional)
- VS Code or other IDE

### Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd duckduckgo-mcp-server-py

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Development Tools Configuration

#### VS Code Configuration

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

#### Code Quality Tools

**pyproject.toml** configuration:
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

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                           # Unit tests
│   ├── test_search_client.py       # Search client tests
│   ├── test_models.py              # Data model tests
│   ├── test_rate_limiter.py        # Rate limiter tests
│   └── test_transports.py          # Transport layer tests
├── integration/                    # Integration tests
│   ├── test_integration.py         # Basic integration tests
│   ├── test_server.py              # Server endpoint tests
│   └── test_docker_integration.py  # Docker integration tests
└── docker/                         # Docker tests
    └── test_docker_deployment.py   # Docker deployment tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/unit/
pytest tests/integration/

# Run tests with coverage
pytest --cov=duckduckgo_mcp_server --cov-report=html

# Run performance tests
pytest tests/performance/ -v

# Generate test report
pytest --html=reports/test_report.html --self-contained-html
```

### Test Examples

#### Unit Test

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
        """Test basic search functionality"""
        results = await client.search("Python programming", count=5)

        assert len(results) <= 5
        assert all(result.title for result in results)
        assert all(result.url for result in results)

    async def test_search_empty_query(self, client):
        """Test empty query handling"""
        results = await client.search("", count=5)
        assert results == []

    async def test_search_long_query(self, client):
        """Test long query handling"""
        long_query = "test " * 100
        results = await client.search(long_query, count=5)
        # Should truncate or return error
```

#### Integration Test

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
        """Test search endpoint"""
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

## 📝 Coding Standards

### Python Code Style

Follow PEP 8 and Black formatting standards:

```python
# Good example
class SearchService:
    """Search service class"""

    def __init__(self, client: DuckDuckGoSearchClient):
        self.client = client
        self.logger = logging.getLogger(__name__)

    async def search_with_retry(
        self,
        query: str,
        max_retries: int = 3
    ) -> List[SearchResult]:
        """Search with retry"""
        for attempt in range(max_retries):
            try:
                return await self.client.search(query)
            except Exception as e:
                self.logger.warning(f"Search failed, retry {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return []
```

### Docstrings

Use Google-style docstrings:

```python
def process_search_results(
    results: List[SearchResult],
    max_count: int = 10
) -> List[Dict[str, str]]:
    """Process search results and return formatted data.

    Args:
        results: List of raw search results
        max_count: Maximum number of results to return

    Returns:
        List of formatted search results

    Raises:
        ValueError: When result count is negative

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

### Error Handling

```python
# Good error handling
class SearchError(Exception):
    """Search-related error"""
    pass

class RateLimitError(SearchError):
    """Rate limit error"""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")

async def safe_search(query: str) -> List[SearchResult]:
    """Safe search function"""
    try:
        return await search_client.search(query)
    except RateLimitError as e:
        logger.warning(f"Rate limited, waiting {e.retry_after} seconds")
        await asyncio.sleep(e.retry_after)
        return await safe_search(query)
    except SearchError as e:
        logger.error(f"Search failed: {e}")
        return []
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

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

## 🤝 Contributing Guidelines

### Development Workflow

1. **Fork the project**
2. **Create feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Write code and tests**
4. **Run test suite**
   ```bash
   pytest
   black src/ tests/
   isort src/ tests/
   mypy src/
   ```
5. **Commit changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
6. **Push branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Create Pull Request**

### Commit Message Convention

Use Conventional Commits format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation update
- `style`: Code formatting
- `refactor`: Code refactoring
- `test`: Test related
- `chore`: Build or tooling changes

Examples:
```bash
git commit -m "feat(search): add image search support"
git commit -m "fix(rate-limiter): handle redis connection errors"
git commit -m "docs(api): update SSE endpoint documentation"
```

### Code Review Checklist

- [ ] Code follows project standards
- [ ] Includes appropriate tests
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact is acceptable
- [ ] Backward compatibility maintained

## 🔧 Debugging and Performance Analysis

### Debugging Tools

#### Logging Configuration

```python
# config/logging.py
import logging
import sys

def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )

    # Set third-party library log levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
```

#### Performance Monitoring

```python
# src/duckduckgo_mcp_server/monitoring.py
import time
import functools
from typing import Callable

def monitor_performance(func: Callable) -> Callable:
    """Performance monitoring decorator"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"{func.__name__} execution time: {duration:.2f}s")

    return wrapper

# Usage example
@monitor_performance
async def search_with_monitoring(query: str) -> List[SearchResult]:
    return await search_client.search(query)
```

## 📚 Extension Development

### Adding New Transport Modes

```python
# src/duckduckgo_mcp_server/transports.py
class WebSocketTransport(BaseTransport):
    """WebSocket transport implementation"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8082):
        self.host = host
        self.port = port
        self.connections = set()

    async def start(self):
        """Start WebSocket server"""
        # Implement WebSocket server logic
        pass

    async def handle_message(self, websocket, message):
        """Handle WebSocket message"""
        # Implement message handling logic
        pass

# Register new transport
TRANSPORT_REGISTRY["websocket"] = WebSocketTransport
```

### Adding New Search Engines

```python
# src/duckduckgo_mcp_server/search_engines/
class SearchEngine(ABC):
    """Base search engine class"""

    @abstractmethod
    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """Perform search"""
        pass

class GoogleSearchEngine(SearchEngine):
    """Google search engine"""

    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        # Implement Google search logic
        pass

# Use in search client
class UniversalSearchClient:
    def __init__(self):
        self.engines = {
            "duckduckgo": DuckDuckGoSearchEngine(),
            "google": GoogleSearchEngine(),
        }

    async def search(self, query: str, engine: str = "duckduckgo", **kwargs):
        """Search with specified engine"""
        if engine not in self.engines:
            raise ValueError(f"Unsupported search engine: {engine}")

        return await self.engines[engine].search(query, **kwargs)
```

## 📖 Learning Resources

### Related Documentation

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

### Recommended Reading

- "Effective Python" - Brett Slatkin
- "Fluent Python" - Luciano Ramalho
- "Clean Architecture" - Robert C. Martin

---

**Documentation Version**: v0.1.2
**Last Updated**: 2025-10-22
**Maintainer**: Claude Code Assistant