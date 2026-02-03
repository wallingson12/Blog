from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, Post, Like, Comentario
from forms import PostForm
from permissions import verificar_autor_do_post
from utils import processar_imagem_post
import os

posts_bp = Blueprint('posts', __name__)

@posts_bp.route("/")
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    pagination = Post.query \
        .order_by(Post.id.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    posts = pagination.items

    return render_template(
        'index.html',
        posts=posts,
        pagination=pagination,
        user=current_user
    )

@posts_bp.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        image_filename = processar_imagem_post(
            form.image.data,
            current_app.config['UPLOAD_FOLDER_POSTS'],
            current_app.config['ALLOWED_IMAGES']
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
            return redirect(url_for('posts.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro: {str(e)}', 'danger')

    return render_template('new_post.html', form=form)

@posts_bp.route('/curtir/<int:post_id>', methods=['POST'])
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
        return redirect(url_for('posts.index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro: {str(e)}', 'danger')
        return redirect(url_for('posts.index'))

@posts_bp.route('/comentar/<int:post_id>', methods=['POST'])
@login_required
def comentar(post_id):
    conteudo = request.form.get('conteudo')
    if conteudo:
        try:
            db.session.add(Comentario(conteudo=conteudo, usuario_id=current_user.id, post_id=post_id))
            db.session.commit()
            flash('Comentário adicionado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao adicionar o comentário: {str(e)}', 'danger')
    else:
        flash('O comentário não pode estar vazio.', 'warning')

    return redirect(url_for('posts.index'))

@posts_bp.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if not verificar_autor_do_post(post):
        return redirect(url_for('posts.index'))
    if post.image:
        path = os.path.join(current_app.config['UPLOAD_FOLDER_POSTS'], post.image)
        if os.path.exists(path):
            os.remove(path)
    try:
        db.session.delete(post)
        db.session.commit()
        flash('Post excluído com sucesso!', 'success')
        return redirect(url_for('posts.index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao adicionar o comentário: {str(e)}', 'danger')
        return redirect(url_for('posts.index'))

@posts_bp.route('/sobre')
@login_required
def sobre():
    return render_template('sobre.html')
