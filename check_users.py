from sqlalchemy import create_engine, inspect, text
import pandas as pd

# Configuração do banco
DATABASE_URL = 'postgresql://postgres.cfhkuvuqyzjqizkqqpwm:85082518@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

schema = 'public'
tabela = 'usuario'


def excluir_usuario(user_id):
    try:
        with engine.begin() as conn:
            # Verifica se o usuário existe
            query_verificar = text(f'SELECT 1 FROM "{schema}"."{tabela}" WHERE id = :id LIMIT 1')
            result = conn.execute(query_verificar, {'id': user_id}).fetchone()

            if result:
                confirm = input(f"Tem certeza que deseja excluir o usuário com ID {user_id}? (s/n): ")
                if confirm.lower() != 's':
                    print("❎ Operação cancelada.")
                    return

                # Excluir likes
                conn.execute(text(f'''
                    DELETE FROM "{schema}"."like" 
                    WHERE usuario_id = :id
                '''), {'id': user_id})

                # Excluir comentários
                conn.execute(text(f'''
                    DELETE FROM "{schema}"."comentario" 
                    WHERE usuario_id = :id
                '''), {'id': user_id})

                # Excluir posts
                conn.execute(text(f'''
                    DELETE FROM "{schema}"."post" 
                    WHERE usuario_id = :id
                '''), {'id': user_id})

                # Excluir amizades
                conn.execute(text(f'''
                    DELETE FROM "{schema}"."amizades" 
                    WHERE solicitante_id = :id OR solicitado_id = :id
                '''), {'id': user_id})

                # Excluir usuário
                conn.execute(text(f'''
                    DELETE FROM "{schema}"."{tabela}" 
                    WHERE id = :id
                '''), {'id': user_id})

                print(f"✅ Usuário com ID {user_id} foi excluído com sucesso.")
            else:
                print(f"❌ Usuário com ID {user_id} não encontrado.")
    except Exception as e:
        print(f"❌ Erro ao excluir o usuário: {e}")


def adicionar_coluna(nome_coluna, tipo_coluna):
    try:
        colunas = inspector.get_columns(tabela, schema=schema)
        nomes_colunas = [col['name'] for col in colunas]

        if nome_coluna in nomes_colunas:
            print(f"⚠️ A coluna '{nome_coluna}' já existe na tabela '{tabela}'.")
            return

        with engine.begin() as conn:
            alter_query = text(f'ALTER TABLE "{schema}"."{tabela}" ADD COLUMN "{nome_coluna}" {tipo_coluna}')
            conn.execute(alter_query)
            print(f"✅ Coluna '{nome_coluna}' ({tipo_coluna}) adicionada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna: {e}")


def excluir_coluna_post(nome_coluna):
    try:
        colunas_post = inspector.get_columns('post', schema=schema)
        nomes_colunas = [col['name'] for col in colunas_post]

        if nome_coluna not in nomes_colunas:
            print(f"❌ A coluna '{nome_coluna}' não existe na tabela 'post'.")
            return

        confirm = input(f"Tem certeza que deseja excluir a coluna '{nome_coluna}' da tabela 'post'? (s/n): ")
        if confirm.lower() != 's':
            print("❎ Operação cancelada.")
            return

        with engine.begin() as conn:
            drop_query = text(f'ALTER TABLE "{schema}"."post" DROP COLUMN "{nome_coluna}"')
            conn.execute(drop_query)
            print(f"✅ Coluna '{nome_coluna}' foi excluída da tabela 'post'.")
    except Exception as e:
        print(f"❌ Erro ao excluir coluna: {e}")


def mostrar_estrutura_do_banco():
    tabelas = inspector.get_table_names(schema=schema)
    print(f"\n📚 Estrutura do banco - Schema: '{schema}'")
    for tbl in tabelas:
        print(f"\n🧾 Tabela: {tbl}")
        try:
            colunas_tbl = inspector.get_columns(tbl, schema=schema)
            for col in colunas_tbl:
                print(f"  - {col['name']} ({col['type']})")
        except Exception as e:
            print(f"❌ Erro ao obter colunas da tabela '{tbl}': {e}")
    return tabelas


def mostrar_dados_da_tabela_usuario():
    try:
        query = f'SELECT * FROM "{schema}"."{tabela}" LIMIT 10'
        df = pd.read_sql(query, engine)
        print("\n📊 Primeiras 10 linhas da tabela 'usuario':")
        print(df)
    except Exception as e:
        print(f"❌ Erro ao carregar dados da tabela 'usuario': {e}")


def menu():
    tabelas = mostrar_estrutura_do_banco()

    if tabela in tabelas:
        mostrar_dados_da_tabela_usuario()

        print("\n📍 Menu de Opções:")
        print("1 - Excluir usuário")
        print("2 - Adicionar coluna à tabela 'usuario'")
        print("3 - Excluir coluna da tabela 'post'")
        print("0 - Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            user_id = input("Digite o ID do usuário que deseja excluir: ")
            if user_id.strip().isdigit():
                excluir_usuario(int(user_id.strip()))
            else:
                print("❌ O ID fornecido não é válido.")
        elif opcao == "2":
            nome_coluna = input("Nome da nova coluna: ").strip()
            tipo_coluna = input("Tipo da nova coluna (ex: VARCHAR(100), INTEGER): ").strip()
            if nome_coluna and tipo_coluna:
                adicionar_coluna(nome_coluna, tipo_coluna)
            else:
                print("❌ Nome e tipo da coluna não podem estar em branco.")
        elif opcao == "3":
            nome_coluna = input("Nome da coluna que deseja excluir da tabela 'post': ").strip()
            if nome_coluna:
                excluir_coluna_post(nome_coluna)
            else:
                print("❌ Nome da coluna não pode estar em branco.")
        elif opcao == "0":
            print("👋 Encerrando...")
        else:
            print("❌ Opção inválida.")
    else:
        print(f"❌ A tabela '{tabela}' não foi encontrada no schema '{schema}'.")


if __name__ == "__main__":
    menu()
