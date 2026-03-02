from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional

class ProfessorBase(BaseModel):
    nome: str
    email: EmailStr

class ProfessorCreate(ProfessorBase):
    pass

class ProfessorResponse(ProfessorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
