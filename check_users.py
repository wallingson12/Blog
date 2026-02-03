import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from sqlalchemy import create_engine, inspect, text
import pandas as pd

# Configuração do banco de dados
database_url = 'postgresql://postgres:?G#Gka8$#nR&r6f@db.korkljglbctkdtjaszxz.supabase.co:5432/postgres'
engine = create_engine(database_url)
schema = 'public'

# Funções de operação no banco
def excluir_usuario(user_id):
    try:
        with engine.begin() as conn:
            sql = text(f'SELECT 1 FROM "{schema}"."usuario" WHERE id = :id LIMIT 1')
            exists = conn.execute(sql, {'id': user_id}).scalar()
            if not exists:
                messagebox.showerror("Erro", f"Usuário com ID {user_id} não encontrado.")
                return
            for tabela in ['like', 'comentario', 'post']:
                conn.execute(text(f'DELETE FROM "{schema}"."{tabela}" WHERE usuario_id = :id'), {'id': user_id})
            conn.execute(
                text(f'DELETE FROM "{schema}"."amizades" WHERE solicitante_id = :id OR solicitado_id = :id'),
                {'id': user_id}
            )
            conn.execute(text(f'DELETE FROM "{schema}"."usuario" WHERE id = :id'), {'id': user_id})
        messagebox.showinfo("Sucesso", f"Usuário {user_id} excluído com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro ao excluir usuário", str(e))


def excluir_coluna(nome_coluna, nome_tabela):
    try:
        insp = inspect(engine)
        cols = [c['name'] for c in insp.get_columns(nome_tabela, schema=schema)]
        if nome_coluna not in cols:
            messagebox.showerror("Erro", f"Coluna '{nome_coluna}' não existe em '{nome_tabela}'")
            return
        with engine.begin() as conn:
            conn.execute(text(f'ALTER TABLE "{schema}"."{nome_tabela}" DROP COLUMN "{nome_coluna}"'))
        messagebox.showinfo("Sucesso", f"Coluna '{nome_coluna}' excluída de '{nome_tabela}'.")
    except Exception as e:
        messagebox.showerror("Erro ao excluir coluna", str(e))


def excluir_post(post_id):
    try:
        with engine.begin() as conn:
            sql = text(f'SELECT 1 FROM "{schema}"."post" WHERE id = :id LIMIT 1')
            exists = conn.execute(sql, {'id': post_id}).scalar()
            if not exists:
                messagebox.showerror("Erro", f"Post {post_id} não encontrado.")
                return
            conn.execute(text(f'DELETE FROM "{schema}"."post" WHERE id = :id'), {'id': post_id})
        messagebox.showinfo("Sucesso", f"Post {post_id} excluído com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro ao excluir post", str(e))


def zerar_tabela(nome_tabela):
    try:
        with engine.begin() as conn:
            conn.execute(text(f'DELETE FROM "{schema}"."{nome_tabela}"'))
        messagebox.showinfo("Sucesso", f"Tabela '{nome_tabela}' zerada com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro ao zerar tabela", str(e))


def adicionar_coluna(nome_coluna, tipo_coluna, nome_tabela):
    try:
        insp = inspect(engine)
        cols = [c['name'] for c in insp.get_columns(nome_tabela, schema=schema)]
        if nome_coluna in cols:
            messagebox.showerror("Erro", f"Coluna '{nome_coluna}' já existe em '{nome_tabela}'")
            return
        with engine.begin() as conn:
            conn.execute(text(f'ALTER TABLE "{schema}"."{nome_tabela}" ADD COLUMN "{nome_coluna}" {tipo_coluna}'))
        messagebox.showinfo("Sucesso", f"Coluna '{nome_coluna}' adicionada em '{nome_tabela}'.")
    except Exception as e:
        messagebox.showerror("Erro ao adicionar coluna", str(e))


def adicionar_tabela(nome_tabela, colunas_definidas):
    # Validação básica das colunas definidas
    defs = [c.strip() for c in colunas_definidas.split(',') if c.strip()]
    for c in defs:
        if ' ' not in c:
            raise ValueError(f"Definição inválida: '{c}'. Use formato 'nome tipo', ex: id VARCHAR(255)")
    create_sql = f'CREATE TABLE "{schema}"."{nome_tabela}" ({colunas_definidas});'
    with engine.begin() as conn:
        conn.execute(text(create_sql))


