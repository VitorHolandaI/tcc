from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional

class AlunoBase(BaseModel):
    nome: str
    email: EmailStr
    matricula: str

class AlunoCreate(AlunoBase):
    pass

class AlunoResponse(AlunoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
