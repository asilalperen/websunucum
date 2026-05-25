from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

# Eklentileri dışarıda tanımlıyoruz (Factory Pattern kuralı)
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()
login.login_view = 'auth.login'  # Blueprint kullandığımız için auth.login oldu

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Eklentileri bu uygulama örneğine bağlıyoruz
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)

    # BLUEPRINT'LERİ SİSTEME KAYDEDİYORUZ
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Hata yönetimini bağlıyoruz
   # Hata yönetimini bağlıyoruz
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    return app