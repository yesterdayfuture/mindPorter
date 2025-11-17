from Core.basicModel import BasicModel
from Utils.config import Config
import re
import ast
import json


class AgentExcuter:
    """
    智能体执行器
    """
    def __init__(self, model: BasicModel, func_doc, func_object):
        """
        初始化智能体
        :param model: 使用的模型
        :param func_doc: 函数介绍
        :param func_object: 函数对象
        """
        self.model = model
        self.func_doc = func_doc
        self.func_object = func_object

    def run(self, inputs):
        """
        模型调用
        :param inputs:
        :return:
        """
        return self.model.invoke(messages=inputs)

    def _prompt(self, inputs, func_results:list = []):
        """
        根据模型的输入、函数信息、函数执行结果，组织新的模型输入
        :param inputs:
        :return:
        """

        # 函数介绍
        func_info = ""
        for v in self.func_doc.values():
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

    def __call__(self, inputs):
        count = 0
        try:
            response = ""
            func_results = []
            while True:
                count += 1

                if count > 10:
                    print(f"达到最大迭代次数 {count} 次")
                    break

                inputs = self._prompt(inputs, func_results)
                response = self.run(inputs)
                print(f"\n\n===================== 第 {count} 轮 结果=======================")
                print(f"模型回复为：{response}")

                status, func_tools = self._getFuncTools(response)

                if not status:
                    print(f"本次模型回复格式不规范...")
                    continue

                if len(func_tools) < 1:
                    print(f"函数调用结束 或 没有可调用函数")
                    break

                first_func_name = func_tools[0].get("func", "unknow")
                first_func_param = func_tools[0].get("params", {})

                if first_func_name == "unknow":
                    print(f"未发现对应函数名称")
                    break
                first_func = self.func_object.get(first_func_name, "unknow")

                if first_func == "unknow":
                    print(f"未发现对应函数")
                    break

                first_func_result = first_func(**first_func_param)
                func_results.append(f"函数 {first_func_name} 的运行结果为 {first_func_result}")

                print(f"函数 {first_func_name} 的运行结果为 {first_func_result}")

            return response
        except Exception as e:
            print(f"出现错误❌：{str(e)}")
            return f"出现错误❌：{str(e)}"