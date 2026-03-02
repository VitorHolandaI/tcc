from sqlalchemy.orm import Session
from app.models.aluno_model import Aluno
from app.schemas.aluno_schema import AlunoCreate

class AlunoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, aluno: AlunoCreate):
        db_aluno = Aluno(
            nome=aluno.nome,
            email=aluno.email,
            matricula=aluno.matricula
        )
        self.db.add(db_aluno)
        self.db.commit()
        self.db.refresh(db_aluno)
        return db_aluno

    def list_all(self):
        return self.db.query(Aluno).all()

    def get_by_id(self, aluno_id: int):
        return self.db.query(Aluno).filter(Aluno.id == aluno_id).first()

    def get_by_email(self, email: str):
        return self.db.query(Aluno).filter(Aluno.email == email).first()

    def get_by_matricula(self, matricula: str):
        return self.db.query(Aluno).filter(Aluno.matricula == matricula).first()

    def update(self, aluno_id: int, aluno: AlunoCreate):
        db_aluno = self.get_by_id(aluno_id)
        if db_aluno:
            db_aluno.nome = aluno.nome
            db_aluno.email = aluno.email
            db_aluno.matricula = aluno.matricula
            self.db.commit()
            self.db.refresh(db_aluno)
        return db_aluno

    def delete(self, aluno_id: int):
        db_aluno = self.get_by_id(aluno_id)
        if db_aluno:
            self.db.delete(db_aluno)
            self.db.commit()
        return db_aluno
