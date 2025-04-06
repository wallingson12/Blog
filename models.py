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