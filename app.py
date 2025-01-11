from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm, PostForm
from models import db, Usuario, Post
from werkzeug.utils import secure_filename
import os
from flask_migrate import Migrate
from flask import send_from_directory

# Inicializando a aplicação
app = Flask(__name__)

# Configurações
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'

# Definindo o diretório para o upload do avatar
UPLOAD_FOLDER = 'uploads/avatars'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Inicializando o banco de dados
db.init_app(app)

# Inicializando a migração
migrate = Migrate(app, db)

# Inicializando o LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# Função que carrega o usuário para login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# Rota para a página inicial
@app.route('/')
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('index.html', posts=posts)


# Rota de login
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

@app.route('/uploads/avatars/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'static/uploads/avatars'), filename)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        avatar_filename = None  # Definir como None por padrão

        # Verificar se o formulário tem um arquivo de avatar
        if form.avatar.data:
            avatar_file = form.avatar.data
            avatar_filename = secure_filename(avatar_file.filename)  # Garante que o nome do arquivo é seguro
            avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename))  # Salva a imagem
        else:
            # Se não tiver avatar, definir um avatar padrão baseado no gênero
            gender = form.gender.data  # Usa 'gender' do formulário
            if gender == 'Masculino':
                avatar_filename = 'default_men_avatar.png'  # Avatar padrão para homem
            else:
                avatar_filename = 'default_women_avatar.png'  # Avatar padrão para mulher

        # Criptografa a senha do usuário
        hashed_senha = generate_password_hash(form.password.data, method='pbkdf2:sha256')

        # Cria o novo usuário, incluindo o nome do avatar
        novo_usuario = Usuario(username=form.username.data, password=hashed_senha, gender=form.gender.data,
                               avatar=avatar_filename)

        db.session.add(novo_usuario)
        db.session.commit()

        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

# Rota de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))


# Rota para criar um novo post
@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        novo_post = Post(titulo=form.title.data, conteudo=form.content.data, autor=current_user)
        db.session.add(novo_post)
        db.session.commit()
        flash('Post criado com sucesso!', 'success')
        return redirect(url_for('index'))
    return render_template('new_post.html', form=form)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

# Inicializando o servidor
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco de dados
    app.run(debug=True)