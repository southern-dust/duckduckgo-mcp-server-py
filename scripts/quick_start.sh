#!/bin/bash

# DuckDuckGo MCP Server 多协议快速启动脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
DuckDuckGo MCP Server 多协议启动脚本

用法: $0 [选项] [模式]

模式:
  auto     - 自动检测最佳传输模式 (默认)
  stdio    - 标准输入输出模式
  http     - HTTP REST API 模式
  sse      - Server-Sent Events 模式
  hybrid   - 混合模式 (HTTP + SSE)
  multi    - 多进程模式 (所有协议)
  test     - 运行配置验证和测试

选项:
  -h, --help     显示此帮助信息
  -b, --build    强制重新构建镜像
  -d, --debug    启用调试模式
  -q, --quiet    静默模式
  -s, --stop     停止所有服务
  -l, --logs     查看服务日志
  -c, --clean    清理镜像和容器

示例:
  $0                    # 使用自动模式启动
  $0 http              # 使用 HTTP 模式启动
  $0 -b hybrid         # 重新构建并启动混合模式
  $0 -s                # 停止所有服务
  $0 test              # 运行配置验证

EOF
}

# 检查依赖
check_dependencies() {
    log "检查依赖..."

    if ! command -v docker &> /dev/null; then
        error "Docker 未安装或不在 PATH 中"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose 未安装或不在 PATH 中"
        exit 1
    fi

    success "依赖检查通过"
}

# 验证配置
validate_config() {
    log "验证配置..."

    if ! python3 validate_integration.py > /dev/null 2>&1; then
        error "配置验证失败"
        exit 1
    fi

    success "配置验证通过"
}

# 构建镜像
build_image() {
    local force_build=$1
    local image_name="duckduckgo-mcp-server:unified"

    # 检查镜像是否存在
    if docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$image_name" && [ "$force_build" != "true" ]; then
        log "Docker 镜像已存在，跳过构建 (使用 -b 强制重新构建)"
        return 0
    fi

    log "构建 Docker 镜像..."
    if docker build -t "$image_name" .; then
        success "镜像构建完成"
    else
        error "镜像构建失败"
        exit 1
    fi
}

# 停止服务
stop_services() {
    log "停止所有服务..."

    # 停止并删除容器
    docker-compose down --remove-orphans 2>/dev/null || true

    # 停止可能遗留的容器
    docker ps -q --filter "name=duckduckgo" | xargs -r docker stop 2>/dev/null || true
    docker ps -aq --filter "name=duckduckgo" | xargs -r docker rm 2>/dev/null || true

    success "所有服务已停止"
}

# 清理
cleanup() {
    log "清理 Docker 资源..."

    stop_services

    # 删除镜像
    docker rmi duckduckgo-mcp-server:unified 2>/dev/null || true
    docker rmi duckduckgo-test 2>/dev/null || true

    # 清理悬空镜像
    docker image prune -f 2>/dev/null || true

    success "清理完成"
}

# 启动服务
start_service() {
    local mode=$1
    local debug=$2

    log "启动 DuckDuckGo MCP Server (模式: $mode)"

    # 设置环境变量
    export LOG_LEVEL=${LOG_LEVEL:-INFO}
    if [ "$debug" = "true" ]; then
        export LOG_LEVEL=DEBUG
        log "启用调试模式"
    fi

    # 根据模式选择 profile
    case "$mode" in
        "stdio")
            profile="stdio"
            ;;
        "http")
            profile="http"
            ;;
        "sse")
            profile="sse"
            ;;
        "hybrid")
            profile="hybrid"
            ;;
        "multi")
            profile="multi"
            ;;
        "auto"|*)
            profile="auto"
            ;;
    esac

    log "使用 profile: $profile"

    # 启动服务
    if docker-compose --profile "$profile" up -d; then
        success "服务启动成功"
        show_service_info "$mode"
    else
        error "服务启动失败"
        exit 1
    fi
}

