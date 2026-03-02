from fastapi import FastAPI, Request
from pydantic import BaseModel
from models.models import Prova
from fastapi.middleware.cors import CORSMiddleware
import subprocess

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Prova(BaseModel):
    name: str
    prova_id: int
    prova_data: str  # This is the python code string


def file_writer(lines):
    with open("../test.py", "w", encoding="utf-8") as f:
        f.writelines(lines)


def file_execute():
    result = subprocess.run(["python3", "../test.py"],
                            capture_output=True, text=True)
    final_result = (
        f"result was: {result.stdout} {result.stderr}")
    return final_result


@app.post("/prova_execute")
async def receive(prova: Prova):
    list_program = prova.prova_data
    print(list_program)
    file_writer(list_program)
    result_execution = file_execute()
    print(result_execution)
    formated = (f"the code run results in the value {result_execution}")

    return {
        "prova_id": prova.prova_id,
        "status": "success",
        "result": formated
        }
