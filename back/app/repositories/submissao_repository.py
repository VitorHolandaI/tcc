from sqlalchemy.orm import Session
from app.models.submissao_model import Submissao
from app.models.aluno_model import Aluno
from app.schemas.submissao_schema import SubmissaoCreate
from datetime import datetime
from datetime import datetime
from zoneinfo import ZoneInfo

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


class SubmissaoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, submissao_id: int):
        return self.db.query(Submissao).filter(Submissao.id == submissao_id).first()

    def get_by_aluno_and_questao(self, aluno_id: int, questao_id: int):
        return self.db.query(Submissao).filter(
            Submissao.aluno_id == aluno_id,
            Submissao.questao_id == questao_id
        ).first()

    def get_all_by_aluno_id(self, aluno_id: int):
        return self.db.query(Submissao).filter(Submissao.aluno_id == aluno_id).all()

    def are_submissions_finalized(self, aluno_id: int, prova_id: int) -> bool:
        return self.db.query(Submissao).filter(
            Submissao.aluno_id == aluno_id,
            Submissao.prova_id == prova_id,
            Submissao.finalizada == True
        ).first() is not None

    def create_or_update(self, submissao_data: SubmissaoCreate, aluno_id: int, finalizada: bool = False):
        """
        Cria uma nova submissão ou atualiza uma existente.
        A constraint no model garante que a combinação de aluno_id e questao_id é única.
        """
        
        db_submissao = self.get_by_aluno_and_questao(aluno_id=aluno_id, questao_id=submissao_data.questao_id)

        if db_submissao:
            db_submissao.codigo_submetido = submissao_data.codigo_submetido
            db_submissao.data_envio = datetime.now(SAO_PAULO_TZ)
            db_submissao.finalizada = finalizada
            # db_submissao.resultado_execucao = None 
        else:
            db_submissao = Submissao(
                aluno_id=aluno_id,
                prova_id=submissao_data.prova_id,
                questao_id=submissao_data.questao_id,
                codigo_submetido=submissao_data.codigo_submetido,
                data_envio=datetime.now(SAO_PAULO_TZ),
                finalizada=finalizada
            )
            self.db.add(db_submissao)
        
        self.db.commit()
        self.db.refresh(db_submissao)
        return db_submissao
