from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Interface.Utils.config import Config
import traceback


excuter_router = APIRouter(prefix="/excuter", tags=["工具执行中心"])


# ---------- 2. 调用接口 ----------
class CallIn(BaseModel):
    func: str           # 函数名称
    params: dict = {}   # 函数的参数


@excuter_router.post("/call")
def call(body: CallIn):
    if body.func not in Config.register_funObject:
        raise HTTPException(400, "函数未注册")
    try:
        result = Config.register_funObject[body.func](**body.params)
        return {"result": result}
    except Exception as e:
        raise HTTPException(500, f"调用失败: {traceback.format_exc()}")