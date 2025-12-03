from Core.basicModel import BasicModel
from Utils.config import Config
import re
import ast
import json
import requests
from Utils.Messages.messageStorage.messageToSqlite import MemorySystem, Message


class AgentRemoteExcuter:
    """
    智能体执行器,使用服务端工具
    """

    def __init__(self, model: BasicModel, func_doc, url, iter_num=10, message_store: MemorySystem = None):
        """
        初始化智能体
        :param model: 使用的模型
        :param func_doc: 函数介绍
        :param url: 远程函数服务注册调用中心
        :param iter_num: 工具中间调用失败时，最大迭代次数
        :param message_store: 消息持久化存储配置
        """
        self.model = model
        self.func_doc = func_doc
        self.url = url
        self.iter_num = iter_num
        self.message_store = message_store or MemorySystem()

    def run(self, inputs):
        """
        模型调用
        :param inputs:
        :return:
        """
        return self.model.invoke(messages=inputs)

    def _prompt(self, inputs, func_results: list = []):
        """
        根据模型的输入、函数信息、函数执行结果，组织新的模型输入
        :param inputs:
        :return:
        """

        # 函数介绍
        func_info = ""
        for item in self.func_doc:
            v = item.get("func_info")
            func_info += v + "。"

        new_inputs = (Config.default_prompt +
                      Config.few_shot +
                      f"\n函数信息：{func_info}" +
                      f"\n用户输入：{inputs}")
        if len(func_results) > 0:
            new_inputs += f"\n已执行的函数结果为：{';'.join(func_results)}"

        return new_inputs

    def _getFuncTools(self, inputs):
        parse = re.compile(r"<functools>(.*?)</functools>", flags=re.S)
        try:
            m = parse.findall(inputs)  # 只取第一处
            if not m:
                return True, []  # 无标签就返回空列表

            json_str = m[0]

            if json_str == "":
                return True, []

            try:
                obj = json.loads(json_str)  # JSON 解析，支持 null/true/false
            except json.JSONDecodeError as e:
                print(f'❌ JSON 解析失败：{e}')
                return False, []

            # 统一成 list
            if isinstance(obj, dict):
                obj = [obj]
            if not isinstance(obj, list):
                print('❌ <functools> 内容必须是 dict 或 list[dict]')
                return False, []

            return True, obj
        except Exception as e:
            print(f"出现错误❌：{str(e)}")
            return False, []

    def __call__(self, session_id: str, inputs: str):
        """
        智能体执行入口
        :param session_id: 用户对话唯一标识
        :param inputs: 用户输入
        :return:
        """
        count = 0
        try:
            response = ""
            func_results = []
            while True:
                count += 1

                if count > self.iter_num:
                    print(f"达到最大迭代次数 {count} 次")
                    break

                inputs = self._prompt(inputs, func_results)

                # 消息存储
                user_message = Message(role="user", content=inputs)
                self.message_store.store_message(session_id, user_message)

                # 获取对话上下文
                context = self.message_store.get_recent_context(session_id, limit=5)

                # 构建提示
                context_str = "\n".join([
                    f"{msg.role}: {msg.content}"
                    for msg in context[:-1]  # 排除当前消息
                ])

                full_inputs = f"""
                对话历史：
                {context_str}
                用户：{inputs}
                助手："""

                # 执行 大模型
                response = self.run(full_inputs)
                print(f"\n\n===================== 第 {count} 轮 结果=======================")
                print(f"模型回复为：{response}")

                status, func_tools = self._getFuncTools(response)

                if not status:
                    print(f"本次模型回复格式不规范...")
                    continue

                if len(func_tools) < 1:
                    print(f"函数调用结束 或 没有可调用函数")
                    break

                first_func_name = func_tools[0].get("func")
                remote_url_response = requests.post(url=self.url, json=func_tools[0])
                remote_url_response.raise_for_status()  # 不是 2xx 会报异常

                response_json = remote_url_response.json()

                func_results.append(f"函数 {first_func_name} 的运行结果为 {response_json['result']}")

                print(f"函数 {first_func_name} 的运行结果为 {response_json['result']}")

                # 存储工具调用和结果
                tool_message = Message(
                    role="assistant",
                    content=response,
                    metadata={"tool": first_func_name, "args": func_tools[0].get("params", {})}
                )
                self.message_store.store_message(session_id, tool_message)

                result_message = Message(
                    role="tool",
                    content=f"函数 {first_func_name} 调用结果为: {response_json['result']}",
                    metadata={"tool": first_func_name, "args": func_tools[0].get("params", {}), "tool_result": True}
                )
                self.message_store.store_message(session_id, result_message)

            return response
        except Exception as e:
            print(f"出现错误❌：{str(e)}")
            return f"出现错误❌：{str(e)}"