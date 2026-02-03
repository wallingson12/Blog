from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Usuario, Amizade
from sqlalchemy.orm import joinedload

friends_bp = Blueprint('friends', __name__)

@friends_bp.route('/enviar_amizade/<int:user_id>', methods=['POST'])
@login_required
def enviar_amizade(user_id):
    if current_user.id == user_id:
        flash("Você não pode se adicionar!", "warning")
        return redirect(url_for('profile.perfil_usuario', user_id=user_id))

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

    return redirect(url_for('profile.perfil_usuario', user_id=user_id))

@friends_bp.route('/aceitar_amizade/<int:amizade_id>', methods=['POST'])
@login_required
def aceitar_amizade(amizade_id):
    amizade = Amizade.query.get(amizade_id)
    if amizade and amizade.solicitado_id == current_user.id:
        try:
            amizade.status = 'aceita'
            db.session.commit()
            flash("Solicitação de amizade aceita!", "success")
            return redirect(url_for('profile.perfil_usuario', user_id=amizade.solicitante.id))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao aceitar a solicitação: " + str(e), "danger")
            return redirect(url_for('profile.perfil_usuario', user_id=current_user.id))
    else:
        flash("Erro ao aceitar a solicitação.", "danger")
        return redirect(url_for('profile.perfil_usuario', user_id=current_user.id))

@friends_bp.route('/recusar_amizade/<int:amizade_id>', methods=['POST'])
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
    return redirect(url_for('profile.perfil_usuario', user_id=current_user.id))

@friends_bp.route('/excluir_amizade/<int:amizade_id>', methods=['POST'])
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
    return redirect(url_for('profile.perfil'))

@friends_bp.route('/amigos')
@login_required
def amigos():
    rels = Amizade.query.filter(
        ((Amizade.solicitante_id == current_user.id) | (Amizade.solicitado_id == current_user.id)) &
        (Amizade.status == 'aceita')
    )

    lista_amigos = []
    for a in rels:
        amigo = a.solicitado if a.solicitante_id == current_user.id else a.solicitante
        amigo.amizade_id = a.id
        lista_amigos.append(amigo)

    return render_template('amigos.html', lista_amigos=lista_amigos, user=current_user)

@friends_bp.route('/solicitaçoes')
@login_required
def solicitacoes():
    solicitacoes_recebidas = Amizade.query.filter_by(solicitado_id=current_user.id, status='pendente')
    return render_template('solicitaçoes.html', pendentes=solicitacoes_recebidas)

@friends_bp.route("/amigos/<int:user_id>", methods=["GET"])
@login_required
def listar_amigos(user_id):
    user = Usuario.query.get_or_404(user_id)

    amigos = Amizade.query.filter(
        ((Amizade.solicitante_id == user.id) | (Amizade.solicitado_id == user.id)),
        Amizade.status == 'aceita'
    )

    lista_amigos = []
    for amizade in amigos:
        if amizade.solicitante_id != user.id:
            amigo = Usuario.query.get(amizade.solicitante_id)
            lista_amigos.append(amigo)
        elif amizade.solicitado_id != user.id:
            amigo = Usuario.query.get(amizade.solicitado_id)
            lista_amigos.append(amigo)

    return render_template("amigos.html", user=user, lista_amigos=lista_amigos)
