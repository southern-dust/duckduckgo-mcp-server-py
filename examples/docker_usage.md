# Docker Usage Examples

This document provides comprehensive examples for using the DuckDuckGo MCP Server with Docker.

## Quick Start

### 1. Build the Image
```bash
docker build -t duckduckgo-mcp-server:latest .
```

### 2. Run with Different Transport Modes

#### STDIO Transport (for local development)
```bash
docker run -i --rm duckduckgo-mcp-server:latest \
  python -m duckduckgo_mcp_server.server --transport stdio
```

#### HTTP Transport
```bash
docker run -d --name duckduckgo-http \
  -p 8080:8080 \
  duckduckgo-mcp-server:latest \
  python -m duckduckgo_mcp_server.server --transport http --host 0.0.0.0
```

#### SSE Transport
```bash
docker run -d --name duckduckgo-sse \
  -p 8081:8081 \
  duckduckgo-mcp-server:latest \
  python -m duckduckgo_mcp_server.server --transport sse --host 0.0.0.0
```

#### Hybrid Mode (HTTP + SSE)
```bash
docker run -d --name duckduckgo-hybrid \
  -p 8080:8080 \
  -p 8081:8081 \
  duckduckgo-mcp-server:latest \
  python -m duckduckgo_mcp_server.server --transport hybrid
```

## Docker Compose Usage

### Available Profiles

1. **stdio**: STDIO transport only
2. **http**: HTTP transport only
3. **sse**: SSE transport only
4. **hybrid**: Both HTTP and SSE transports
5. **production**: Hybrid + Nginx reverse proxy
6. **enhanced**: Production + Redis for rate limiting

### Profile Commands

```bash
# STDIO transport
docker-compose --profile stdio up duckduckgo-stdio

# HTTP transport
docker-compose --profile http up duckduckgo-http

# SSE transport
docker-compose --profile sse up duckduckgo-sse

# Hybrid mode (both HTTP and SSE)
docker-compose --profile hybrid up

# Production with Nginx
docker-compose --profile production up

# Enhanced with Redis
docker-compose --profile enhanced up
```

### Detached Mode

```bash
# Run in background
docker-compose --profile production up -d

# View logs
docker-compose --profile production logs -f

# Stop services
docker-compose --profile production down
```

## Testing with Docker

### Test HTTP Endpoint
```bash
# Start HTTP service
docker-compose --profile http up -d duckduckgo-http

# Wait for service to be ready
sleep 10

# Test health check
curl http://localhost:8080/health

# Test search
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "duckduckgo_web_search",
      "arguments": {
        "query": "Docker containers",
        "count": 5
      }
    }
  }'
```

### Test SSE Endpoint
```bash
# Start SSE service
docker-compose --profile sse up -d duckduckgo-sse

# Test health check
curl http://localhost:8081/health

# Listen to SSE events (in another terminal)
curl -N http://localhost:8081/sse

# Test search request
curl -X POST http://localhost:8081/sse/request \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "duckduckgo_web_search",
      "arguments": {
        "query": "Server-Sent Events"
      }
    }
  }'
```

## Production Deployment

### Using Production Profile
```bash
# Start with Nginx reverse proxy
docker-compose --profile production up -d

# Check status
docker-compose --profile production ps

# View logs
docker-compose --profile production logs -f

# Test via Nginx
curl http://localhost/health
```

### Custom Configuration

#### Environment Variables
```bash
# Create .env file
cat > .env << EOF
PYTHONPATH=/app/src
LOG_LEVEL=INFO
HTTP_HOST=0.0.0.0
HTTP_PORT=8080
SSE_HOST=0.0.0.0
SSE_PORT=8081
EOF

# Use with docker-compose
docker-compose --profile production up --env-file .env
```

#### Custom Ports
```bash
# Override ports in docker-compose
HTTP_PORT=9090 SSE_PORT=9091 docker-compose --profile http up
```

### SSL/TLS Setup

#### Generate Self-Signed Certificates
```bash
# Create SSL directory
mkdir -p ssl

# Generate certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=US/ST=CA/L=SF/O=Example/CN=localhost"

# Start with SSL
docker-compose --profile production up
```

#### Use Existing Certificates
```bash
# Place certificates in ssl/ directory
cp your-cert.pem ssl/cert.pem
cp your-key.pem ssl/key.pem

# Start production profile
docker-compose --profile production up
```

## Monitoring

### Health Checks
```bash
# Check all services health
for port in 8080 8081 80; do
  echo "Checking port $port..."
  curl -s http://localhost:$port/health || echo "Port $port not responding"
done
```

### Logs Monitoring
```bash
# View all logs
docker-compose --profile production logs -f

# View specific service logs
docker-compose --profile production logs -f duckduckgo-hybrid
docker-compose --profile production logs -f nginx

# View last 100 lines
docker-compose --profile production logs --tail=100
```

### Resource Monitoring
```bash
# View resource usage
docker stats $(docker-compose --profile production ps -q)

# View container info
docker-compose --profile production ps
```

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :8080
netstat -tulpn | grep :8081

# Use different ports
HTTP_PORT=9090 SSE_PORT=9091 docker-compose --profile hybrid up
```

#### Permission Issues
```bash
# Fix file permissions if needed
sudo chown -R $USER:$USER .

# Clean up and rebuild
docker-compose --profile production down -v
docker-compose --profile production build --no-cache
```

#### Container Won't Start
```bash
# Check logs
docker-compose --profile production logs duckduckgo-hybrid

# Inspect container
docker inspect duckduckgo-mcp-hybrid

# Enter container for debugging
docker-compose --profile production exec duckduckgo-hybrid bash
```

### Debug Mode
```bash
# Run with debug logging
LOG_LEVEL=DEBUG docker-compose --profile http up duckduckgo-http

# Run with increased verbosity
docker run -it --rm duckduckgo-mcp-server:latest bash
```

## Cleanup

### Remove All Containers and Images
```bash
# Stop and remove containers
docker-compose --profile production down -v --remove-orphans

# Remove images
docker rmi duckduckgo-mcp-server:latest

# Clean up unused resources
docker system prune -a
```

### Reset Everything
```bash
# Complete cleanup
docker-compose down -v --remove-orphans
docker system prune -a --volumes
docker volume prune