# 显示服务信息
show_service_info() {
    local mode=$1

    echo ""
    success "🎉 DuckDuckGo MCP Server 启动成功！"
    echo ""
    echo "📋 服务信息:"
    echo "   模式: $mode"
    echo "   容器: duckduckgo-mcp-server"
    echo ""

    case "$mode" in
        "stdio")
            echo "🔌 使用方法:"
            echo "   docker run -i --rm -e TRANSPORT_MODE=stdio duckduckgo-mcp-server:unified"
            ;;
        "http")
            echo "🌐 HTTP 端点:"
            echo "   健康检查: http://localhost:8080/health"
            echo "   搜索 API: http://localhost:8080/mcp"
            echo "   服务信息: http://localhost:8080/"
            ;;
        "sse")
            echo "📡 SSE 端点:"
            echo "   健康检查: http://localhost:8081/health"
            echo "   流式连接: http://localhost:8081/sse"
            echo "   搜索请求: http://localhost:8081/sse/request"
            ;;
        "hybrid"|"auto")
            echo "🌐 HTTP 端点:"
            echo "   健康检查: http://localhost:8080/health"
            echo "   搜索 API: http://localhost:8080/mcp"
            echo ""
            echo "📡 SSE 端点:"
            echo "   健康检查: http://localhost:8081/health"
            echo "   流式连接: http://localhost:8081/sse"
            ;;
        "multi")
            echo "🔄 多进程模式 - 所有协议可用"
            echo "🌐 HTTP 端点:"
            echo "   健康检查: http://localhost:8080/health"
            echo "   搜索 API: http://localhost:8080/mcp"
            echo ""
            echo "📡 SSE 端点:"
            echo "   健康检查: http://localhost:8081/health"
            echo "   流式连接: http://localhost:8081/sse"
            ;;
    esac

    echo ""
    echo "🔧 管理命令:"
    echo "   查看日志: $0 -l"
    echo "   停止服务: $0 -s"
    echo "   重新启动: $0"
    echo ""
    echo "📊 监控:"
    echo "   容器状态: docker ps"
    echo "   健康检查: curl http://localhost:8080/health"
    echo ""
}

# 显示日志
show_logs() {
    log "显示服务日志..."
    docker-compose logs -f --tail=50 2>/dev/null || {
        warning "Docker Compose 日志不可用，显示 Docker 容器日志:"
        docker logs -f --tail=50 duckduckgo-mcp-server 2>/dev/null || {
            error "没有找到运行中的容器"
            exit 1
        }
    }
}

# 运行测试
run_tests() {
    log "运行配置验证和功能测试..."

    # 配置验证
    log "1. 配置验证..."
    if python3 validate_integration.py; then
        success "配置验证通过"
    else
        error "配置验证失败"
        return 1
    fi

    echo ""

    # 简单功能测试
    log "2. 功能测试..."
    if [ -f "simple_docker_test.py" ]; then
        if python3 simple_docker_test.py; then
            success "功能测试通过"
        else
            warning "功能测试失败 (可能需要先构建镜像)"
        fi
    else
        warning "功能测试脚本不存在"
    fi

    echo ""
    success "测试完成"
}

# 主函数
main() {
    local mode="auto"
    local force_build="false"
    local debug="false"
    local quiet="false"
    local show_logs_only="false"
    local stop_only="false"
    local cleanup_only="false"
    local run_tests_only="false"

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -b|--build)
                force_build="true"
                shift
                ;;
            -d|--debug)
                debug="true"
                shift
                ;;
            -q|--quiet)
                quiet="true"
                shift
                ;;
            -s|--stop)
                stop_only="true"
                shift
                ;;
            -l|--logs)
                show_logs_only="true"
                shift
                ;;
            -c|--clean)
                cleanup_only="true"
                shift
                ;;
            test)
                run_tests_only="true"
                shift
                ;;
            auto|stdio|http|sse|hybrid|multi)
                mode="$1"
                shift
                ;;
            *)
                error "未知参数: $1"
                echo "使用 $0 --help 查看帮助"
                exit 1
                ;;
        esac
    done

    # 执行相应操作
    if [ "$cleanup_only" = "true" ]; then
        cleanup
        exit 0
    elif [ "$stop_only" = "true" ]; then
        stop_services
        exit 0
    elif [ "$show_logs_only" = "true" ]; then
        show_logs
        exit 0
    elif [ "$run_tests_only" = "true" ]; then
        run_tests
        exit 0
    fi

    # 正常启动流程
    if [ "$quiet" != "true" ]; then
        echo "🚀 DuckDuckGo MCP Server 多协议启动器"
        echo "========================================"
    fi

    # 检查依赖
    check_dependencies

    # 验证配置
    validate_config

    # 构建镜像
    build_image "$force_build"

    # 启动服务
    start_service "$mode" "$debug"
}

# 运行主函数
main "$@"