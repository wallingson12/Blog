from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Usuario
from forms import LoginForm, RegisterForm
from utils import processar_avatar_upload
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('posts.index'))
        else:
            flash('Usuário ou senha incorretos!', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        avatar_filename = processar_avatar_upload(
            form.avatar.data,
            current_app.config['UPLOAD_FOLDER_AVATARS'],
            form.gender.data,
            current_app.config['ALLOWED_IMAGES']
        )

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
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro: {str(e)}', 'danger')

    return render_template('register.html', title='Register', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/uploads/<folder>/<filename>')
def uploaded_file(folder, filename):
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'uploads', folder), filename)
