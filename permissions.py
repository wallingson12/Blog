# permissions.py
from flask import flash
from flask_login import current_user

def verificar_autor_do_post(post):
    if post.usuario_id != current_user.id:
        flash('Você não tem permissão para realizar esta ação.', 'danger')
        return False
    return True
