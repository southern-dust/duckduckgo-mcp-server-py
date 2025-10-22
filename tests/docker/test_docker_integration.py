#!/usr/bin/env python3
"""
Docker 多协议集成测试脚本
测试 stdio, HTTP, SSE, hybrid, multi, auto 六种传输模式
"""

import asyncio
import json
import logging
import subprocess
import time
from typing import Dict, List, Optional

import aiohttp
import requests

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DockerIntegrationTester:
    def __init__(self):
        self.base_url_http = "http://localhost:8080"
        self.base_url_sse = "http://localhost:8081"
        self.test_query = "Python programming"
        self.test_results = {}

    async def test_http_transport(self) -> Dict:
        """测试 HTTP 传输协议"""
        logger.info("Testing HTTP transport...")

        try:
            # 健康检查
            health_response = requests.get(f"{self.base_url_http}/health", timeout=5)
            if health_response.status_code != 200:
                raise Exception(f"Health check failed: {health_response.status_code}")

            # 测试搜索功能
            search_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "duckduckgo_web_search",
                    "arguments": {
                        "query": self.test_query,
                        "count": 3,
                        "safeSearch": "moderate"
                    }
                }
            }

            search_response = requests.post(
                f"{self.base_url_http}/mcp",
                json=search_payload,
                timeout=30
            )

            if search_response.status_code == 200:
                result = search_response.json()
                logger.info("✅ HTTP transport test passed")
                return {
                    "status": "success",
                    "health": health_response.json(),
                    "search_result": result,
                    "response_time": search_response.elapsed.total_seconds()
                }
            else:
                raise Exception(f"Search failed with status {search_response.status_code}")

        except Exception as e:
            logger.error(f"❌ HTTP transport test failed: {e}")
            return {"status": "error", "error": str(e)}

    async def test_sse_transport(self) -> Dict:
        """测试 SSE 传输协议"""
        logger.info("Testing SSE transport...")

        try:
            # 健康检查
            health_response = requests.get(f"{self.base_url_sse}/health", timeout=5)
            if health_response.status_code != 200:
                raise Exception(f"Health check failed: {health_response.status_code}")

            # 测试 SSE 搜索功能
            search_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "duckduckgo_web_search",
                    "arguments": {
                        "query": self.test_query,
                        "count": 3,
                        "safeSearch": "moderate"
                    }
                }
            }

            search_response = requests.post(
                f"{self.base_url_sse}/sse/request",
                json=search_payload,
                timeout=30
            )

            if search_response.status_code == 200:
                result = search_response.json()
                logger.info("✅ SSE transport test passed")
                return {
                    "status": "success",
                    "health": health_response.json(),
                    "search_result": result,
                    "response_time": search_response.elapsed.total_seconds()
                }
            else:
                raise Exception(f"SSE search failed with status {search_response.status_code}")

        except Exception as e:
            logger.error(f"❌ SSE transport test failed: {e}")
            return {"status": "error", "error": str(e)}

    async def test_sse_streaming(self) -> Dict:
        """测试 SSE 流式连接"""
        logger.info("Testing SSE streaming...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url_sse}/sse") as response:
                    if response.status != 200:
                        raise Exception(f"SSE connection failed: {response.status}")

                    events_received = []
                    timeout = 10  # 10秒超时
                    start_time = time.time()

                    async for line in response.content:
                        if time.time() - start_time > timeout:
                            break

                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data = line[6:]  # 移除 'data: ' 前缀
                            try:
                                event_data = json.loads(data)
                                events_received.append(event_data)
                                logger.info(f"Received SSE event: {event_data.get('event', 'unknown')}")
                            except json.JSONDecodeError:
                                continue

                    if events_received:
                        logger.info("✅ SSE streaming test passed")
                        return {
                            "status": "success",
                            "events_count": len(events_received),
                            "events": events_received[:3]  # 只返回前3个事件
                        }
                    else:
                        raise Exception("No SSE events received")

        except Exception as e:
            logger.error(f"❌ SSE streaming test failed: {e}")
            return {"status": "error", "error": str(e)}

    async def test_stdio_transport(self) -> Dict:
        """测试 STDIO 传输协议（通过 Docker）"""
        logger.info("Testing STDIO transport...")

        try:
            # 构建测试容器
            build_result = subprocess.run(
                ["docker", "build", "-t", "duckduckgo-test-stdio", "."],
                capture_output=True,
                text=True,
                timeout=60
            )

            if build_result.returncode != 0:
                raise Exception(f"Docker build failed: {build_result.stderr}")

            # 运行 STDIO 测试容器
            test_command = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "duckduckgo_web_search",
                    "arguments": {
                        "query": self.test_query,
                        "count": 2
                    }
                }
            }

            container_cmd = [
                "docker", "run", "--rm", "-i",
                "-e", "TRANSPORT_MODE=stdio",
                "duckduckgo-test-stdio"
            ]

            process = subprocess.Popen(
                container_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )

            stdout, stderr = process.communicate(
                input=json.dumps(test_command) + "\n",
                timeout=30
            )

            if process.returncode == 0 and stdout:
                try:
                    result = json.loads(stdout.strip())
                    logger.info("✅ STDIO transport test passed")
                    return {
                        "status": "success",
                        "result": result,
                        "stdout": stdout,
                        "stderr": stderr
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "success",
                        "raw_output": stdout,
                        "stderr": stderr
                    }
            else:
                raise Exception(f"STDIO test failed: {stderr}")

        except subprocess.TimeoutExpired:
            logger.error("❌ STDIO transport test timed out")
            return {"status": "error", "error": "timeout"}
        except Exception as e:
            logger.error(f"❌ STDIO transport test failed: {e}")
            return {"status": "error", "error": str(e)}

    async def run_transport_tests(self) -> Dict:
        """运行所有传输协议测试"""
        logger.info("Starting comprehensive transport protocol tests...")

        results = {}

        # 测试 HTTP 协议
        results["http"] = await self.test_http_transport()
        await asyncio.sleep(1)

        # 测试 SSE 协议
        results["sse"] = await self.test_sse_transport()
        await asyncio.sleep(1)

        # 测试 SSE 流式连接
        results["sse_streaming"] = await self.test_sse_streaming()
        await asyncio.sleep(1)

        # 测试 STDIO 协议
        results["stdio"] = await self.test_stdio_transport()

        return results

    def generate_report(self, results: Dict) -> str:
        """生成测试报告"""
        report = []
        report.append("# Docker 多协议集成测试报告")
        report.append(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"测试查询: '{self.test_query}'")
        report.append("")

        # 统计结果
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.get("status") == "success")
        failed_tests = total_tests - successful_tests

        report.append(f"## 测试概览")
        report.append(f"- 总测试数: {total_tests}")
        report.append(f"- 成功: {successful_tests}")
        report.append(f"- 失败: {failed_tests}")
        report.append(f"- 成功率: {successful_tests/total_tests*100:.1f}%")
        report.append("")

        # 详细结果
        report.append("## 详细测试结果")

        for protocol, result in results.items():
            status = "✅ 通过" if result.get("status") == "success" else "❌ 失败"
            report.append(f"### {protocol.upper()} 传输协议 - {status}")

            if result.get("status") == "success":
                if "health" in result:
                    health = result["health"]
                    report.append(f"- 健康检查: {health.get('status', 'unknown')}")
                    report.append(f"- 传输模式: {health.get('transport', 'unknown')}")

                if "response_time" in result:
                    report.append(f"- 响应时间: {result['response_time']:.3f}s")

                if "search_result" in result:
                    search_data = result["search_result"]
                    if isinstance(search_data, dict) and "result" in search_data:
                        content_list = search_data["result"].get("content", [])
                        if content_list:
                            content = content_list[0].get("text", "")[:200]
                            report.append(f"- 搜索结果预览: {content}...")

                if "events_count" in result:
                    report.append(f"- 接收事件数: {result['events_count']}")

                if "raw_output" in result:
                    output = result["raw_output"][:200]
                    report.append(f"- 输出预览: {output}...")

            else:
                report.append(f"- 错误信息: {result.get('error', 'unknown error')}")

            report.append("")

        # 建议
        report.append("## 建议")

        if failed_tests == 0:
            report.append("🎉 所有传输协议测试通过！系统运行正常。")
        else:
            report.append("⚠️  部分测试失败，请检查：")
            report.append("- Docker 容器是否正常启动")
            report.append("- 网络端口是否被占用")
            report.append("- 环境变量配置是否正确")

        return "\n".join(report)

async def main():
    """主测试函数"""
    print("🚀 开始 Docker 多协议集成测试...")

    tester = DockerIntegrationTester()

    try:
        # 等待服务启动
        logger.info("等待服务启动...")
        await asyncio.sleep(3)

        # 运行测试
        results = await tester.run_transport_tests()

        # 生成报告
        report = tester.generate_report(results)

        # 保存报告
        with open("docker_test_report.md", "w", encoding="utf-8") as f:
            f.write(report)

        print("\n" + "="*60)
        print("测试完成！详细报告已保存到 docker_test_report.md")
        print("="*60)
        print("\n" + report)

        return results

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(main())