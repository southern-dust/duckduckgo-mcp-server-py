# 部署文档 / Deployment Guide

[中文](deployment_zh.md) | [English](deployment_en.md)

## 概述 / Overview

本文档详细介绍了 DuckDuckGo MCP Server 的各种部署方案，包括本地开发、Docker 容器化部署和生产环境配置。

This document provides detailed deployment guides for DuckDuckGo MCP Server, including local development, Docker containerization, and production environment configuration.

## 📋 部署前准备 / Prerequisites

### 系统要求 / System Requirements

- **操作系统 / Operating System**: Linux, macOS, Windows
- **Python 版本 / Python Version**: 3.8 或更高 / 3.8 or higher
- **内存 / Memory**: 最少 512MB / Minimum 512MB
- **磁盘空间 / Disk Space**: 最少 1GB / Minimum 1GB

### 依赖软件 / Required Software

```bash
# 基础依赖 / Basic dependencies
python >= 3.8
pip >= 21.0

# Docker 部署 / Docker deployment (可选 / optional)
docker >= 20.10
docker-compose >= 2.0

# 开发工具 / Development tools (可选 / optional)
git
node.js (用于前端客户端 / for frontend clients)
```

## 🚀 本地开发部署 / Local Development Deployment

### 方式一：直接安装 / Method 1: Direct Installation

```bash
# 1. 克隆项目 / Clone the repository
git clone <repository-url>
cd duckduckgo-mcp-server-py

# 2. 创建虚拟环境 / Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 / or
venv\Scripts\activate     # Windows

# 3. 安装依赖 / Install dependencies
pip install -e .

# 4. 可选：安装 duck-duck-scrape-py 集成
pip install -e /path/to/duck-duck-scrape-py

# 5. 运行服务器 / Run the server
python -m duckduckgo_mcp_server.server --transport stdio
```

### 方式二：开发模式 / Method 2: Development Mode

```bash
# 安装开发依赖 / Install development dependencies
pip install -e ".[dev]"

# 运行测试 / Run tests
pytest

# 代码格式化 / Code formatting
black src/
isort src/

# 类型检查 / Type checking
mypy src/
```

## 🐳 Docker 部署 / Docker Deployment

### 构建镜像 / Build Image

```bash
# 构建基础镜像 / Build base image
docker build -t duckduckgo-mcp-server:latest .

# 构建特定版本 / Build specific version
docker build -t duckduckgo-mcp-server:v0.1.2 .
```

### Docker Compose 部署 / Docker Compose Deployment

#### 1. 开发环境 / Development Environment

```bash
# STDIO 传输模式 / STDIO transport mode
docker-compose --profile stdio up

# HTTP API 模式 / HTTP API mode
docker-compose --profile http up

# SSE 事件流模式 / SSE event stream mode
docker-compose --profile sse up

# 混合模式 / Hybrid mode
docker-compose --profile hybrid up
```

#### 2. 生产环境 / Production Environment

```bash
# 基础生产环境 / Basic production environment
docker-compose --profile production up -d

# 增强环境（包含 Redis） / Enhanced environment (with Redis)
docker-compose --profile enhanced up -d

# 完整环境（包含监控） / Full environment (with monitoring)
docker-compose --profile full up -d
```

### Docker 配置文件 / Docker Configuration Files

#### docker-compose.yml / Production Services

```yaml
version: '3.8'

services:
  # HTTP API 服务 / HTTP API Service
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

  # SSE 服务 / SSE Service
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

  # Nginx 反向代理 / Nginx Reverse Proxy
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

  # Redis 缓存 / Redis Cache
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

## 🔧 环境配置 / Environment Configuration

### 环境变量 / Environment Variables

| 变量名 / Variable | 默认值 / Default | 描述 / Description |
|------------------|------------------|-------------------|
| `MCP_SERVER_TRANSPORT` | `stdio` | 传输模式 / Transport mode |
| `MCP_SERVER_HOST` | `0.0.0.0` | 服务器主机 / Server host |
| `MCP_SERVER_PORT` | `8080` | HTTP 服务器端口 / HTTP server port |
| `MCP_SSE_PORT` | `8081` | SSE 服务器端口 / SSE server port |
| `MCP_LOG_LEVEL` | `INFO` | 日志级别 / Log level |
| `MCP_RATE_LIMIT_PER_SEC` | `1` | 每秒速率限制 / Per second rate limit |
| `MCP_RATE_LIMIT_PER_MONTH` | `15000` | 每月速率限制 / Per month rate limit |
| `REDIS_URL` | - | Redis 连接 URL / Redis connection URL |

### 配置文件 / Configuration Files

#### .env 文件示例 / .env File Example

```bash
# 服务器配置 / Server configuration
MCP_SERVER_TRANSPORT=hybrid
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8080
MCP_SSE_PORT=8081
MCP_LOG_LEVEL=INFO

# 速率限制 / Rate limiting
MCP_RATE_LIMIT_PER_SEC=1
MCP_RATE_LIMIT_PER_MONTH=15000

# Redis 配置 / Redis configuration (可选 / optional)
REDIS_URL=redis://redis:6379/0

# 安全配置 / Security configuration (可选 / optional)
MCP_API_KEY=your_api_key_here
MCP_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## 🌐 生产环境部署 / Production Deployment

### 1. 服务器准备 / Server Preparation

