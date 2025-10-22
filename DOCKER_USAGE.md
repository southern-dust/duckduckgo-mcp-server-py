# Docker 多协议集成使用指南

## 概述

DuckDuckGo MCP Server 现在支持在单个 Docker 镜像中集成所有传输协议：标准IO (stdio)、HTTP REST API、Server-Sent Events (SSE)。

## 镜像特性

### 🚀 统一镜像
- 单个 `duckduckgo-mcp-server:unified` 镜像
- 智能启动脚本自动检测和切换传输模式
- 支持多种部署场景

### 🔄 传输协议支持

| 协议 | 端口 | 用途 | 特点 |
|------|------|------|------|
| STDIO | - | 直接 MCP 客户端集成 | 最简单，无网络开销 |
| HTTP | 8080 | REST API 调用 | 易于集成，支持防火墙 |
| SSE | 8081 | 实时流式通信 | 支持推送，实时性好 |
| HYBRID | 8080, 8081 | HTTP + SSE 混合 | 灵活性最高 |
| MULTI | 8080, 8081 | 多进程并行 | 高可用性 |

## 快速开始

### 1. 构建镜像
```bash
docker build -t duckduckgo-mcp-server:unified .
```

### 2. 环境配置
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置
vim .env
```

### 3. 启动服务

#### 自动模式（推荐）
```bash
docker-compose --profile auto up -d
```

#### 手动选择协议
```bash
# HTTP 模式
docker-compose --profile http up -d

# SSE 模式
docker-compose --profile sse up -d

# 混合模式
docker-compose --profile hybrid up -d

# 多进程模式
docker-compose --profile multi up -d

# STDIO 模式（用于直接集成）
docker-compose --profile stdio up -d
```

## 使用场景

### 1. 开发环境 - 自动模式
```bash
# 自动检测最佳传输模式
docker run -d \
  --name duckduckgo-dev \
  -e TRANSPORT_MODE=auto \
  -p 8080:8080 \
  -p 8081:8081 \
  duckduckgo-mcp-server:unified
```

### 2. 生产环境 - 混合模式
```bash
# 使用 docker-compose
docker-compose --profile production up -d
```

### 3. 直接集成 - STDIO 模式
```bash
# 用于与 MCP 客户端直接通信
docker run -i --rm \
  -e TRANSPORT_MODE=stdio \
  duckduckgo-mcp-server:unified
```

### 4. 高可用 - 多进程模式
```bash
# 运行多个进程，每个协议独立
docker run -d \
  --name duckduckgo-ha \
  -e TRANSPORT_MODE=multi \
  -p 8080:8080 \
  -p 8081:8081 \
  duckduckgo-mcp-server:unified
```

## 环境变量配置

### 基础配置
```bash
# 传输模式
TRANSPORT_MODE=auto|stdio|http|sse|hybrid|multi

# 日志级别
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
```

### 网络配置
```bash
# HTTP 配置
HTTP_HOST=0.0.0.0
HTTP_PORT=8080

# SSE 配置
SSE_HOST=0.0.0.0
SSE_PORT=8081
```

### 高级配置
```bash
# 强制特定模式
HTTP_ONLY=true
SSE_ONLY=true

# MCP 客户端检测
MCP_CLIENT_ID=your-client-id
```

## API 端点

### HTTP 协议
- **搜索**: `POST http://localhost:8080/mcp`
- **健康检查**: `GET http://localhost:8080/health`
- **服务信息**: `GET http://localhost:8080/`

### SSE 协议
- **流式连接**: `GET http://localhost:8081/sse`
- **搜索请求**: `POST http://localhost:8081/sse/request`
- **健康检查**: `GET http://localhost:8081/health`
- **服务信息**: `GET http://localhost:8081/`

## 健康检查

### 自动健康检查
```bash
# 检查服务状态
curl -f http://localhost:8080/health
curl -f http://localhost:8081/health
```

### Docker 健康检查
```bash
# 查看容器健康状态
docker ps

# 查看健康检查日志
docker inspect duckduckgo-mcp-server | grep Health -A 10
```

## 性能优化

### 1. 资源限制
```yaml
# docker-compose.yml 中添加
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 256M
    reservations:
      cpus: '0.25'
      memory: 128M
```

### 2. 并发配置
```bash
# 调整 Python 异步处理
export PYTHONASYNCIODEBUG=1

# 调整 uvicorn 配置
export UVICORN_WORKERS=2
```

## 故障排除

### 1. 端口冲突
```bash
# 检查端口占用
netstat -tulpn | grep 8080
netstat -tulpn | grep 8081

# 修改端口
export HTTP_PORT=8082
export SSE_PORT=8083
```

### 2. 传输模式问题
```bash
# 查看启动日志
docker logs duckduckgo-mcp-server

# 强制特定模式
export TRANSPORT_MODE=stdio
```

### 3. 网络问题
```bash
# 检查容器网络
docker network ls
docker network inspect mcp-network

# 测试连接
docker exec -it duckduckgo-mcp-server curl http://localhost:8080/health
```

## 监控和日志

### 1. 日志查看
```bash
# 实时日志
docker-compose logs -f duckduckgo-mcp

# 特定服务日志
docker-compose logs -f duckduckgo-hybrid
```

### 2. 监控指标
```bash
# 容器资源使用
docker stats duckduckgo-mcp-server

# 健康检查状态
docker inspect --format='{{.State.Health.Status}}' duckduckgo-mcp-server
```

## 安全配置

### 1. 网络安全
```yaml
# 使用自定义网络
networks:
  mcp-secure:
    driver: bridge
    internal: true
```

### 2. 访问控制
```bash
# 限制外部访问
docker run -d \
  --network mcp-secure \
  -p 127.0.0.1:8080:8080 \
  duckduckgo-mcp-server:unified
```

## 最佳实践

1. **开发环境**: 使用 `auto` 模式，让系统自动选择
2. **生产环境**: 使用 `hybrid` 模式，提供最大灵活性
3. **高可用**: 使用 `multi` 模式，进程隔离
4. **直接集成**: 使用 `stdio` 模式，最小延迟
5. **监控**: 始终启用健康检查和日志记录

## 版本兼容性

- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **Python**: 3.11+
- **MCP Protocol**: 2.0+