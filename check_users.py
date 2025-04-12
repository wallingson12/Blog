import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from sqlalchemy import create_engine, inspect, text
import pandas as pd

# Configuração do banco de dados
DATABASE_URL = 'postgresql://postgres.cfhkuvuqyzjqizkqqpwm:85082518@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

schema = 'public'
tabela = 'usuario'


def excluir_usuario(user_id):
    try:
        with engine.begin() as conn:
            query_verificar = text(f'SELECT 1 FROM "{schema}"."{tabela}" WHERE id = :id LIMIT 1')
            result = conn.execute(query_verificar, {'id': user_id}).fetchone()

            if result:
                conn.execute(text(f'DELETE FROM "{schema}"."like" WHERE usuario_id = :id'), {'id': user_id})
                conn.execute(text(f'DELETE FROM "{schema}"."comentario" WHERE usuario_id = :id'), {'id': user_id})
                conn.execute(text(f'DELETE FROM "{schema}"."post" WHERE usuario_id = :id'), {'id': user_id})
                conn.execute(text(f'DELETE FROM "{schema}"."amizades" WHERE solicitante_id = :id OR solicitado_id = :id'), {'id': user_id})
                conn.execute(text(f'DELETE FROM "{schema}"."{tabela}" WHERE id = :id'), {'id': user_id})
                messagebox.showinfo("Sucesso", f"Usuário com ID {user_id} foi excluído com sucesso.")
            else:
                messagebox.showerror("Erro", f"Usuário com ID {user_id} não encontrado.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao excluir o usuário: {e}")


def excluir_coluna(nome_coluna, nome_tabela):
    try:
        colunas_tabela = inspector.get_columns(nome_tabela, schema=schema)
        nomes_colunas = [col['name'] for col in colunas_tabela]

        if nome_coluna not in nomes_colunas:
            messagebox.showerror("Erro", f"A coluna '{nome_coluna}' não existe na tabela '{nome_tabela}'.")
            return

        with engine.begin() as conn:
            drop_query = text(f'ALTER TABLE "{schema}"."{nome_tabela}" DROP COLUMN "{nome_coluna}"')
            conn.execute(drop_query)
            messagebox.showinfo("Sucesso", f"Coluna '{nome_coluna}' foi excluída da tabela '{nome_tabela}'.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao excluir coluna: {e}")


def excluir_post(post_id):
    try:
        with engine.begin() as conn:
            query_verificar = text(f'SELECT 1 FROM "{schema}"."post" WHERE id = :id LIMIT 1')
            result = conn.execute(query_verificar, {'id': post_id}).fetchone()

            if result:
                conn.execute(text(f'DELETE FROM "{schema}"."post" WHERE id = :id'), {'id': post_id})
                messagebox.showinfo("Sucesso", f"Post com ID {post_id} foi excluído com sucesso.")
            else:
                messagebox.showerror("Erro", f"Post com ID {post_id} não encontrado.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao excluir o post: {e}")


def zerar_tabela(nome_tabela):
    try:
        with engine.begin() as conn:
            delete_query = text(f'DELETE FROM "{schema}"."{nome_tabela}"')
            conn.execute(delete_query)
            messagebox.showinfo("Sucesso", f"Todos os dados da tabela '{nome_tabela}' foram excluídos com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao zerar a tabela '{nome_tabela}': {e}")


