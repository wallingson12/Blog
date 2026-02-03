from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Usuario, Conversa, Mensagem
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/mensagem/enviar/<int:usuario_id>', methods=['POST', 'GET'])
@login_required
def enviar_mensagem(usuario_id):
    if usuario_id == current_user.id:
        flash("Você não pode conversar consigo mesmo.", "warning")
        return redirect(url_for('posts.index'))

    conteudo = request.form.get('conteudo')
    if not conteudo:
        flash("Mensagem vazia não pode ser enviada.", "warning")
        return redirect(url_for('messages.ver_conversa', usuario_id=usuario_id))

    conversa = Conversa.query.filter(
        db.or_(
            db.and_(Conversa.usuario1_id == current_user.id, Conversa.usuario2_id == usuario_id),
            db.and_(Conversa.usuario1_id == usuario_id, Conversa.usuario2_id == current_user.id)
        )
    ).first()

    if not conversa:
        conversa = Conversa(usuario1_id=current_user.id, usuario2_id=usuario_id)
        db.session.add(conversa)
        db.session.commit()

        if not conversa.id:
            db.session.rollback()
            flash("Erro ao criar conversa. Tente novamente.", "danger")
            return redirect(url_for('messages.ver_conversa', usuario_id=usuario_id))

    nova_mensagem = Mensagem(
        conteudo=conteudo,
        remetente_id=current_user.id,
        conversa_id=conversa.id,
        data_envio=datetime.utcnow()
    )

    try:
        db.session.add(nova_mensagem)
        db.session.commit()
        flash("Mensagem enviada com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao enviar mensagem: {str(e)}", "danger")

    return redirect(url_for('messages.ver_conversa', usuario_id=usuario_id))

@messages_bp.route('/conversa/<int:usuario_id>')
@login_required
def ver_conversa(usuario_id):
    if usuario_id == current_user.id:
        flash("Você não pode conversar consigo mesmo.", "warning")
        return redirect(url_for('posts.index'))

    usuario = Usuario.query.get_or_404(usuario_id)

    conversa = Conversa.query.filter(
        or_(
            and_(Conversa.usuario1_id == current_user.id, Conversa.usuario2_id == usuario_id),
            and_(Conversa.usuario1_id == usuario_id, Conversa.usuario2_id == current_user.id)
        )
    ).first()

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

@messages_bp.route('/chats')
@messages_bp.route('/listar_chats')
@login_required
def listar_chats():
    conversas = Conversa.query.filter(
        or_(
            Conversa.usuario1_id == current_user.id,
            Conversa.usuario2_id == current_user.id
        )
    ).order_by(Conversa.data_criacao.desc()).all()

    print(f"[DEBUG] Conversas encontradas para user {current_user.id}: {conversas}")

    return render_template('chats.html', conversas=conversas)
