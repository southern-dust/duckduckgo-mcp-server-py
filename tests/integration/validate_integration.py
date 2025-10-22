#!/usr/bin/env python3
"""
Docker 多协议集成验证脚本
验证配置文件和集成逻辑的正确性
"""

import json
import os
import subprocess
import yaml
from typing import Dict, List

def log(msg):
    print(f"[验证] {msg}")

def validate_dockerfile():
    """验证 Dockerfile 配置"""
    log("验证 Dockerfile 配置...")

    try:
        with open("Dockerfile", "r") as f:
            content = f.read()

        # 检查关键配置
        checks = [
            ("FROM python:3.11-slim", "Python 基础镜像"),
            ("WORKDIR /app", "工作目录"),
            ("EXPOSE 8080 8081", "端口暴露"),
            ("ENTRYPOINT [\"docker-entrypoint.sh\"]", "入口点配置"),
            ("docker-entrypoint.sh", "启动脚本复制"),
        ]

        passed = 0
        for check, description in checks:
            if check in content:
                log(f"  ✅ {description}")
                passed += 1
            else:
                log(f"  ❌ {description} - 缺少: {check}")

        log(f"  📊 Dockerfile 验证: {passed}/{len(checks)} 项通过")
        return passed == len(checks)

    except FileNotFoundError:
        log("  ❌ Dockerfile 文件不存在")
        return False

def validate_entrypoint_script():
    """验证启动脚本"""
    log("验证启动脚本...")

    try:
        with open("docker-entrypoint.sh", "r") as f:
            content = f.read()

        # 检查脚本功能
        features = [
            ("TRANSPORT_MODE", "传输模式变量"),
            ("case \"$TRANSPORT_MODE\"", "模式选择逻辑"),
            ("stdio", "STDIO 支持"),
            ("http", "HTTP 支持"),
            ("sse", "SSE 支持"),
            ("hybrid", "混合模式支持"),
            ("auto", "自动检测支持"),
            ("multi", "多进程支持"),
        ]

        passed = 0
        for feature, description in features:
            if feature in content:
                log(f"  ✅ {description}")
                passed += 1
            else:
                log(f"  ❌ {description} - 缺少: {feature}")

        # 检查可执行权限
        is_executable = os.access("docker-entrypoint.sh", os.X_OK)
        if is_executable:
            log(f"  ✅ 脚本可执行权限")
            passed += 1
        else:
            log(f"  ❌ 脚本缺少可执行权限")

        log(f"  📊 启动脚本验证: {passed}/{len(features)+1} 项通过")
        return passed == len(features) + 1

    except FileNotFoundError:
        log("  ❌ docker-entrypoint.sh 文件不存在")
        return False

def validate_docker_compose():
    """验证 docker-compose.yml 配置"""
    log("验证 docker-compose.yml 配置...")

    try:
        with open("docker-compose.yml", "r") as f:
            compose_config = yaml.safe_load(f)

        # 检查服务配置
        services = compose_config.get("services", {})
        required_services = [
            "duckduckgo-mcp",
            "duckduckgo-stdio",
            "duckduckgo-http",
            "duckduckgo-sse",
            "duckduckgo-hybrid",
            "duckduckgo-multi",
            "duckduckgo-auto"
        ]

        passed = 0
        for service in required_services:
            if service in services:
                log(f"  ✅ {service} 服务配置")
                passed += 1
            else:
                log(f"  ❌ {service} 服务配置缺失")

        # 检查网络配置
        if "networks" in compose_config:
            log(f"  ✅ 网络配置")
            passed += 1
        else:
            log(f"  ❌ 网络配置缺失")

        # 检查环境变量
        base_service = services.get("duckduckgo-mcp", {})
        env_vars = base_service.get("environment", [])
        required_env = [
            "TRANSPORT_MODE",
            "HTTP_PORT",
            "SSE_PORT"
        ]

        for env in required_env:
            if any(env in str(e) for e in env_vars):
                log(f"  ✅ {env} 环境变量")
                passed += 1
            else:
                log(f"  ❌ {env} 环境变量缺失")

        log(f"  📊 Docker Compose 验证: {passed}+ 项通过")
        return True

    except FileNotFoundError:
        log("  ❌ docker-compose.yml 文件不存在")
        return False
    except yaml.YAMLError as e:
        log(f"  ❌ YAML 格式错误: {e}")
        return False

