from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Interface.Utils.config import Config
import traceback

register_router = APIRouter(prefix="/register", tags=["工具注册中心"])


class RegisterIn(BaseModel):
    func_name: str      # 函数名
    func_info: str      # 函数信息
    func_code: str      # 函数完整源码


@register_router.post("/func")
def register(body: RegisterIn):
    """
    把任意 Python 函数注册到服务里。
    源码里必须定义一个同名函数，否则会报错。
    """
    try:
        # 执行源码，产生局部命名空间
        loc: dict = {}
        exec(body.func_code, globals(), loc)

        if body.func_name not in loc:
            raise ValueError(f"源码中找不到函数 {body.func_name}")

        Config.register_funObject[body.func_name] = loc[body.func_name]
        Config.register_funDoc[body.func_name] = body.func_info

        return {"msg": f"函数 {body.func_name} 已注册"}
    except Exception as e:
        raise HTTPException(500, f"注册失败: {traceback.format_exc()}")