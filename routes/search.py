from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import login_required
from models import Usuario

search_bp = Blueprint('search', __name__)

@search_bp.route('/buscar_usuarios', methods=['GET'])
@login_required
def buscar_usuarios():
    termo = request.args.get('q', '')
    usuarios = Usuario.query.filter(Usuario.username.ilike(f'%{termo}%'))
    return render_template('buscar_usuarios.html', usuarios=usuarios)

@search_bp.route("/autocomplete")
@login_required
def autocomplete():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    users = Usuario.query.filter(Usuario.username.ilike(f"%{q}%")).limit(5).all()

    results = []
    for user in users:
        results.append({
            "name": user.username,
            "url": url_for("profile.perfil_usuario", user_id=user.id),
            "avatar": url_for('auth.uploaded_file', folder='avatars', filename=user.avatar) if user.avatar else url_for(
            'static', filename='default_avatar.png')
        })

    return jsonify(results)
