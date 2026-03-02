from sqlalchemy.orm import Session
from app.models.questao_model import Questao
from app.schemas.questao_schema import QuestaoCreate

class QuestaoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, questao: QuestaoCreate):
        db_questao = Questao(
            prova_id=questao.prova_id,
            titulo=questao.titulo,
            descricao=questao.descricao,
            exemplo_input1=questao.exemplo_input1,
            exemplo_output1=questao.exemplo_output1,
            exemplo_input2=questao.exemplo_input2,
            exemplo_output2=questao.exemplo_output2,
            peso=questao.peso
        )
        self.db.add(db_questao)
        self.db.commit()
        self.db.refresh(db_questao)
        return db_questao

    def list_all(self):
        return self.db.query(Questao).all()

    def get_by_id(self, questao_id: int):
        return self.db.query(Questao).filter(Questao.id == questao_id).first()

    def list_by_prova(self, prova_id: int):
        return self.db.query(Questao).filter(Questao.prova_id == prova_id).all()

    def update(self, questao_id: int, questao: QuestaoCreate):
        db_questao = self.get_by_id(questao_id)
        if db_questao:
            db_questao.prova_id = questao.prova_id
            db_questao.titulo = questao.titulo
            db_questao.descricao = questao.descricao
            db_questao.exemplo_input1 = questao.exemplo_input1
            db_questao.exemplo_output1 = questao.exemplo_output1
            db_questao.exemplo_input2 = questao.exemplo_input2
            db_questao.exemplo_output2 = questao.exemplo_output2
            db_questao.peso = questao.peso
            self.db.commit()
            self.db.refresh(db_questao)
        return db_questao

    def delete(self, questao_id: int):
        db_questao = self.get_by_id(questao_id)
        if db_questao:
            self.db.delete(db_questao)
            self.db.commit()
        return db_questao
