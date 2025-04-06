import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import Usuario
from dotenv import load_dotenv
from tabulate import tabulate

# Carregar variáveis do .env
load_dotenv()

def get_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL não encontrada no .env")
    return create_engine(db_url)

def show_usuarios(engine):
    try:
        df = pd.read_sql('SELECT * FROM "usuario"', engine)
        print("\n👥 Lista de Usuários:\n")
        print(tabulate(df, headers='keys', tablefmt='fancy_grid'))
    except Exception as e:
        print(f"❌ Erro ao buscar usuários: {e}")

def delete_user_by_name(session):
    username_to_delete = input("Digite o nome do usuário que deseja excluir: ")

    try:
        user = session.query(Usuario).filter_by(username=username_to_delete).first()
        if user:
            session.delete(user)
            session.commit()
            print(f"✅ Usuário '{username_to_delete}' foi deletado.")
        else:
            print(f"⚠️ Usuário '{username_to_delete}' não encontrado.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"❌ Erro ao deletar usuário: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    show_usuarios(engine)
    delete_user_by_name(session)
