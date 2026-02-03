from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, Usuario, Post, Amizade, Crush
from utils import processar_avatar_upload
from sqlalchemy.orm import joinedload

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/perfil')
@login_required
def perfil():
    return redirect(url_for('profile.perfil_usuario', user_id=current_user.id))

@profile_bp.route("/perfil/<int:user_id>", methods=["GET", "POST"])
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
                current_app.config['UPLOAD_FOLDER_AVATARS'],
                user.gender,
                current_app.config['ALLOWED_IMAGES']
            )
        try:
            db.session.commit()
            flash("Perfil atualizado com sucesso!", "success")
            return redirect(url_for("profile.perfil_usuario", user_id=user.id))
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
        amizade=amizade
    )

@profile_bp.route('/adicionar_crush/<int:user_id>', methods=['POST'])
@login_required
def adicionar_crush(user_id):
    if current_user.id == user_id:
        flash("Você não pode adicionar a si mesmo como crush!", "warning")
        return redirect(url_for('profile.perfil_usuario', user_id=user_id))

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

    return redirect(url_for('profile.perfil_usuario', user_id=user_id))

@profile_bp.route('/remover_crush/<int:user_id>', methods=['POST'])
@login_required
def remover_crush(user_id):
    if current_user.id == user_id:
        flash("Você não pode remover seu próprio crush!", "warning")
        return redirect(url_for('profile.perfil_usuario', user_id=user_id))

    crush_existente = Crush.query.filter_by(admirador_id=current_user.id, alvo_id=user_id).first()

    if crush_existente:
        try:
            db.session.delete(crush_existente)
            db.session.commit()
            flash("Crush removido com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Erro ao remover o crush: " + str(e), "danger")
    else:
        flash("Você não tem um crush por essa pessoa!", "info")

    return redirect(url_for('profile.perfil_usuario', user_id=user_id))
