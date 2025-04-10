from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(10), nullable=False, default='Masculino')
    avatar = db.Column(db.String(150), nullable=True)
    bio = db.Column(db.String(100), unique=False, nullable=False)

    # Novos campos
    age = db.Column(db.Integer, nullable=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(120), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    autor = db.relationship('Usuario', backref=db.backref('posts', lazy=True, cascade="all, delete"))
    likes = db.relationship('Like', backref='post', lazy='dynamic')

    def curtido_por(self, usuario):
        if not usuario.is_authenticated:
            return False
        return self.likes.filter_by(usuario_id=usuario.id).first() is not None

    def total_likes(self):
        return self.likes.count()

    def get_likes_lista(self):
        return self.likes.all()

    def __repr__(self):
        return f"<Post {self.id}>"

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    usuario = db.relationship('Usuario', backref=db.backref('comentarios', lazy=True))
    post = db.relationship('Post', backref=db.backref('comentarios', lazy=True, cascade="all, delete-orphan"))

class Amizade(db.Model):
    __tablename__ = 'amizades'
    id = db.Column(db.Integer, primary_key=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    solicitado_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    status = db.Column(db.String(20), default='pendente')  # pendente, aceita, recusada
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow)

    solicitante = db.relationship('Usuario',
        foreign_keys=[solicitante_id],
        backref=db.backref('amizades_enviadas', lazy='dynamic', foreign_keys=[solicitante_id])
    )
    solicitado = db.relationship('Usuario',
        foreign_keys=[solicitado_id],
        backref=db.backref('amizades_recebidas', lazy='dynamic', foreign_keys=[solicitado_id])
    )

    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], backref='amizades_enviadas')
    solicitado = db.relationship('Usuario', foreign_keys=[solicitado_id], backref='amizades_recebidas')