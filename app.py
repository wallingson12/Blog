from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from models import db, Usuario
from routes.auth import auth_bp
from routes.posts import posts_bp
from routes.profile import profile_bp
from routes.friends import friends_bp
from routes.messages import messages_bp
from routes.search import search_bp

app = Flask(__name__)
load_dotenv()

# Configurações
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER_AVATARS'] = os.path.join(app.root_path, 'static', 'uploads', 'avatars')
app.config['UPLOAD_FOLDER_POSTS'] = os.path.join(app.root_path, 'static', 'uploads', 'post_images')
app.config['ALLOWED_IMAGES'] = {'png', 'jpg', 'jpeg', 'gif'}

# Inicialização do banco de dados
db.init_app(app)
migrate = Migrate(app, db)

# Configuração do Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Você precisa estar logado para acessar esta página."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Registro dos Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(friends_bp)
app.register_blueprint(messages_bp)
app.register_blueprint(search_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
