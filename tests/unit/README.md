# Unit Tests

This directory contains unit tests for the DuckDuckGo MCP Server.

## Test Structure

```
tests/unit/
├── __init__.py                    # Package initialization
├── conftest.py                    # pytest configuration and fixtures
├── test_models.py                 # Tests for data models
├── test_search_client.py          # Tests for search client
├── test_rate_limiter.py           # Tests for rate limiter
├── test_transports.py             # Tests for transport layer
├── test_server.py                 # Tests for main server
├── test_config.py                 # Tests for configuration management
└── README.md                      # This file
```

## Test Coverage

### Models (`test_models.py`)
- **DuckDuckGoSearchArgs**: Test search argument validation and serialization
- **SearchResult**: Test search result model functionality
- Test cases for:
  - Field validation (query length, count bounds, safe search values)
  - Model serialization/deserialization
  - JSON handling
  - Unicode content support
  - Edge cases and error conditions

### Search Client (`test_search_client.py`)
- **DuckDuckGoSearchClient**: Test search functionality
- Test cases for:
  - Basic search operations
  - Safe search levels
  - URL redirect cleanup
  - Error handling and fallback mechanisms
  - Concurrent search requests
  - Parameter validation
  - Performance characteristics

### Rate Limiter (`test_rate_limiter.py`)
- **RateLimiter**: Test rate limiting functionality
- Test cases for:
  - Rate limit enforcement (per second and per month)
  - Concurrent request handling
  - Rate limit reset behavior
  - Status information reporting
  - Edge cases (zero limits, boundary conditions)
  - High concurrency stress testing

### Transports (`test_transports.py`)
- **HTTPTransport**: Test HTTP API transport
- **SSETransport**: Test Server-Sent Events transport
- **STDIOTransport**: Test standard I/O transport
- **HybridTransport**: Test combined transport
- Test cases for:
  - Transport initialization and configuration
  - Request/response handling
  - Health check endpoints
  - Connection management (SSE)
  - Error handling and validation
  - Start/stop functionality

### Server (`test_server.py`)
- **MCPServer**: Test main server implementation
- Test cases for:
  - Server initialization with different transports
  - MCP protocol handling (tools/list, tools/call)
  - Argument validation
  - Error handling and response formatting
  - Rate limiting integration
  - Health check functionality
  - Concurrent request handling
  - Graceful shutdown

### Configuration (`test_config.py`)
- Test cases for:
  - Default configuration values
  - Environment variable overrides
  - Configuration validation
  - Transport-specific configuration
  - Rate limiter configuration
  - Logging configuration
  - Invalid configuration handling

## Running Tests

### Run All Unit Tests
```bash
source .venv/bin/activate
python -m pytest tests/unit/ -v
```

### Run Specific Test File
```bash
source .venv/bin/activate
python -m pytest tests/unit/test_models.py -v
```

### Run Specific Test Class
```bash
source .venv/bin/activate
python -m pytest tests/unit/test_models.py::TestDuckDuckGoSearchArgs -v
```

### Run Specific Test Method
```bash
source .venv/bin/activate
python -m pytest tests/unit/test_models.py::TestDuckDuckGoSearchArgs::test_valid_search_args_minimal -v
```

### Run Tests with Coverage
```bash
source .venv/bin/activate
python -m pytest tests/unit/ --cov=duckduckgo_mcp_server --cov-report=html
```

## Test Fixtures

The `conftest.py` file provides several useful fixtures:

- `mock_logger`: Mock logger for testing
- `sample_search_results`: Sample search result data
- `sample_mcp_request`: Sample MCP request structure
- `sample_mcp_response`: Sample MCP response structure
- `event_loop`: Async event loop for async tests

## Test Data Factory

The `TestDataFactory` class provides methods to create test data:

- `create_search_request()`: Create search request models
- `create_search_results()`: Create search result data
- `create_mcp_error()`: Create MCP error responses
- `create_health_status()`: Create health status data

## Test Utilities

The `TestUtils` class provides utility functions:

- `assert_eventually()`: Assert condition becomes true within timeout
- `mock_async_response()`: Create mock async functions
- `assert_valid_mcp_response()`: Validate MCP response format
- `assert_valid_mcp_error()`: Validate MCP error format

## Async Testing

All tests that use async functionality are marked with `@pytest.mark.asyncio` and require pytest-asyncio.

## Mocking Strategy

The tests use extensive mocking to isolate components:

- Search client mocking for consistent test data
- Rate limiter mocking for predictable rate limit behavior
- Transport mocking to test protocol handling without network dependencies
- Configuration mocking to test different environment setups

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Mocking**: Mock external dependencies (network, databases, etc.)
3. **Assertion**: Use specific assertions with clear messages
4. **Edge Cases**: Test boundary conditions and error scenarios
5. **Async Handling**: Properly handle async/await in tests
6. **Fixtures**: Use fixtures for common test data and setup

## Coverage Goals

- **Models**: 100% coverage of validation logic
- **Search Client**: 90%+ coverage including error paths
- **Rate Limiter**: 95%+ coverage including edge cases
- **Transports**: 85%+ coverage of protocol handling
- **Server**: 90%+ coverage of MCP protocol implementation
- **Configuration**: 95%+ coverage of configuration logic

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the package is installed in development mode
   ```bash
   pip install -e .
   ```

2. **Async Test Errors**: Make sure pytest-asyncio is installed
   ```bash
   pip install pytest-asyncio
   ```

3. **Mock Issues**: Verify that the actual class/method names match the mocks

4. **Environment Variables**: Some tests may depend on specific environment setups

### Debugging Tests

Run tests with more verbose output:
```bash
python -m pytest tests/unit/ -v -s --tb=long
```

Run a specific test with debugging:
```bash
python -m pytest tests/unit/test_models.py::TestDuckDuckGoSearchArgs::test_valid_search_args_minimal -v -s --pdb
```

## Contributing

When adding new tests:

1. Follow the existing naming conventions
2. Add appropriate fixtures to `conftest.py` if needed
3. Include both positive and negative test cases
4. Test edge cases and error conditions
5. Ensure tests are fast and independent
6. Add documentation for complex test scenarios

---

**Last Updated**: 2025-10-22
**Test Framework**: pytest + pytest-asyncio
**Coverage Target**: 90%+ overall