from functools import wraps
from Utils.config import Config
import inspect


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