def excluir_tabela(nome_tabela):
    try:
        with engine.begin() as conn:
            # Verifica se a tabela existe
            sql = text(f'SELECT 1 FROM information_schema.tables WHERE table_name = :table_name AND table_schema = :schema')
            exists = conn.execute(sql, {'table_name': nome_tabela, 'schema': schema}).scalar()
            if not exists:
                messagebox.showerror("Erro", f"Tabela '{nome_tabela}' não encontrada.")
                return
            # Exclui a tabela
            conn.execute(text(f'DROP TABLE "{schema}"."{nome_tabela}"'))
        messagebox.showinfo("Sucesso", f"Tabela '{nome_tabela}' excluída com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro ao excluir tabela", str(e))


# Funções de ação para o GUI
def visualizar_tabela_action(combo, tree):
    nome = combo.get().strip()
    if not nome:
        messagebox.showerror("Erro", "Selecione uma tabela.")
        return
    try:
        df = pd.read_sql(f'SELECT * FROM "{schema}"."{nome}"', engine)
        tree.delete(*tree.get_children())
        tree["columns"] = list(df.columns)
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=100)
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))
    except Exception as e:
        messagebox.showerror("Erro ao visualizar", str(e))


def adicionar_tabela_action(entry_nome, entry_def, combo):
    nome = entry_nome.get().strip()
    definicao = entry_def.get().strip()
    if not nome or not definicao:
        messagebox.showerror("Erro", "Preencha todos os campos.")
        return
    try:
        adicionar_tabela(nome, definicao)
    except ValueError as ve:
        messagebox.showerror("Erro de definição", str(ve))
        return
    except Exception as e:
        messagebox.showerror("Erro ao criar tabela", str(e))
        return
    # Se chegou aqui, criou com sucesso
    combo.config(values=inspect(engine).get_table_names(schema=schema))
    messagebox.showinfo("Sucesso", f"Tabela '{nome}' criada com sucesso.")

