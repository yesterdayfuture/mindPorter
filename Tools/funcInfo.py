from functools import wraps
from Utils.config import Config
import inspect
import requests
import re


class FuncInfo:
    """
    通过此类的方法 将函数注册到全局配置中，为进行函数调用提供函数信息
    """

    def get_funcDoc(self, func):

        # 函数名称
        func_name = func.__name__
        # 函数描述
        func_doc = inspect.getdoc(func).strip()
        # 函数参数
        sig = inspect.signature(func)
        params = []
        required_params = []
        for p_name, p_info in sig.parameters.items():
            if p_info.default is inspect.Parameter.empty:
                required_params.append(p_name)

            param_type = str(p_info.annotation) if p_info.annotation != inspect.Parameter.empty else "Any"
            required = "是" if p_name in required_params else "否"
            default = p_info.default if p_info.default != inspect.Parameter.empty else None

            params.append(f"参数为 {p_name},类型为 {param_type},是否必须: {required},默认值为 {default}")

        Config.register_funDoc[func_name] = f"函数 {func_name} 的作用为 {func_doc}," + ";".join(params)
        Config.register_funObject[func_name] = func

        return func

    def source_without_decorators(self, func_code):
        """
        根据 func 的源码，把顶部的 @decorator 行全部删掉。
        返回 str，带换行符，与 inspect.getsource 格式一致。
        """
        # 1. 找到 def 所在行号（0-based）
        def_line_idx = next(i for i, line in enumerate(func_code.splitlines())
                            if re.match(r'\s*def\s+', line))
        # 2. 截取 def 行及其之后的内容
        return '\n'.join(func_code.splitlines()[def_line_idx:]) + '\n'

    def remote_register(self, url, require_type = "post"):
        """
        本函数是一个装饰器，将本地函数注册到远程服务中，在远程服务中调用本地函数
        :param url:
        :param require_type:
        :return:
        """
        def get_local_func(func):
            # 函数名称
            func_name = func.__name__
            # 函数描述
            func_doc = inspect.getdoc(func).strip()
            # 函数参数
            sig = inspect.signature(func)
            params = []
            required_params = []
            for p_name, p_info in sig.parameters.items():
                if p_info.default is inspect.Parameter.empty:
                    required_params.append(p_name)

                param_type = str(p_info.annotation) if p_info.annotation != inspect.Parameter.empty else "Any"
                required = "是" if p_name in required_params else "否"
                default = p_info.default if p_info.default != inspect.Parameter.empty else None

                params.append(f"参数为 {p_name},类型为 {param_type},是否必须: {required},默认值为 {default}")

            func_info = f"函数 {func_name} 的作用为 {func_doc}," + ";".join(params)
            func_code = self.source_without_decorators(inspect.getsource(func))

            if require_type == "post":
                response = requests.post(url=url, json={
                    "func_name": func_name,
                    "func_code": func_code,
                    # "func_info": func_info,
                })
                if response.status_code == 200:
                    print(f"本地函数 {func_name} 远程注册成功")
                else:
                    print(f"本地函数 {func_name} 远程注册失败")

            return func
        return get_local_func