def iniciar_interface():
    root = tk.Tk()
    root.title("Administração de Banco de Dados")
    root.geometry("800x600")

    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    aba_usuarios = ttk.Frame(notebook)
    aba_colunas = ttk.Frame(notebook)
    aba_post = ttk.Frame(notebook)
    aba_zerar = ttk.Frame(notebook)
    aba_visualizar = ttk.Frame(notebook)

    notebook.add(aba_usuarios, text="Usuários")
    notebook.add(aba_colunas, text="Colunas")
    notebook.add(aba_post, text="Posts")
    notebook.add(aba_zerar, text="Zerar Tabela")
    notebook.add(aba_visualizar, text="Visualizar Tabela")

    # Aba Usuários
    tk.Label(aba_usuarios, text="ID do usuário para excluir:").pack(pady=5)
    entry_user_id = tk.Entry(aba_usuarios, width=30)
    entry_user_id.pack(pady=5)
    tk.Button(aba_usuarios, text="Excluir Usuário", command=lambda: excluir_usuario_action(entry_user_id)).pack(pady=5)

    def excluir_usuario_action(entry_user_id):
        user_id = entry_user_id.get().strip()
        if user_id.isdigit():
            excluir_usuario(int(user_id))
        else:
            messagebox.showerror("Erro", "O ID fornecido não é válido.")

    # Aba Colunas
    tk.Label(aba_colunas, text="Nome da coluna para excluir:").pack(pady=5)
    entry_nome_coluna = tk.Entry(aba_colunas, width=30)
    entry_nome_coluna.pack(pady=5)

    tk.Label(aba_colunas, text="Nome da tabela:").pack(pady=5)
    entry_nome_tabela_coluna = tk.Entry(aba_colunas, width=30)
    entry_nome_tabela_coluna.pack(pady=5)

    tk.Button(aba_colunas, text="Excluir Coluna", command=lambda: excluir_coluna_action(entry_nome_coluna, entry_nome_tabela_coluna)).pack(pady=5)

    def excluir_coluna_action(entry_nome_coluna, entry_nome_tabela_coluna):
        nome_coluna = entry_nome_coluna.get().strip()
        nome_tabela = entry_nome_tabela_coluna.get().strip()
        if nome_coluna and nome_tabela:
            excluir_coluna(nome_coluna, nome_tabela)
        else:
            messagebox.showerror("Erro", "Os campos não podem estar vazios.")

    # Aba Posts
    tk.Label(aba_post, text="ID do post para excluir:").pack(pady=5)
    entry_post_id = tk.Entry(aba_post, width=30)
    entry_post_id.pack(pady=5)
    tk.Button(aba_post, text="Excluir Post", command=lambda: excluir_post_action(entry_post_id)).pack(pady=5)

    def excluir_post_action(entry_post_id):
        post_id = entry_post_id.get().strip()
        if post_id.isdigit():
            excluir_post(int(post_id))
        else:
            messagebox.showerror("Erro", "O ID fornecido não é válido.")

    # Aba Zerar
    tk.Label(aba_zerar, text="Nome da tabela para zerar:").pack(pady=5)
    entry_nome_tabela_zerar = tk.Entry(aba_zerar, width=30)
    entry_nome_tabela_zerar.pack(pady=5)
    tk.Button(aba_zerar, text="Zerar Tabela", command=lambda: zerar_tabela_action(entry_nome_tabela_zerar)).pack(pady=10)

    def zerar_tabela_action(entry_nome_tabela_zerar):
        nome_tabela = entry_nome_tabela_zerar.get().strip()
        if nome_tabela:
            zerar_tabela(nome_tabela)
        else:
            messagebox.showerror("Erro", "O nome da tabela não pode estar vazio.")

    # Aba Visualizar
    tk.Label(aba_visualizar, text="Escolha a tabela para visualizar:").pack(pady=5)
    tabelas = inspector.get_table_names(schema=schema)
    combo_tabela = ttk.Combobox(aba_visualizar, values=tabelas, width=40)
    combo_tabela.pack(pady=5)

    # Treeview
    treeview = ttk.Treeview(aba_visualizar, show="headings")
    treeview.pack(pady=10, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(aba_visualizar, orient="vertical", command=treeview.yview)
    treeview.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    def visualizar_tabela_action():
        nome_tabela = combo_tabela.get().strip()
        if nome_tabela:
            try:
                query = f'SELECT * FROM "{schema}"."{nome_tabela}"'
                df = pd.read_sql(query, engine)

                # Limpar antigo
                treeview.delete(*treeview.get_children())
                treeview["columns"] = list(df.columns)

                for col in df.columns:
                    treeview.heading(col, text=col)
                    treeview.column(col, anchor="center", width=100)

                for _, row in df.iterrows():
                    treeview.insert("", "end", values=list(row))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar dados da tabela '{nome_tabela}': {e}")
        else:
            messagebox.showerror("Erro", "Selecione uma tabela para visualizar.")

    tk.Button(aba_visualizar, text="Visualizar Tabela", command=visualizar_tabela_action).pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    iniciar_interface()
