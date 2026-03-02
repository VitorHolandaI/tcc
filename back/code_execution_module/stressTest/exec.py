from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import io
import contextlib
import types
import sys

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Prova(BaseModel):
    name: str
    prova_id: int
    prova_data: str


@app.post("/prova_execute")
async def receive(prova: Prova):
    module_name = "LocalExecuter"
    plugin_module = types.ModuleType(module_name)
    plugin_module.__file__ = "<string>"
    instance = None
    result = None

    try:
        # fresh namespace for each execution
        namespace = {}

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exec(prova.prova_data, namespace)

        result = namespace.get("RESULT", stdout.getvalue())

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Execution Error: {str(e)}"
        )

    finally:
        if module_name in sys.modules:
            del sys.modules[module_name]
        del plugin_module
            #print("Memory released.")

    return {
        "prova_id": prova.prova_id,
        "status": "success",
        "result": result}
