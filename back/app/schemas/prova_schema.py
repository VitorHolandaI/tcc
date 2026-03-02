from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from app.core.enums import LinguagemEnum
from app.schemas.avaliacao_schema import AvaliacaoResponse

class ProvaBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    data_aplicacao: str
    data_fim: str
    professor_id: int
    linguagem: LinguagemEnum
    emails_permitidos: Optional[List[str]] = []  # Lista de emails de alunos permitidos
    max_saidas: int = 3  # Número máximo de saídas permitidas (padrão: 3)

class ProvaCreate(ProvaBase):
    pass

class ProvaResponse(ProvaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ProvaComResultadosResponse(ProvaResponse):
    avaliacoes: List[AvaliacaoResponse]
