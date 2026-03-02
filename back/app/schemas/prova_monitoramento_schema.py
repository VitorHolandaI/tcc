from pydantic import BaseModel, ConfigDict

class ProvaMonitoramentoBase(BaseModel):
    aluno_id: int
    prova_id: int
    numero_saidas: int
    invalidada: bool

class ProvaMonitoramentoResponse(ProvaMonitoramentoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
