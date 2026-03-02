from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class SubmissaoBase(BaseModel):
    prova_id: int
    questao_id: int
    codigo_submetido: str

class SubmissaoCreate(SubmissaoBase):
    pass

class SubmissaoUpdate(BaseModel):
    codigo_submetido: str

class SubmissaoResponse(SubmissaoBase):
    id: int
    aluno_id: int
    data_envio: datetime
    resultado_execucao: Optional[str] = None
    finalizada: bool
    nota: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
