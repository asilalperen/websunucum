from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

# Eklentileri dışarıda tanımlıyoruz (Factory Pattern kuralı)
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()
login.login_view = 'auth.login'  # Blueprint kullandığımız için auth.login oldu

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # PythonAnywhere arkasındaki gerçek IP'leri alabilmek için ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    app.config.from_object(config_class)

    # Eklentileri bu uygulama örneğine bağlıyoruz
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    talisman.init_app(
        app,
        content_security_policy={
            'default-src': [
                '\'self\'',
                '\'unsafe-inline\'',
                '\'unsafe-eval\'',
                'https:',
                'data:',
                'blob:'
            ]
        },
        force_https=False,
        session_cookie_secure=False
    )

    # BLUEPRINT'LERİ SİSTEME KAYDEDİYORUZ
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Hata yönetimini bağlıyoruz
   # Hata yönetimini bağlıyoruz
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    import re
    from markupsafe import Markup

    def mentions_filter(text):
        if not text:
            return text
        def replace_match(match):
            username = match.group(1)
            return f'<a href="/user/{username}" style="color: var(--accent-orange); font-weight: bold; text-decoration: none;">@{username}</a>'
        html = re.sub(r'@([a-zA-Z0-9_ğüşöçıİĞÜŞÖÇ]+)', replace_match, text)
        return Markup(html)

    app.jinja_env.filters['mentions'] = mentions_filter

    return app