```bash
# 更新系统 / Update system
sudo apt update && sudo apt upgrade -y

# 安装 Docker / Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose / Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 部署配置 / Deployment Configuration

```bash
# 创建部署目录 / Create deployment directory
sudo mkdir -p /opt/duckduckgo-mcp
cd /opt/duckduckgo-mcp

# 复制项目文件 / Copy project files
sudo cp -r /path/to/duckduckgo-mcp-server-py/* .

# 设置权限 / Set permissions
sudo chown -R $USER:$USER .
sudo chmod +x scripts/*.sh
```

### 3. SSL 证书配置 / SSL Certificate Configuration

```bash
# 创建 SSL 目录 / Create SSL directory
mkdir -p ssl

# 使用 Let's Encrypt (推荐) / Use Let's Encrypt (recommended)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# 复制证书 / Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
```

### 4. Nginx 配置 / Nginx Configuration

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

    # HTTP 重定向到 HTTPS / HTTP redirect to HTTPS
    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS 主配置 / HTTPS main configuration
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # SSL 配置 / SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;

        # 安全头 / Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # API 代理 / API proxy
        location /mcp {
            proxy_pass http://duckduckgo_http;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # SSE 代理 / SSE proxy
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

        # 健康检查 / Health check
        location /health {
            proxy_pass http://duckduckgo_http;
            access_log off;
        }
    }
}
```

### 5. 启动生产服务 / Start Production Services

```bash
# 启动生产环境 / Start production environment
docker-compose --profile production up -d

# 检查服务状态 / Check service status
docker-compose ps

# 查看日志 / View logs
docker-compose logs -f
```

## 🔍 监控和日志 / Monitoring and Logging

### 健康检查 / Health Checks

```bash
# 检查所有服务健康状态 / Check all services health
curl http://localhost/health

# 检查各个服务 / Check individual services
curl http://localhost:8080/health  # HTTP API
curl http://localhost:8081/health  # SSE
curl http://localhost:6379/ping    # Redis
```

### 日志管理 / Log Management

```bash
# 查看应用日志 / View application logs
docker-compose logs -f duckduckgo-http
docker-compose logs -f duckduckgo-sse

# 查看访问日志 / View access logs
docker-compose logs -f nginx

# 设置日志轮转 / Set up log rotation
sudo nano /etc/logrotate.d/docker-containers
```

### 性能监控 / Performance Monitoring

```bash
# 系统资源监控 / System resource monitoring
docker stats

# 容器资源使用 / Container resource usage
docker-compose exec duckduckgo-http top
docker-compose exec duckduckgo-sse top

# 网络连接 / Network connections
netstat -tulpn | grep :8080
netstat -tulpn | grep :8081
```

## 🔧 故障排除 / Troubleshooting

### 常见问题 / Common Issues

#### 1. 服务无法启动 / Service Won't Start

```bash
# 检查端口占用 / Check port conflicts
sudo netstat -tulpn | grep :8080
sudo lsof -i :8080

# 检查 Docker 状态 / Check Docker status
sudo systemctl status docker
sudo docker info

# 重新构建镜像 / Rebuild image
docker-compose build --no-cache
```

#### 2. 搜索功能异常 / Search Function Issues

```bash
# 检查网络连接 / Check network connectivity
docker-compose exec duckduckgo-http ping duckduckgo.com

# 查看详细错误日志 / View detailed error logs
docker-compose logs duckduckgo-http | grep ERROR

# 测试搜索功能 / Test search functionality
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"duckduckgo_web_search","arguments":{"query":"test"}}}'
```

#### 3. 速率限制问题 / Rate Limiting Issues

```bash
# 检查速率限制状态 / Check rate limit status
curl -I http://localhost:8080/health

# 重置速率限制 / Reset rate limit (Redis)
docker-compose exec redis redis-cli FLUSHALL
```

### 调试模式 / Debug Mode

```bash
# 启用调试日志 / Enable debug logging
export MCP_LOG_LEVEL=DEBUG
docker-compose up --force-recreate

# 进入容器调试 / Debug inside container
docker-compose exec duckduckgo-http /bin/bash
```

## 🔄 更新和维护 / Updates and Maintenance

### 应用更新 / Application Updates

```bash
# 拉取最新代码 / Pull latest code
git pull origin main

# 重新构建和部署 / Rebuild and deploy
docker-compose build
docker-compose up -d

# 验证更新 / Verify update
curl http://localhost/health
```

### 定期维护 / Regular Maintenance

```bash
# 清理 Docker 资源 / Clean up Docker resources
docker system prune -f

# 备份配置 / Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz config/ .env ssl/

# 更新 SSL 证书 / Update SSL certificates
sudo certbot renew
```

## 🔒 安全最佳实践 / Security Best Practices

1. **定期更新 / Regular Updates**: 保持系统和容器镜像最新 / Keep system and container images updated
2. **最小权限原则 / Principle of Least Privilege**: 使用非 root 用户运行服务 / Run services with non-root users
3. **网络安全 / Network Security**: 配置防火墙和访问控制 / Configure firewalls and access control
4. **日志监控 / Log Monitoring**: 监控异常访问和错误 / Monitor abnormal access and errors
5. **备份策略 / Backup Strategy**: 定期备份配置和数据 / Regular backup of configuration and data

---

**文档版本 / Documentation Version**: v0.1.2
**最后更新 / Last Updated**: 2025-10-22
**维护者 / Maintainer**: Claude Code Assistant