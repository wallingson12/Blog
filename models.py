from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Conversa(db.Model):
    __tablename__ = 'conversa'

    id = db.Column(db.Integer, primary_key=True)
    usuario1_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario2_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos com a tabela Usuario
    usuario1 = db.relationship('Usuario', foreign_keys=[usuario1_id], backref='minhas_conversas_iniciadas ')
    usuario2 = db.relationship('Usuario', foreign_keys=[usuario2_id], backref='minhas_conversas_recebidas')

    # Relacionamento com a tabela Mensagem
    mensagens = db.relationship('Mensagem', back_populates='conversa', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Conversa entre {self.usuario1_id} e {self.usuario2_id}>"

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(10), nullable=False, default='Masculino')
    avatar = db.Column(db.String(150), nullable=True)
    bio = db.Column(db.String(100), nullable=False, default='')
    age = db.Column(db.Integer, nullable=True)

    # Relacionamentos com as conversas
    conversas_iniciadas = db.relationship('Conversa', foreign_keys=[Conversa.usuario1_id], backref='iniciador', lazy='dynamic')
    conversas_recebidas = db.relationship('Conversa', foreign_keys=[Conversa.usuario2_id], backref='receptor', lazy='dynamic')

    # Relacionamentos simplificados com backref
    posts = db.relationship('Post', backref='Usuario', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='Usuario', cascade='all, delete-orphan')
    comentarios = db.relationship('Comentario', backref='Usuario', cascade='all, delete-orphan')

    # Amizades, crushes e notificações com backref ajustado
    amizades_enviadas = db.relationship('Amizade', foreign_keys='Amizade.solicitante_id', backref='solicitante_amizade')
    amizades_recebidas = db.relationship('Amizade', foreign_keys='Amizade.solicitado_id', backref='solicitado_amizade')
    crushes_feitos = db.relationship('Crush', foreign_keys='Crush.admirador_id', backref='admirador_crush')
    crushes_recebidos = db.relationship('Crush', foreign_keys='Crush.alvo_id', backref='alvo_crush')
    notificacoes = db.relationship('Notificacao', backref='Usuario', cascade='all, delete-orphan')

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
    likes = db.relationship('Like', back_populates='post', cascade='all, delete-orphan')
    comentarios = db.relationship('Comentario', back_populates='post', cascade='all, delete-orphan',)

    def reagido_por(self, usuario, tipo):
        return db.session.query(Like).filter_by(usuario_id=usuario.id, tipo=tipo).first() is not None

    def curtido_por(self, usuario):
        if not usuario.is_authenticated:
            return False
        return self.likes.filter_by(usuario_id=usuario.id, tipo='like').first() is not None

    def contar_reacoes(self, tipo):
        return db.session.query(Like).filter_by(post_id=self.id, tipo=tipo).count()

    def total_likes(self):
        return db.session.query(Like).filter_by(post_id=self.id, tipo='like').count()

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

class Mensagem(db.Model):
    __tablename__ = 'mensagem'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Autoincrement
    conteudo = db.Column(db.String(500), nullable=False)
    remetente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    conversa_id = db.Column(db.Integer, db.ForeignKey('conversa.id'), nullable=False)
    data_envio = db.Column(db.DateTime, nullable=False)

    # Relacionamento com a tabela 'Conversa'
    conversa = db.relationship('Conversa', back_populates='mensagens')

    # Relacionamento com a tabela 'Usuario' (remetente)
    remetente = db.relationship('Usuario', lazy='joined')

    def __repr__(self):
        return f"<Mensagem de {self.remetente_id} na conversa {self.conversa_id}>"