def iniciar_interface():
    root = tk.Tk()
    root.title("Administração de Banco de Dados")
    root.geometry("800x600")

    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Abas
    aba_usuarios = ttk.Frame(notebook)
    aba_colunas = ttk.Frame(notebook)
    aba_post = ttk.Frame(notebook)
    aba_zerar = ttk.Frame(notebook)
    aba_visualizar = ttk.Frame(notebook)
    aba_adicionar_coluna = ttk.Frame(notebook)
    aba_excluir_tabela = ttk.Frame(notebook)
    aba_adicionar_tabela = ttk.Frame(notebook)

    notebook.add(aba_usuarios, text="Usuários")
    notebook.add(aba_colunas, text="Colunas")
    notebook.add(aba_post, text="Posts")
    notebook.add(aba_zerar, text="Zerar Tabela")
    notebook.add(aba_visualizar, text="Visualizar Tabela")
    notebook.add(aba_adicionar_coluna, text="Adicionar Coluna")
    notebook.add(aba_excluir_tabela, text="Excluir Tabela")
    notebook.add(aba_adicionar_tabela, text="Adicionar Tabela")

    # Widgets - Excluir Tabela
    tk.Label(aba_excluir_tabela, text="Nome da tabela para excluir:").pack(pady=5)
    entry_nome_tabela = tk.Entry(aba_excluir_tabela, width=30)
    entry_nome_tabela.pack(pady=5)
    tk.Button(
        aba_excluir_tabela, text="Excluir Tabela",
        command=lambda: excluir_tabela(entry_nome_tabela.get().strip())
    ).pack(pady=5)

    # Widgets - Usuários
    tk.Label(aba_usuarios, text="ID do usuário para excluir:").pack(pady=5)
    entry_user_id = tk.Entry(aba_usuarios, width=30)
    entry_user_id.pack(pady=5)
    tk.Button(
        aba_usuarios, text="Excluir Usuário",
        command=lambda: excluir_usuario(int(entry_user_id.get().strip()))
    ).pack(pady=5)

    # Widgets - Colunas
    tk.Label(aba_colunas, text="Nome da coluna:").pack(pady=5)
    entry_coluna = tk.Entry(aba_colunas, width=30)
    entry_coluna.pack(pady=5)
    tk.Label(aba_colunas, text="Nome da tabela:").pack(pady=5)
    entry_tabela_coluna = tk.Entry(aba_colunas, width=30)
    entry_tabela_coluna.pack(pady=5)
    tk.Button(
        aba_colunas, text="Excluir Coluna",
        command=lambda: excluir_coluna(entry_coluna.get().strip(), entry_tabela_coluna.get().strip())
    ).pack(pady=5)

    # Widgets - Posts
    tk.Label(aba_post, text="ID do post para excluir:").pack(pady=5)
    entry_post_id = tk.Entry(aba_post, width=30)
    entry_post_id.pack(pady=5)
    tk.Button(
        aba_post, text="Excluir Post",
        command=lambda: excluir_post(int(entry_post_id.get().strip()))
    ).pack(pady=5)

    # Widgets - Zerar
    tk.Label(aba_zerar, text="Nome da tabela:").pack(pady=5)
    entry_zerar = tk.Entry(aba_zerar, width=30)
    entry_zerar.pack(pady=5)
    tk.Button(
        aba_zerar, text="Zerar Tabela",
        command=lambda: zerar_tabela(entry_zerar.get().strip())
    ).pack(pady=5)

    # Widgets - Adicionar Coluna
    tk.Label(aba_adicionar_coluna, text="Nome da coluna:").pack(pady=5)
    entry_add_coluna = tk.Entry(aba_adicionar_coluna, width=30)
    entry_add_coluna.pack(pady=5)
    tk.Label(aba_adicionar_coluna, text="Tipo da coluna:").pack(pady=5)
    entry_tipo_coluna = tk.Entry(aba_adicionar_coluna, width=30)
    entry_tipo_coluna.pack(pady=5)
    tk.Label(aba_adicionar_coluna, text="Nome da tabela:").pack(pady=5)
    entry_add_tabela = tk.Entry(aba_adicionar_coluna, width=30)
    entry_add_tabela.pack(pady=5)
    tk.Button(
        aba_adicionar_coluna, text="Adicionar Coluna",
        command=lambda: adicionar_coluna(
            entry_add_coluna.get().strip(),
            entry_tipo_coluna.get().strip(),
            entry_add_tabela.get().strip()
        )
    ).pack(pady=5)

    # Widgets - Visualizar
    tk.Label(aba_visualizar, text="Escolha a tabela:").pack(pady=5)
    combo_tabela = ttk.Combobox(
        aba_visualizar,
        values=inspect(engine).get_table_names(schema=schema),
        width=40
    )
    combo_tabela.pack(pady=5)
    treeview = ttk.Treeview(aba_visualizar, show="headings")
    treeview.pack(pady=10, fill=tk.BOTH, expand=True)
    scrollbar = ttk.Scrollbar(aba_visualizar, orient="vertical", command=treeview.yview)
    treeview.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tk.Button(
        aba_visualizar, text="Visualizar Tabela",
        command=lambda: visualizar_tabela_action(combo_tabela, treeview)
    ).pack(pady=5)

    # Widgets - Adicionar Tabela
    tk.Label(aba_adicionar_tabela, text="Nome da nova tabela:").pack(pady=5)
    entry_nome_nova_tabela = tk.Entry(aba_adicionar_tabela, width=40)
    entry_nome_nova_tabela.pack(pady=5)
    tk.Label(
        aba_adicionar_tabela,
        text="Definição das colunas (ex: id INT, nome VARCHAR(255)):"
    ).pack(pady=5)
    entry_definicao_colunas = tk.Entry(aba_adicionar_tabela, width=60)
    entry_definicao_colunas.pack(pady=5)
    tk.Button(
        aba_adicionar_tabela, text="Criar Tabela",
        command=lambda: adicionar_tabela_action(
            entry_nome_nova_tabela, entry_definicao_colunas, combo_tabela
        )
    ).pack(pady=10)

    root.mainloop()


if __name__ == '__main__':
    iniciar_interface()
