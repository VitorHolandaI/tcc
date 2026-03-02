from sqlalchemy.orm import Session
from app.models.prova_model import Prova
from app.schemas.prova_schema import ProvaCreate

class ProvaRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, prova: ProvaCreate):
        db_prova = Prova(
            titulo=prova.titulo,
            descricao=prova.descricao,
            data_aplicacao=prova.data_aplicacao,
            data_fim=prova.data_fim,
            professor_id=prova.professor_id,
            linguagem=prova.linguagem,
            emails_permitidos=prova.emails_permitidos,
            max_saidas=prova.max_saidas
        )
        self.db.add(db_prova)
        self.db.commit()
        self.db.refresh(db_prova)
        return db_prova

    def list_all(self):
        return self.db.query(Prova).all()

    def get_by_id(self, prova_id: int):
        return self.db.query(Prova).filter(Prova.id == prova_id).first()

    def list_by_professor(self, professor_id: int):
        return self.db.query(Prova).filter(Prova.professor_id == professor_id).all()

    def update(self, prova_id: int, prova: ProvaCreate):
        db_prova = self.get_by_id(prova_id)
        if db_prova:
            db_prova.titulo = prova.titulo
            db_prova.descricao = prova.descricao
            db_prova.data_aplicacao = prova.data_aplicacao
            db_prova.data_fim = prova.data_fim
            db_prova.professor_id = prova.professor_id
            db_prova.linguagem = prova.linguagem
            db_prova.emails_permitidos = prova.emails_permitidos
            db_prova.max_saidas = prova.max_saidas
            self.db.commit()
            self.db.refresh(db_prova)
        return db_prova

    def delete(self, prova_id: int):
        db_prova = self.get_by_id(prova_id)
        if db_prova:
            self.db.delete(db_prova)
            self.db.commit()
        return db_prova
