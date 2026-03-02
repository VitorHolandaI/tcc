import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models.aluno_model import Aluno
from app.models.professor_model import Professor
from app.models.prova_model import Prova
from app.models.questao_model import Questao
from app.core.enums import LinguagemEnum

def seed_database():
    """
    Populates the database with mock data for professors, students, tests, and questions.
    """
    db: Session = SessionLocal()

    try:
        print("Dropping all tables (with CASCADE for foreign keys)...")
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.commit()

        print("Creating all tables...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")

        print("Seeding professors...")
        prof1 = Professor(nome="Dr. Roberto", email="roberto@email.com")
        prof2 = Professor(nome="Dra. Carla", email="carla@email.com")
        db.add_all([prof1, prof2])
        db.commit()
        print(f" - Created professor: {prof1.nome} (ID: {prof1.id})")
        print(f" - Created professor: {prof2.nome} (ID: {prof2.id})")

        print("Seeding students...")
        aluno1 = Aluno(nome="Alice", email="alice@email.com", matricula="2024001")
        aluno2 = Aluno(nome="Beto", email="beto@email.com", matricula="2024002")
        aluno3 = Aluno(nome="Carlos", email="carlos@email.com", matricula="2024003")
        db.add_all([aluno1, aluno2, aluno3])
        db.commit()
        print(f" - Created student: {aluno1.nome} (ID: {aluno1.id})")
        print(f" - Created student: {aluno2.nome} (ID: {aluno2.id})")
        print(f" - Created student: {aluno3.nome} (ID: {aluno3.id})")

        print("Seeding provas...")
        now = datetime.now()
        
        prova_python = Prova(
            titulo="Prova de Algoritmos em Python",
            descricao="Uma prova para avaliar conhecimentos básicos de Python.",
            data_aplicacao=(now - timedelta(days=1)).isoformat(),
            data_fim=(now + timedelta(days=1)).isoformat(),
            professor_id=prof1.id,
            linguagem=LinguagemEnum.python,
            emails_permitidos=[aluno1.email, aluno2.email],
            max_saidas=5
        )

        prova_java = Prova(
            titulo="Desafio de Java",
            descricao="Questões sobre POO e conceitos avançados de Java.",
            data_aplicacao=(now + timedelta(days=5)).isoformat(),
            data_fim=(now + timedelta(days=6)).isoformat(),
            professor_id=prof1.id,
            linguagem=LinguagemEnum.java,
            emails_permitidos=[aluno2.email, aluno3.email],
            max_saidas=3
        )
        db.add_all([prova_python, prova_java])
        db.commit()
        print(f" - Created prova: '{prova_python.titulo}' (ID: {prova_python.id})")
        print(f" - Created prova: '{prova_java.titulo}' (ID: {prova_java.id})")

        print("Seeding questões para a prova de Python...")
        q1_py = Questao(
            prova_id=prova_python.id,
            titulo="Soma de dois números",
            descricao="Escreva uma função `soma(a, b)` que retorne a soma de dois números.",
            exemplo_input1="a=2, b=3",
            exemplo_output1="5",
            peso=0.4
        )
        q2_py = Questao(
            prova_id=prova_python.id,
            titulo="Inverter uma string",
            descricao="Escreva uma função `inverte(s)` que retorne a string invertida.",
            exemplo_input1="s='hello'",
            exemplo_output1="'olleh'",
            peso=0.6
        )
        db.add_all([q1_py, q2_py])
        db.commit()
        print(f" - Created questao: '{q1_py.titulo}' para a prova ID {prova_python.id}")
        print(f" - Created questao: '{q2_py.titulo}' para a prova ID {prova_python.id}")

        print("\n Database seeded successfully!")

    except Exception as e:
        print(f"\n An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
