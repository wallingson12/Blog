from flask import Flask, render_template, redirect, url_for, flash, send_from_directory, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from models import db, Usuario, Post, Like, Comentario, Amizade
from forms import LoginForm, RegisterForm, PostForm
from flask_login import current_user

app = Flask(__name__)
load_dotenv()

# Configurações
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
# Pastas de upload
app.config['UPLOAD_FOLDER_AVATARS'] = os.path.join(app.root_path, 'static', 'uploads', 'avatars')
app.config['UPLOAD_FOLDER_POSTS'] = os.path.join(app.root_path, 'static', 'uploads', 'post_images')

# Inicialização
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
    posts = Post.query.all()
    return render_template('index.html', posts=posts, user=current_user)

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
        # Avatar enviado ou padrão por gênero
        if form.avatar.data and form.avatar.data.filename:
            avatar_file = form.avatar.data
            avatar_filename = secure_filename(avatar_file.filename)
            avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER_AVATARS'], avatar_filename))
        else:
            # Usa default .jpg conforme gênero
            avatar_filename = 'default_men_avatar.jpg' if form.gender.data == 'Masculino' else 'default_women_avatar.jpg'

        hashed_senha = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        novo_usuario = Usuario(
            username=form.username.data,
            password=hashed_senha,
            gender=form.gender.data,
            avatar=avatar_filename,
            age=form.age.data
        )
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/curtir/<int:post_id>', methods=['POST'])
@login_required
def curtir(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(usuario_id=current_user.id, post_id=post.id).first()
    if like:
        db.session.delete(like)
    else:
        db.session.add(Like(usuario_id=current_user.id, post_id=post.id))
    db.session.commit()
    return redirect(url_for('index'))

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
        if form.image.data and form.image.data.filename:
            image = form.image.data
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER_POSTS'], image_filename))
        else:
            image_filename = None
        novo_post = Post(conteudo=form.content.data, image=image_filename, autor=current_user)
        db.session.add(novo_post)
        db.session.commit()
        flash('Post criado com sucesso!', 'success')
        return redirect(url_for('index'))
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
        db.session.add(Comentario(conteudo=conteudo, usuario_id=current_user.id, post_id=post_id))
        db.session.commit()
        flash('Comentário adicionado com sucesso!', 'success')
    else:
        flash('O comentário não pode estar vazio.', 'warning')
    return redirect(url_for('index'))

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.usuario_id != current_user.id:
        flash('Você não tem permissão para excluir este post.', 'danger')
        return redirect(url_for('index'))
    if post.image:
        path = os.path.join(app.config['UPLOAD_FOLDER_POSTS'], post.image)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(post)
    db.session.commit()
    flash('Post excluído com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/perfil')
@login_required
def perfil():
    return redirect(url_for('perfil_usuario', user_id=current_user.id))

@app.route("/perfil/<int:user_id>", methods=["GET", "POST"])
@login_required
def perfil_usuario(user_id):
    user = Usuario.query.get_or_404(user_id)
    editar = request.args.get("editar") == "1"

    if request.method == "POST" and current_user.id == user.id:
        user.bio = request.form.get("bio")
        if "avatar" in request.files:
            avatar_file = request.files["avatar"]
            if avatar_file and avatar_file.filename:
                filename = secure_filename(avatar_file.filename)
                avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER_AVATARS'], filename))
                user.avatar = filename
            else:
                # default .jpg conforme gênero
                user.avatar = 'default_men_avatar.jpg' if user.gender == 'Masculino' else 'default_women_avatar.jpg'
        db.session.commit()
        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for("perfil_usuario", user_id=user.id))

    return render_template("perfil.html", user=user, editar=editar)

@app.route('/enviar_amizade/<int:user_id>', methods=['POST'])
@login_required
def enviar_amizade(user_id):
    if current_user.id == user_id:
        flash("Você não pode se adicionar!", "warning")
        return redirect(url_for('perfil_usuario', user_id=user_id))
    amizade = Amizade.query.filter_by(solicitante_id=current_user.id, solicitado_id=user_id).first()
    if not amizade:
        db.session.add(Amizade(solicitante_id=current_user.id, solicitado_id=user_id))
        db.session.commit()
        flash("Pedido de amizade enviado!", "success")
    else:
        flash("Pedido já existente!", "info")
    return redirect(url_for('perfil_usuario', user_id=user_id))

@app.route('/aceitar_amizade/<int:amizade_id>', methods=['POST'])
@login_required
def aceitar_amizade(amizade_id):
    amizade = Amizade.query.get_or_404(amizade_id)
    if amizade.solicitado_id == current_user.id and amizade.status == 'pendente':
        amizade.status = 'aceita'
        db.session.commit()
        flash("Amizade aceita!", "success")
    return redirect(url_for('perfil_usuario', user_id=current_user.id))

@app.route('/amigos')
@login_required
def amigos():
    rels = Amizade.query.filter(
        ((Amizade.solicitante_id == current_user.id) | (Amizade.solicitado_id == current_user.id)) &
        (Amizade.status == 'aceita')
    ).all()
    lista = [a.solicitado if a.solicitante_id == current_user.id else a.solicitante for a in rels]
    return render_template('amigos.html', amigos=lista)

@app.route('/solicitações')
@login_required
def solicitacoes():
    pendentes = Amizade.query.filter_by(solicitado_id=current_user.id, status='pendente').all()
    return render_template('solicitações.html', pendentes=pendentes)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)