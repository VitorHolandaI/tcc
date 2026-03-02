from pydantic import BaseModel, ConfigDict
from typing import Optional

class QuestaoBase(BaseModel):
    prova_id: int
    titulo: str
    descricao: str
    exemplo_input1: str
    exemplo_output1: str
    exemplo_input2: Optional[str] = None
    exemplo_output2: Optional[str] = None
    peso: float = 1.0

class QuestaoCreate(QuestaoBase):
    pass

class QuestaoResponse(QuestaoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