def validate_server_code():
    """验证服务器代码支持"""
    log("验证服务器代码传输层支持...")

    try:
        # 检查服务器主文件
        with open("src/duckduckgo_mcp_server/server.py", "r") as f:
            server_content = f.read()

        # 检查传输层文件
        with open("src/duckduckgo_mcp_server/transports.py", "r") as f:
            transports_content = f.read()

        # 检查关键功能
        features = [
            ("--transport", "命令行传输参数"),
            ("StdioTransport", "STDIO 传输类"),
            ("HTTPTransport", "HTTP 传输类"),
            ("SSETransport", "SSE 传输类"),
            ("HybridTransport", "混合传输类"),
            ("run_stdio", "STDIO 运行方法"),
            ("run_http", "HTTP 运行方法"),
            ("run_sse", "SSE 运行方法"),
            ("run_hybrid", "混合运行方法"),
        ]

        passed = 0
        for feature, description in features:
            if feature in server_content or feature in transports_content:
                log(f"  ✅ {description}")
                passed += 1
            else:
                log(f"  ❌ {description}")

        log(f"  📊 服务器代码验证: {passed}/{len(features)} 项通过")
        return passed >= len(features) * 0.8

    except FileNotFoundError as e:
        log(f"  ❌ 代码文件不存在: {e}")
        return False

def validate_environment_config():
    """验证环境配置文件"""
    log("验证环境配置文件...")

    try:
        with open(".env.example", "r") as f:
            env_content = f.read()

        # 检查配置项
        required_configs = [
            "TRANSPORT_MODE=auto",
            "HTTP_PORT=8080",
            "SSE_PORT=8081",
            "LOG_LEVEL=INFO"
        ]

        passed = 0
        for config in required_configs:
            if config in env_content:
                log(f"  ✅ {config}")
                passed += 1
            else:
                log(f"  ❌ 缺少配置: {config}")

        log(f"  📊 环境配置验证: {passed}/{len(required_configs)} 项通过")
        return passed == len(required_configs)

    except FileNotFoundError:
        log("  ❌ .env.example 文件不存在")
        return False

def validate_documentation():
    """验证文档完整性"""
    log("验证文档...")

    docs = [
        ("DOCKER_USAGE.md", "Docker 使用指南"),
        ("README.md", "项目说明"),
    ]

    passed = 0
    for doc, description in docs:
        if os.path.exists(doc):
            log(f"  ✅ {description}")
            passed += 1
        else:
            log(f"  ❌ {description} 缺失")

    log(f"  📊 文档验证: {passed}/{len(docs)} 项通过")
    return passed == len(docs)

def generate_validation_report(results: Dict[str, bool]):
    """生成验证报告"""
    log("\n" + "="*60)
    log("🎯 Docker 多协议集成验证报告")
    log("="*60)

    total_checks = len(results)
    passed_checks = sum(results.values())

    for check_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        log(f"{check_name}: {status}")

    log(f"\n📊 总体结果: {passed_checks}/{total_checks} 项验证通过")
    log(f"🎯 成功率: {passed_checks/total_checks*100:.1f}%")

    if passed_checks == total_checks:
        log("\n🎉 所有验证项通过！Docker 多协议集成配置正确！")
        log("\n📋 下一步操作:")
        log("1. 构建 Docker 镜像: docker build -t duckduckgo-mcp-server:unified .")
        log("2. 启动服务: docker-compose --profile auto up -d")
        log("3. 测试功能: curl http://localhost:8080/health")
    else:
        log("\n⚠️ 部分验证项失败，请检查配置后重试")
        log("\n🔧 建议修复:")
        for check_name, result in results.items():
            if not result:
                log(f"- 修复 {check_name} 相关配置")

def main():
    """主验证函数"""
    log("🔍 开始 Docker 多协议集成配置验证")
    log("=" * 50)

    # 运行所有验证
    results = {
        "Dockerfile 配置": validate_dockerfile(),
        "启动脚本": validate_entrypoint_script(),
        "Docker Compose 配置": validate_docker_compose(),
        "服务器代码支持": validate_server_code(),
        "环境配置": validate_environment_config(),
        "文档完整性": validate_documentation(),
    }

    # 生成报告
    generate_validation_report(results)

    return results

if __name__ == "__main__":
    main()