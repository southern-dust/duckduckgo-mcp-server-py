# Deployment Guide

[中文](deployment_zh.md) | [English](deployment_en.md)

## Overview

This document provides detailed deployment guides for DuckDuckGo MCP Server, including local development, Docker containerization, and production environment configuration.

## 📋 Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, Windows
- **Python Version**: 3.8 or higher
- **Memory**: Minimum 512MB
- **Disk Space**: Minimum 1GB

### Required Software

```bash
# Basic dependencies
python >= 3.8
pip >= 21.0

# Docker deployment (optional)
docker >= 20.10
docker-compose >= 2.0

# Development tools (optional)
git
node.js (for frontend clients)
```

## 🚀 Local Development Deployment

### Method 1: Direct Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd duckduckgo-mcp-server-py

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -e .

# 4. Optional: Install duck-duck-scrape-py integration
pip install -e /path/to/duck-duck-scrape-py

# 5. Run the server
python -m duckduckgo_mcp_server.server --transport stdio
```

### Method 2: Development Mode

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black src/
isort src/

# Type checking
mypy src/
```

## 🐳 Docker Deployment

### Build Image

```bash
# Build base image
docker build -t duckduckgo-mcp-server:latest .

# Build specific version
docker build -t duckduckgo-mcp-server:v0.1.2 .
```

### Docker Compose Deployment

#### 1. Development Environment

```bash
# STDIO transport mode
docker-compose --profile stdio up

# HTTP API mode
docker-compose --profile http up

# SSE event stream mode
docker-compose --profile sse up

# Hybrid mode
docker-compose --profile hybrid up
```

#### 2. Production Environment

```bash
# Basic production environment
docker-compose --profile production up -d

# Enhanced environment (with Redis)
docker-compose --profile enhanced up -d

# Full environment (with monitoring)
docker-compose --profile full up -d
```

### Docker Configuration Files

#### docker-compose.yml / Production Services

```yaml
version: '3.8'

services:
  # HTTP API Service
  duckduckgo-http:
    build: .
    ports:
      - "8080:8080"
    environment:
      - MCP_SERVER_TRANSPORT=http
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=8080
      - MCP_LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # SSE Service
  duckduckgo-sse:
    build: .
    ports:
      - "8081:8081"
    environment:
      - MCP_SERVER_TRANSPORT=sse
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=8081
      - MCP_LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - duckduckgo-http
      - duckduckgo-sse
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

## 🔧 Environment Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_TRANSPORT` | `stdio` | Transport mode |
| `MCP_SERVER_HOST` | `0.0.0.0` | Server host |
| `MCP_SERVER_PORT` | `8080` | HTTP server port |
| `MCP_SSE_PORT` | `8081` | SSE server port |
| `MCP_LOG_LEVEL` | `INFO` | Log level |
| `MCP_RATE_LIMIT_PER_SEC` | `1` | Per second rate limit |
| `MCP_RATE_LIMIT_PER_MONTH` | `15000` | Per month rate limit |
| `REDIS_URL` | - | Redis connection URL |

### Configuration Files

#### .env File Example

```bash
# Server configuration
MCP_SERVER_TRANSPORT=hybrid
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8080
MCP_SSE_PORT=8081
MCP_LOG_LEVEL=INFO

# Rate limiting
MCP_RATE_LIMIT_PER_SEC=1
MCP_RATE_LIMIT_PER_MONTH=15000

# Redis configuration (optional)
REDIS_URL=redis://redis:6379/0

# Security configuration (optional)
MCP_API_KEY=your_api_key_here
MCP_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## 🌐 Production Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Deployment Configuration

```bash
# Create deployment directory
sudo mkdir -p /opt/duckduckgo-mcp
cd /opt/duckduckgo-mcp

# Copy project files
sudo cp -r /path/to/duckduckgo-mcp-server-py/* .

# Set permissions
sudo chown -R $USER:$USER .
sudo chmod +x scripts/*.sh
```

### 3. SSL Certificate Configuration

```bash
# Create SSL directory
mkdir -p ssl

# Use Let's Encrypt (recommended)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
```

### 4. Nginx Configuration

```nginx
# config/nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream duckduckgo_http {
        server duckduckgo-http:8080;
    }

    upstream duckduckgo_sse {
        server duckduckgo-sse:8081;
    }

    # HTTP redirect to HTTPS
    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS main configuration
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # API proxy
        location /mcp {
            proxy_pass http://duckduckgo_http;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # SSE proxy
        location /sse {
            proxy_pass http://duckduckgo_sse;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_cache off;
        }

        # Health check
        location /health {
            proxy_pass http://duckduckgo_http;
            access_log off;
        }
    }
}
```

### 5. Start Production Services

```bash
# Start production environment
docker-compose --profile production up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🔍 Monitoring and Logging

### Health Checks

```bash
# Check all services health
curl http://localhost/health

# Check individual services
curl http://localhost:8080/health  # HTTP API
curl http://localhost:8081/health  # SSE
curl http://localhost:6379/ping    # Redis
```

### Log Management

```bash
# View application logs
docker-compose logs -f duckduckgo-http
docker-compose logs -f duckduckgo-sse

# View access logs
docker-compose logs -f nginx

# Set up log rotation
sudo nano /etc/logrotate.d/docker-containers
```

### Performance Monitoring

```bash
# System resource monitoring
docker stats

# Container resource usage
docker-compose exec duckduckgo-http top
docker-compose exec duckduckgo-sse top

# Network connections
netstat -tulpn | grep :8080
netstat -tulpn | grep :8081
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check port conflicts
sudo netstat -tulpn | grep :8080
sudo lsof -i :8080

# Check Docker status
sudo systemctl status docker
sudo docker info

# Rebuild image
docker-compose build --no-cache
```

#### 2. Search Function Issues

```bash
# Check network connectivity
docker-compose exec duckduckgo-http ping duckduckgo.com

# View detailed error logs
docker-compose logs duckduckgo-http | grep ERROR

# Test search functionality
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"duckduckgo_web_search","arguments":{"query":"test"}}}'
```

#### 3. Rate Limiting Issues

```bash
# Check rate limit status
curl -I http://localhost:8080/health

# Reset rate limit (Redis)
docker-compose exec redis redis-cli FLUSHALL
```

### Debug Mode

```bash
# Enable debug logging
export MCP_LOG_LEVEL=DEBUG
docker-compose up --force-recreate

# Debug inside container
docker-compose exec duckduckgo-http /bin/bash
```

## 🔄 Updates and Maintenance

### Application Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and deploy
docker-compose build
docker-compose up -d

# Verify update
curl http://localhost/health
```

### Regular Maintenance

```bash
# Clean up Docker resources
docker system prune -f

# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz config/ .env ssl/

# Update SSL certificates
sudo certbot renew
```

## 🔒 Security Best Practices

1. **Regular Updates**: Keep system and container images updated
2. **Principle of Least Privilege**: Run services with non-root users
3. **Network Security**: Configure firewalls and access control
4. **Log Monitoring**: Monitor abnormal access and errors
5. **Backup Strategy**: Regular backup of configuration and data

---

**Documentation Version**: v0.1.2
**Last Updated**: 2025-10-22
**Maintainer**: Claude Code Assistant