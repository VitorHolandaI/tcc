from pydantic import BaseModel

class Prova(BaseModel):
    name: str
    prova_id: int
    prova_data: str  # This is the python code string


