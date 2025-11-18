from fastapi import FastAPI
import uvicorn
from Interface.Utils.config import Config
from Interface.Router.excuterRouter import excuter_router
from Interface.Router.registerRouter import register_router

app = FastAPI(title="FuncTools 工具中心")

app.include_router(excuter_router)
app.include_router(register_router)

@app.get("/list")
def list_funcs():
    """
    返回已经注册的工具信息
    :return:
    """
    functools = []
    for k,v in Config.register_funDoc.items():
        cur_dict = {
            "func_name": k,
            "func_info": v,
        }
        functools.append(cur_dict)

    return {"funcs": functools}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)