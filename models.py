from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(10), nullable=False, default='Masculino')
    avatar = db.Column(db.String(150), nullable=True)
    bio = db.Column(db.String(100), nullable=False, default='')
    age = db.Column(db.Integer, nullable=True)

    # relacionamentos
    posts = db.relationship('Post', back_populates='autor', cascade='all, delete-orphan', lazy='dynamic')
    likes = db.relationship('Like', back_populates='usuario', cascade='all, delete-orphan', lazy='dynamic')
    comentarios = db.relationship('Comentario', back_populates='usuario', cascade='all, delete-orphan', lazy='dynamic')

    # amizades, crushes e notificações podem continuar com backref, sem conflitos
    amizades_enviadas = db.relationship(
        'Amizade',
        foreign_keys='Amizade.solicitante_id',
        back_populates='solicitante',
        lazy='dynamic'
    )
    amizades_recebidas = db.relationship(
        'Amizade',
        foreign_keys='Amizade.solicitado_id',
        back_populates='solicitado',
        lazy='dynamic'
    )
    crushes_feitos = db.relationship(
        'Crush',
        foreign_keys='Crush.admirador_id',
        back_populates='admirador',
        lazy='dynamic'
    )
    crushes_recebidos = db.relationship(
        'Crush',
        foreign_keys='Crush.alvo_id',
        back_populates='alvo',
        lazy='dynamic'
    )
    notificacoes = db.relationship('Notificacao', back_populates='usuario', cascade='all, delete-orphan', lazy='dynamic')

    def amizade_com(self, outro_usuario_id):
        return Amizade.query.filter(
            db.or_(
                db.and_(Amizade.solicitante_id == self.id, Amizade.solicitado_id == outro_usuario_id),
                db.and_(Amizade.solicitante_id == outro_usuario_id, Amizade.solicitado_id == self.id)
            )
        ).first()

class Amizade(db.Model):
    __tablename__ = 'amizades'

    id = db.Column(db.Integer, primary_key=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    solicitado_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    status = db.Column(db.String(50), default='pendente')  # 'pendente', 'aceita', 'rejeitada'

    # Relacionamentos
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], back_populates='amizades_enviadas')
    solicitado = db.relationship('Usuario', foreign_keys=[solicitado_id], back_populates='amizades_recebidas')

    def __repr__(self):
        return f"<Amizade {self.solicitante_id} - {self.solicitado_id} | Status: {self.status}>"

class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(120), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    autor = db.relationship('Usuario', back_populates='posts')
    likes = db.relationship('Like', back_populates='post', cascade='all, delete-orphan', lazy='dynamic')
    comentarios = db.relationship('Comentario', back_populates='post', cascade='all, delete-orphan', lazy='dynamic')

    def reagido_por(self, usuario, tipo):
        return self.likes.filter_by(usuario_id=usuario.id, tipo=tipo).first() is not None

    def curtido_por(self, usuario):
        if not usuario.is_authenticated:
            return False
        return self.likes.filter_by(usuario_id=usuario.id, tipo='like').first() is not None

    def contar_reacoes(self, tipo):
        return self.likes.filter_by(tipo=tipo).count()

    def total_likes(self):
        return self.likes.filter_by(tipo='like').count()

    def __repr__(self):
        return f"<Post {self.id}>"

class Like(db.Model):
    __tablename__ = 'like'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)  # e.g. 'like', 'love', 'haha'
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    usuario = db.relationship('Usuario', back_populates='likes')
    post = db.relationship('Post', back_populates='likes')

    def __repr__(self):
        return f"<Like {self.tipo} by User {self.usuario_id} on Post {self.post_id}>"

class Comentario(db.Model):
    __tablename__ = 'comentario'

    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    usuario = db.relationship('Usuario', back_populates='comentarios')
    post = db.relationship('Post', back_populates='comentarios')

class Crush(db.Model):
    __tablename__ = 'crushes'

    id = db.Column(db.Integer, primary_key=True)
    admirador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    alvo_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    revelado = db.Column(db.Boolean, default=False)

    admirador = db.relationship('Usuario', foreign_keys=[admirador_id], back_populates='crushes_feitos')
    alvo = db.relationship('Usuario', foreign_keys=[alvo_id], back_populates='crushes_recebidos')

class Notificacao(db.Model):
    __tablename__ = 'notificacao'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    mensagem = db.Column(db.String(200), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    usuario = db.relationship('Usuario', back_populates='notificacoes')
