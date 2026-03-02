from sqlalchemy.orm import Session
from app.models.professor_model import Professor
from app.schemas.professor_schema import ProfessorCreate

class ProfessorRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, professor: ProfessorCreate):
        db_professor = Professor(
            nome=professor.nome,
            email=professor.email
        )
        self.db.add(db_professor)
        self.db.commit()
        self.db.refresh(db_professor)
        return db_professor

    def list_all(self):
        return self.db.query(Professor).all()

    def get_by_id(self, professor_id: int):
        return self.db.query(Professor).filter(Professor.id == professor_id).first()

    def get_by_email(self, email: str):
        return self.db.query(Professor).filter(Professor.email == email).first()

    def update(self, professor_id: int, professor: ProfessorCreate):
        db_professor = self.get_by_id(professor_id)
        if db_professor:
            db_professor.nome = professor.nome
            db_professor.email = professor.email
            self.db.commit()
            self.db.refresh(db_professor)
        return db_professor

    def delete(self, professor_id: int):
        db_professor = self.get_by_id(professor_id)
        if db_professor:
            self.db.delete(db_professor)
            self.db.commit()
        return db_professor
