from pydantic import BaseModel
from typing import Optional

class AvaliacaoResponse(BaseModel):
    id: int
    questao_id: int
    aluno_id: int
    codigo_submetido: str
    resultado_execucao: Optional[str] = None
    nota: Optional[float] = None
    data_submissao: Optional[str] = None
    finalizada: bool = False

    model_config = {"from_attributes": True}

class NotaUpdate(BaseModel):
    nota: float
