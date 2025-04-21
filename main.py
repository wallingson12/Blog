from flask import Flask, render_template, redirect, send_from_directory, request, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from models import db, Usuario, Post, Like, Comentario, Amizade, Crush, Conversa, Mensagem
from forms import LoginForm, RegisterForm, PostForm
from permissions import verificar_autor_do_post
from utils import processar_avatar_upload, processar_imagem_post
from sqlalchemy.orm import joinedload
from datetime import datetime
from sqlalchemy import or_, and_

app = Flask(__name__)
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER_AVATARS'] = os.path.join(app.root_path, 'static', 'uploads', 'avatars')
app.config['UPLOAD_FOLDER_POSTS'] = os.path.join(app.root_path, 'static', 'uploads', 'post_images')
ALLOWED_IMAGES = {'png','jpg','jpeg','gif'}

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Você precisa estar logado para acessar esta página."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route("/")
@login_required
def index():
    # pega o número da página da query string (?page=1)
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # faz a paginação ordenando pelo ID (do mais recente para o mais antigo)
    pagination = Post.query \
        .order_by(Post.id.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    posts = pagination.items  # só os posts desta página

    return render_template(
        'index.html',
        posts=posts,
        pagination=pagination,
        user=current_user
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos!', 'danger')
    return render_template('login.html', form=form)

@app.route('/uploads/<folder>/<filename>')
def uploaded_file(folder, filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'uploads', folder), filename)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        avatar_filename = processar_avatar_upload(
            form.avatar.data,
            app.config['UPLOAD_FOLDER_AVATARS'],
            form.gender.data,
            ALLOWED_IMAGES
        )

        # **Faltava isso:**
        hashed_senha = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        novo_usuario = Usuario(
            username=form.username.data,
            password=hashed_senha,
            gender=form.gender.data,
            avatar=avatar_filename,
            age=form.age.data
        )

        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()  # Rollback da transação em caso de erro
            flash(f'Ocorreu um erro: {str(e)}', 'danger')

    return render_template('register.html', title='Register', form=form)


@app.route('/curtir/<int:post_id>', methods=['POST'])
@login_required
def reagir(post_id):
    tipo = request.form.get('tipo')
    post = Post.query.get_or_404(post_id)
    reacao = Like.query.filter_by(usuario_id=current_user.id, post_id=post.id, tipo=tipo).first()

    if reacao:
        db.session.delete(reacao)
    else:
        nova_reacao = Like(usuario_id=current_user.id, post_id=post.id, tipo=tipo)
    try:
        db.session.add(nova_reacao)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()  # Rollback da transação em caso de erro
        flash(f'Ocorreu um erro: {str(e)}', 'danger')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        image_filename = processar_imagem_post(
            form.image.data,
            app.config['UPLOAD_FOLDER_POSTS'],
            ALLOWED_IMAGES
        )

        novo_post = Post(
            conteudo=form.content.data,
            image=image_filename,
            autor=current_user
        )

        try:
            db.session.add(novo_post)
            db.session.commit()
            flash('Post criado com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()  # Rollback da transação em caso de erro
            flash(f'Ocorreu um erro: {str(e)}', 'danger')

    return render_template('new_post.html', form=form)

@app.route('/sobre')
@login_required
def sobre():
    return render_template('sobre.html')


@app.route('/comentar/<int:post_id>', methods=['POST'])
@login_required
def comentar(post_id):
    conteudo = request.form.get('conteudo')
    if conteudo:
        try:
            # Adiciona o comentário à sessão do banco de dados
            db.session.add(Comentario(conteudo=conteudo, usuario_id=current_user.id, post_id=post_id))

            # Tenta realizar o commit
            db.session.commit()
            flash('Comentário adicionado com sucesso!', 'success')
        except Exception as e:
            # Se ocorrer um erro, faz o rollback e mostra uma mensagem de erro
            db.session.rollback()
            flash(f'Ocorreu um erro ao adicionar o comentário: {str(e)}', 'danger')
    else:
        flash('O comentário não pode estar vazio.', 'warning')

    return redirect(url_for('index'))


@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if not verificar_autor_do_post(post):
        return redirect(url_for('index'))
    if post.image:
        path = os.path.join(app.config['UPLOAD_FOLDER_POSTS'], post.image)
        if os.path.exists(path):
            os.remove(path)
    try:
        db.session.delete(post)
        db.session.commit()
        flash('Post excluído com sucesso!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        # Se algum erro ocorrer, desfaz a transação
        db.session.rollback()
        flash(f'Ocorreu um erro ao adicionar o comentário: {str(e)}', 'danger')

@app.route('/perfil')
@login_required
def perfil():
    return redirect(url_for('perfil_usuario', user_id=current_user.id))

@app.route("/perfil/<int:user_id>", methods=["GET", "POST"])
@login_required
def perfil_usuario(user_id):

    user = Usuario.query.options(
        joinedload(Usuario.notificacoes),
        joinedload(Usuario.crushes_feitos),
        joinedload(Usuario.posts)
    ).get_or_404(user_id)

    if request.method == "POST" and current_user.id == user.id:
        user.bio = request.form.get("bio")
        avatar_file = request.files.get("avatar")
        if avatar_file:
            user.avatar = processar_avatar_upload(
                avatar_file,
                app.config['UPLOAD_FOLDER_AVATARS'],
                user.gender,
                ALLOWED_IMAGES
            )
        try:
            db.session.commit()
            flash("Perfil atualizado com sucesso!", "success")
            return redirect(url_for("perfil_usuario", user_id=user.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao adicionar o comentário: {str(e)}', 'danger')

    editar = request.args.get("editar") == "1"
    notificacoes = user.notificacoes
    solicitacoes_recebidas = Amizade.query.filter_by(solicitado_id=user.id, status='pendente')

    amigos = Amizade.query.options(
        joinedload(Amizade.solicitante),
        joinedload(Amizade.solicitado)
    ).filter(
        ((Amizade.solicitante_id == user.id) | (Amizade.solicitado_id == user.id)),
        Amizade.status == 'aceita'
    )
    contagem_amigos = len(amigos.all())

    crush_existente = None
    if current_user.id != user.id:
        crush_existente = next(
            (crush for crush in current_user.crushes_feitos if crush.alvo_id == user.id),
            None
        )

    posts = Post.query.filter_by(usuario_id=user.id).order_by(Post.id.desc())

    # 👇 Adiciona essa parte aqui
    amizade = Amizade.query.filter(
        ((Amizade.solicitante_id == current_user.id) & (Amizade.solicitado_id == user.id)) |
        ((Amizade.solicitante_id == user.id) & (Amizade.solicitado_id == current_user.id))
    ).filter_by(status='aceita').first() if current_user.id != user.id else None

    return render_template(
        "perfil.html",
        user=user,
        editar=editar,
        posts=posts,
        crush_existente=crush_existente,
        notificacoes=notificacoes,
        solicitacoes_recebidas=solicitacoes_recebidas,
        amigos=amigos,
        contagem_amigos=contagem_amigos,
        amizade=amizade  # 👈 passa para o template
    )


@app.route('/enviar_amizade/<int:user_id>', methods=['POST'])
@login_required
def enviar_amizade(user_id):
    if current_user.id == user_id:
        flash("Você não pode se adicionar!", "warning")
        return redirect(url_for('perfil_usuario', user_id=user_id))

    amizade = Amizade.query.filter_by(
        solicitante_id=current_user.id,
        solicitado_id=user_id
    ).first()

    if not amizade:
        try:
            nova_amizade = Amizade(solicitante_id=current_user.id, solicitado_id=user_id)
            db.session.add(nova_amizade)
            db.session.commit()
            flash("Pedido de amizade enviado!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao enviar pedido de amizade: {str(e)}", "danger")
    else:
        flash("Pedido já existente!", "info")

    return redirect(url_for('perfil_usuario', user_id=user_id))


@app.route('/aceitar_amizade/<int:amizade_id>', methods=['POST'])
@login_required
def aceitar_amizade(amizade_id):
    amizade = Amizade.query.get(amizade_id)
    if amizade and amizade.solicitado_id == current_user.id:
        try:
            amizade.status = 'aceita'
            db.session.commit()
            flash("Solicitação de amizade aceita!", "success")
            return redirect(url_for('perfil_usuario', user_id=amizade.solicitante.id))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao aceitar a solicitação: " + str(e), "danger")
            return redirect(url_for('perfil_usuario', user_id=current_user.id))
    else:
        flash("Erro ao aceitar a solicitação.", "danger")
        return redirect(url_for('perfil_usuario', user_id=current_user.id))

@app.route('/recusar_amizade/<int:amizade_id>', methods=['POST'])
@login_required
def recusar_amizade(amizade_id):
    amizade = Amizade.query.get_or_404(amizade_id)
    if amizade.solicitado_id == current_user.id and amizade.status == 'pendente':
        try:
            amizade.status = 'recusa'
            db.session.commit()
            flash("Amizade recusada!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Erro ao recusar amizade: " + str(e), "danger")
    return redirect(url_for('perfil_usuario', user_id=current_user.id))

@app.route('/excluir_amizade/<int:amizade_id>', methods=['POST'])
@login_required
def excluir_amizade(amizade_id):
    amizade = Amizade.query.get_or_404(amizade_id)
    if (amizade.solicitante_id == current_user.id or amizade.solicitado_id == current_user.id) and amizade.status == 'aceita':
        try:
            db.session.delete(amizade)
            db.session.commit()
            flash("Amizade excluída com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Erro ao excluir amizade: " + str(e), "danger")
    else:
        flash("Você não tem permissão para excluir essa amizade.", "danger")
    return redirect(url_for('perfil'))

@app.route('/amigos')
@login_required
def amigos():
    rels = Amizade.query.filter(
        ((Amizade.solicitante_id == current_user.id) | (Amizade.solicitado_id == current_user.id)) &
        (Amizade.status == 'aceita')
    )

    lista_amigos = []
    for a in rels:
        amigo = a.solicitado if a.solicitante_id == current_user.id else a.solicitante
        # Anexa o id da amizade ao objeto do amigo
        amigo.amizade_id = a.id
        lista_amigos.append(amigo)

    return render_template('amigos.html', lista_amigos=lista_amigos, user=current_user)

@app.route('/solicitaçoes')
@login_required
def solicitacoes():
    solicitacoes_recebidas = Amizade.query.filter_by(solicitado_id=current_user.id, status='pendente')
    return render_template('solicitaçoes.html', pendentes=solicitacoes_recebidas)

@app.route('/buscar_usuarios', methods=['GET'])
@login_required
def buscar_usuarios():
    termo = request.args.get('q', '')
    usuarios = Usuario.query.filter(Usuario.username.ilike(f'%{termo}%'))
    return render_template('buscar_usuarios.html', usuarios=usuarios)

@app.route('/adicionar_crush/<int:user_id>', methods=['POST'])
@login_required
def adicionar_crush(user_id):
    if current_user.id == user_id:
        flash("Você não pode adicionar a si mesmo como crush!", "warning")
        return redirect(url_for('perfil_usuario', user_id=user_id))

    crush_existente = Crush.query.filter_by(admirador_id=current_user.id, alvo_id=user_id).first()

    if crush_existente:
        flash("Você já tem um crush por essa pessoa!", "info")
    else:
        try:
            novo_crush = Crush(admirador_id=current_user.id, alvo_id=user_id)
            db.session.add(novo_crush)
            db.session.commit()
            flash("Crush adicionado com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Erro ao adicionar crush: " + str(e), "danger")

    return redirect(url_for('perfil_usuario', user_id=user_id))

@app.route('/remover_crush/<int:user_id>', methods=['POST'])
@login_required
def remover_crush(user_id):
    if current_user.id == user_id:
        flash("Você não pode remover seu próprio crush!", "warning")
        return redirect(url_for('perfil_usuario', user_id=user_id))

    # Verificar se o crush existe
    crush_existente = Crush.query.filter_by(admirador_id=current_user.id, alvo_id=user_id).first()

    if crush_existente:
        try:
            db.session.delete(crush_existente)  # Remover o crush
            db.session.commit()
            flash("Crush removido com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Erro ao remover o crush: " + str(e), "danger")
    else:
        flash("Você não tem um crush por essa pessoa!", "info")

    return redirect(url_for('perfil_usuario', user_id=user_id))

@app.route("/amigos/<int:user_id>", methods=["GET"])
@login_required
def listar_amigos(user_id):
    user = Usuario.query.get_or_404(user_id)

    # Buscar as amizades aceitas para esse usuário
    amigos = Amizade.query.filter(
        ((Amizade.solicitante_id == user.id) | (Amizade.solicitado_id == user.id)),
        Amizade.status == 'aceita'
    )

    # Para cada amizade, recuperamos os dados dos amigos (evitando o 'id' do solicitante ou receptor)
    lista_amigos = []
    for amizade in amigos:
        if amizade.solicitante_id != user.id:
            amigo = Usuario.query.get(amizade.solicitante_id)
            lista_amigos.append(amigo)
        elif amizade.solicitado_id != user.id:
            amigo = Usuario.query.get(amizade.solicitado_id)
            lista_amigos.append(amigo)

    return render_template("amigos.html", user=user, lista_amigos=lista_amigos)

@app.route('/mensagem/enviar/<int:usuario_id>', methods=['POST', 'GET'])
@login_required
def enviar_mensagem(usuario_id):
    # Impede que o usuário envie mensagem para si mesmo
    if usuario_id == current_user.id:
        flash("Você não pode conversar consigo mesmo.", "warning")
        return redirect(url_for('index'))

    # Obtém o conteúdo da mensagem do formulário
    conteudo = request.form.get('conteudo')
    if not conteudo:
        flash("Mensagem vazia não pode ser enviada.", "warning")
        return redirect(url_for('ver_conversa', usuario_id=usuario_id))

    # Tenta encontrar uma conversa existente entre os dois usuários
    conversa = Conversa.query.filter(
        db.or_(
            db.and_(Conversa.usuario1_id == current_user.id, Conversa.usuario2_id == usuario_id),
            db.and_(Conversa.usuario1_id == usuario_id, Conversa.usuario2_id == current_user.id)
        )
    ).first()

    # Se a conversa não existir, cria uma nova
    if not conversa:
        conversa = Conversa(usuario1_id=current_user.id, usuario2_id=usuario_id)
        db.session.add(conversa)
        db.session.commit()  # Commit para garantir que o ID da conversa seja gerado

        # Verifica se a conversa foi registrada corretamente
        if not conversa.id:
            db.session.rollback()
            flash("Erro ao criar conversa. Tente novamente.", "danger")
            return redirect(url_for('ver_conversa', usuario_id=usuario_id))

    # Criação da nova mensagem
    nova_mensagem = Mensagem(
        conteudo=conteudo,
        remetente_id=current_user.id,
        conversa_id=conversa.id,
        data_envio=datetime.utcnow()
    )

    try:
        db.session.add(nova_mensagem)
        db.session.commit()  # Comita a nova mensagem após a conversa ser comitada corretamente
        flash("Mensagem enviada com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao enviar mensagem: {str(e)}", "danger")

    # Redireciona para a página da conversa
    return redirect(url_for('ver_conversa', usuario_id=usuario_id))

@app.route('/conversa/<int:usuario_id>')
@login_required
def ver_conversa(usuario_id):
    if usuario_id == current_user.id:
        flash("Você não pode conversar consigo mesmo.", "warning")
        return redirect(url_for('index'))  # ou alguma outra página
    # Recupera o usuário alvo (com 404 se não existir)
    usuario = Usuario.query.get_or_404(usuario_id)

    # Busca a conversa em qualquer direção entre current_user e usuario
    conversa = Conversa.query.filter(
        or_(
            and_(Conversa.usuario1_id == current_user.id, Conversa.usuario2_id == usuario_id),
            and_(Conversa.usuario1_id == usuario_id, Conversa.usuario2_id == current_user.id)
        )
    ).first()

    # Se já existe conversa, traz todas as mensagens ordenadas
    if conversa:
        mensagens = Mensagem.query \
            .options(joinedload(Mensagem.remetente)) \
            .filter_by(conversa_id=conversa.id) \
            .order_by(Mensagem.data_envio) \
            .all()
    else:
        mensagens = []

    return render_template(
        'conversa.html',
        usuario=usuario,
        mensagens=mensagens
    )

@app.route('/chats')
@app.route('/listar_chats')
@login_required
def listar_chats():
    # Busca todas as conversas em que o usuário está (como usuario1 ou usuario2)
    conversas = Conversa.query.filter(
        or_(
            Conversa.usuario1_id == current_user.id,
            Conversa.usuario2_id == current_user.id
        )
    ).order_by(Conversa.data_criacao.desc()).all()

    # Debug: imprime no terminal o que foi retornado
    print(f"[DEBUG] Conversas encontradas para user {current_user.id}: {conversas}")

    return render_template('chats.html', conversas=conversas)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
