# 文件名: ollama_agent.py

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx
import asyncio

from Utils.Messages.messageStruct.userInput import Message
from Utils.Messages.messageStorage.messageToSqlite import MemorySystem
from abc import ABC, abstractmethod

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class Tool(ABC):
    """工具基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass


class WebSearchTool(Tool):
    """网页搜索工具"""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "搜索互联网信息，返回相关结果"

    async def execute(self, query: str, num_results: int = 5) -> List[Dict]:
        """模拟网页搜索"""
        # 这里可以集成实际的搜索API
        logger.info(f"搜索: {query}")
        return [
            {"title": f"关于{query}的结果1", "url": "http://example1.com", "snippet": f"这是关于{query}的信息片段..."},
            {"title": f"关于{query}的结果2", "url": "http://example2.com", "snippet": f"另一个关于{query}的信息..."}
        ]


class CalculatorTool(Tool):
    """计算器工具"""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "执行数学计算"

    async def execute(self, expression: str) -> str:
        """安全地执行数学计算"""
        try:
            # 只允许安全的字符
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return "错误：表达式包含非法字符"

            result = eval(expression)
            return f"{expression} = {result}"
        except Exception as e:
            return f"计算错误：{str(e)}"


class WeatherTool(Tool):
    """天气查询工具"""

    @property
    def name(self) -> str:
        return "weather"

    @property
    def description(self) -> str:
        return "查询天气信息"

    async def execute(self, location: str) -> str:
        """模拟天气查询"""
        # 这里可以集成实际的天气API
        logger.info(f"查询天气: {location}")
        return f"{location}今天的天气：晴，温度25°C，湿度60%，风速5km/h"


class OllamaClient:
    """Ollama API客户端"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)

    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        """生成回复"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama API错误: {e}")
            return f"抱歉，我遇到了一个错误：{str(e)}"

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


class Agent:
    """智能体主类"""

    def __init__(self, model: str = "llama2"):
        self.ollama = OllamaClient(model=model)
        self.memory = MemorySystem()
        self.tools: Dict[str, Tool] = {
            "web_search": WebSearchTool(),
            "calculator": CalculatorTool(),
            "weather": WeatherTool()
        }
        self.system_prompt = """你是一个功能强大的AI助手，具有以下工具可以使用：
1. web_search: 搜索互联网信息
2. calculator: 执行数学计算  
3. weather: 查询天气信息

当用户提出需要工具辅助的问题时，请分析需求并选择合适的工具。
回复格式：
- 对于工具调用：使用【工具调用】标记，后跟工具名称和参数
- 对于普通回复：直接回复用户

示例：
用户：北京天气如何？
助手：【工具调用】weather:{"location": "北京"}
收到工具结果后，用自然语言回复用户。

用户：1+1等于几？
助手：【工具调用】calculator:{"expression": "1+1"}
收到结果后回复用户计算结果。

记住要保持对话的连贯性和友好性。"""

    async def process_message(self, session_id: str, user_input: str) -> str:
        """处理用户消息"""
        # 存储用户消息
        user_message = Message(role="user", content=user_input)
        self.memory.store_message(session_id, user_message)

        # 获取对话上下文
        context = self.memory.get_recent_context(session_id, limit=5)

        # 构建提示
        context_str = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in context[:-1]  # 排除当前消息
        ])

        full_prompt = f"""{self.system_prompt}

对话历史：
{context_str}

用户：{user_input}
助手："""

        # 生成回复
        response = await self.ollama.generate(full_prompt)

        # 检查是否需要工具调用
        if "【工具调用】" in response:
            tool_call_part = response.split("【工具调用】")[1].strip()
            tool_name, tool_args = self._parse_tool_call(tool_call_part)

            if tool_name in self.tools:
                # 执行工具
                tool_result = await self._execute_tool(tool_name, tool_args)

                # 存储工具调用和结果
                tool_message = Message(
                    role="assistant",
                    content=f"使用工具: {tool_name}",
                    metadata={"tool": tool_name, "args": tool_args}
                )
                self.memory.store_message(session_id, tool_message)

                result_message = Message(
                    role="tool",
                    content=str(tool_result),
                    metadata={"tool_result": True}
                )
                self.memory.store_message(session_id, result_message)

                # 基于工具结果生成最终回复
                final_prompt = f"""基于工具结果生成自然语言回复：

工具：{tool_name}
参数：{tool_args}
结果：{tool_result}

请用友好的方式回复用户的问题。"""

                final_response = await self.ollama.generate(final_prompt)
                response = final_response

        # 存储助手回复
        assistant_message = Message(role="assistant", content=response)
        self.memory.store_message(session_id, assistant_message)

        return response

    def _parse_tool_call(self, tool_call_str: str) -> tuple:
        """解析工具调用字符串"""
        try:
            parts = tool_call_str.split(":", 1)
            tool_name = parts[0].strip()
            if len(parts) > 1:
                tool_args = json.loads(parts[1].strip())
            else:
                tool_args = {}
            return tool_name, tool_args
        except:
            return tool_call_str, {}

    async def _execute_tool(self, tool_name: str, tool_args: Dict) -> Any:
        """执行工具"""
        try:
            tool = self.tools.get(tool_name)
            if tool:
                return await tool.execute(**tool_args)
            else:
                return f"未知工具: {tool_name}"
        except Exception as e:
            return f"工具执行错误: {str(e)}"

    async def close(self):
        """关闭资源"""
        await self.ollama.close()


# 使用示例和测试
async def main():
    """主函数 - 演示智能体功能"""

    # 创建智能体
    agent = Agent(model="llama2")

    print("🤖 Ollama智能体已启动！")
    print("支持的命令：")
    print("- 搜索 [关键词] - 搜索信息")
    print("- 计算 [表达式] - 数学计算")
    print("- 天气 [地点] - 查询天气")
    print("- 退出 - 结束对话")
    print("-" * 50)

    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        while True:
            user_input = input("\n👤 您：").strip()

            if user_input.lower() in ["退出", "exit", "quit"]:
                print("🤖 智能体：再见！感谢您的使用。")
                break

            if not user_input:
                print("continue")
                continue

            print("🤖 智能体：思考中...")
            print(f"用户输入为：{user_input}")


    finally:
        print("智能体已关闭")




if __name__ == "__main__":
    # 运行测试
    # asyncio.run(test_tools())

    # 运行主程序
    asyncio.run(main())