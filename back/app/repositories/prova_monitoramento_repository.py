from sqlalchemy.orm import Session
from app.models.prova_monitoramento_model import ProvaMonitoramento

class ProvaMonitoramentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_aluno_and_prova(self, aluno_id: int, prova_id: int) -> ProvaMonitoramento | None:
        """Busca registro de monitoramento por aluno e prova"""
        return self.db.query(ProvaMonitoramento).filter(
            ProvaMonitoramento.aluno_id == aluno_id,
            ProvaMonitoramento.prova_id == prova_id
        ).first()

    def create_or_update(self, aluno_id: int, prova_id: int) -> ProvaMonitoramento:
        """Cria ou atualiza registro de monitoramento (incrementa saídas)"""
        monitoramento = self.get_by_aluno_and_prova(aluno_id, prova_id)

        if monitoramento:
            monitoramento.numero_saidas += 1
        else:
            monitoramento = ProvaMonitoramento(
                aluno_id=aluno_id,
                prova_id=prova_id,
                numero_saidas=1,
                invalidada=False
            )
            self.db.add(monitoramento)

        self.db.commit()
        self.db.refresh(monitoramento)
        return monitoramento

    def invalidar_prova(self, aluno_id: int, prova_id: int) -> ProvaMonitoramento:
        """Marca a prova como invalidada"""
        monitoramento = self.get_by_aluno_and_prova(aluno_id, prova_id)

        if not monitoramento:
            monitoramento = ProvaMonitoramento(
                aluno_id=aluno_id,
                prova_id=prova_id,
                numero_saidas=0,
                invalidada=True
            )
            self.db.add(monitoramento)
        else:
            monitoramento.invalidada = True

        self.db.commit()
        self.db.refresh(monitoramento)
        return monitoramento

    def is_prova_invalidada(self, aluno_id: int, prova_id: int) -> bool:
        """Verifica se a prova está invalidada"""
        monitoramento = self.get_by_aluno_and_prova(aluno_id, prova_id)
        return monitoramento.invalidada if monitoramento else False
