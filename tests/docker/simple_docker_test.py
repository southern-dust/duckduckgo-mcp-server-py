#!/usr/bin/env python3
"""
简化的 Docker 多协议测试脚本
使用标准库测试 HTTP 和基础功能
"""

import json
import subprocess
import time
import requests
from typing import Dict

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def test_docker_build():
    """测试 Docker 镜像构建"""
    log("Testing Docker image build...")

    try:
        result = subprocess.run(
            ["docker", "build", "-t", "duckduckgo-test", "."],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            log("✅ Docker build successful")
            return True
        else:
            log(f"❌ Docker build failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        log("❌ Docker build timed out")
        return False
    except Exception as e:
        log(f"❌ Docker build error: {e}")
        return False

def test_container_startup(transport_mode="auto"):
    """测试容器启动"""
    log(f"Testing container startup with {transport_mode} mode...")

    try:
        # 清理可能存在的容器
        subprocess.run(["docker", "rm", "-f", "duckduckgo-test-container"],
                      capture_output=True)

        # 启动容器
        cmd = [
            "docker", "run", "-d",
            "--name", "duckduckgo-test-container",
            "-e", f"TRANSPORT_MODE={transport_mode}",
            "-p", "8080:8080",
            "-p", "8081:8081",
            "duckduckgo-test"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            container_id = result.stdout.strip()
            log(f"✅ Container started: {container_id[:12]}")

            # 等待服务启动
            log("Waiting for service to start...")
            time.sleep(5)

            return container_id
        else:
            log(f"❌ Container startup failed: {result.stderr}")
            return None

    except Exception as e:
        log(f"❌ Container startup error: {e}")
        return None

def test_http_health():
    """测试 HTTP 健康检查"""
    log("Testing HTTP health check...")

    try:
        response = requests.get("http://localhost:8080/health", timeout=10)

        if response.status_code == 200:
            health_data = response.json()
            log(f"✅ HTTP health check passed: {health_data.get('status')}")
            return health_data
        else:
            log(f"❌ HTTP health check failed: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        log(f"❌ HTTP health check error: {e}")
        return None

def test_sse_health():
    """测试 SSE 健康检查"""
    log("Testing SSE health check...")

    try:
        response = requests.get("http://localhost:8081/health", timeout=10)

        if response.status_code == 200:
            health_data = response.json()
            log(f"✅ SSE health check passed: {health_data.get('status')}")
            return health_data
        else:
            log(f"❌ SSE health check failed: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        log(f"❌ SSE health check error: {e}")
        return None

def test_http_search():
    """测试 HTTP 搜索功能"""
    log("Testing HTTP search functionality...")

    try:
        search_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "duckduckgo_web_search",
                "arguments": {
                    "query": "Python programming",
                    "count": 3,
                    "safeSearch": "moderate"
                }
            }
        }

        response = requests.post(
            "http://localhost:8080/mcp",
            json=search_payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            log("✅ HTTP search test passed")
            return result
        else:
            log(f"❌ HTTP search failed: {response.status_code}")
            return None

    except Exception as e:
        log(f"❌ HTTP search error: {e}")
        return None

def test_container_logs():
    """检查容器日志"""
    log("Checking container logs...")

    try:
        result = subprocess.run(
            ["docker", "logs", "duckduckgo-test-container"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            logs = result.stdout
            # 提取最后几行重要日志
            log_lines = logs.split('\n')[-10:]
            log("Recent container logs:")
            for line in log_lines:
                if line.strip():
                    log(f"  {line}")
            return logs
        else:
            log(f"❌ Failed to get logs: {result.stderr}")
            return None

    except Exception as e:
        log(f"❌ Log check error: {e}")
        return None

def cleanup_container():
    """清理测试容器"""
    log("Cleaning up test container...")

    try:
        subprocess.run(["docker", "rm", "-f", "duckduckgo-test-container"],
                      capture_output=True)
        log("✅ Container cleaned up")
    except Exception as e:
        log(f"⚠️ Cleanup warning: {e}")

def main():
    """主测试函数"""
    log("🚀 开始 Docker 多协议集成测试")
    log("=" * 50)

    results = {
        "build": False,
        "startup": False,
        "http_health": False,
        "sse_health": False,
        "http_search": False
    }

    try:
        # 1. 测试镜像构建
        if not test_docker_build():
            return results
        results["build"] = True

        # 2. 测试容器启动（自动模式）
        container_id = test_container_startup("auto")
        if not container_id:
            return results
        results["startup"] = True

        # 3. 测试 HTTP 健康检查
        http_health = test_http_health()
        if http_health:
            results["http_health"] = True

        # 4. 测试 SSE 健康检查
        sse_health = test_sse_health()
        if sse_health:
            results["sse_health"] = True

        # 5. 测试 HTTP 搜索功能
        search_result = test_http_search()
        if search_result:
            results["http_search"] = True

        # 6. 检查容器日志
        test_container_logs()

    except KeyboardInterrupt:
        log("\n⚠️ 测试被用户中断")
    except Exception as e:
        log(f"❌ 测试过程中发生错误: {e}")
    finally:
        # 清理
        cleanup_container()

    # 生成测试报告
    log("\n" + "=" * 50)
    log("📊 测试结果摘要")
    log("=" * 50)

    total_tests = len(results)
    passed_tests = sum(results.values())

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        log(f"{test_name.replace('_', ' ').title()}: {status}")

    log(f"\n总计: {passed_tests}/{total_tests} 测试通过")
    log(f"成功率: {passed_tests/total_tests*100:.1f}%")

    if passed_tests == total_tests:
        log("\n🎉 所有测试通过！Docker 多协议集成成功！")
    else:
        log("\n⚠️ 部分测试失败，请检查配置和服务状态")

    return results

if __name__ == "__main__":
    main()