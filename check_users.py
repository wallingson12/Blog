from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
# Importando a classe Usuario do seu arquivo models.py
from models import Usuario

# Caminho correto para o SQLite no Windows (use três barras após "sqlite:///")
db_path = r"C:\Users\wallingson.silva\TO DO\Blog\instance\database.db"
engine = create_engine(f"sqlite:///{db_path}")

# Criar uma sessão para interagir com o banco de dados
Session = sessionmaker(bind=engine)
session = Session()

# Inspecionar tabelas no banco de dados
inspector = inspect(engine)
tables = inspector.get_table_names()

if not tables:
    print("O banco de dados está vazio ou não possui tabelas.")
else:
    print("Tabelas encontradas:", tables)

    # Exibir as colunas e dados de cada tabela
    for table in tables:
        print(f"\n🔹 Dados da tabela: {table}")

        # Obter as colunas da tabela
        columns = [column['name'] for column in inspector.get_columns(table)]
        print(f"🔹 Colunas da tabela: {columns}")

        # Exibir os dados da tabela
        df = pd.read_sql(f"SELECT * FROM {table}", engine)
        print(df)


# Função para deletar um usuário
def delete_user_by_name():
    # Solicitar o nome do usuário a ser excluído
    username_to_delete = input("Digite o nome do usuário que deseja excluir: ")

    try:
        # Buscar o usuário pelo nome
        user = session.query(Usuario).filter_by(username=username_to_delete).first()

        if user:
            # Deletar o usuário
            session.delete(user)
            session.commit()
            print(f"Usuário {username_to_delete} foi deletado.")
        else:
            print(f"Usuário com nome '{username_to_delete}' não encontrado.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Ocorreu um erro ao tentar deletar o usuário: {e}")
    finally:
        # Fechar a sessão
        session.close()


# Chamar a função para deletar o usuário
delete_user_by_name()
