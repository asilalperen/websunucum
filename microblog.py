import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
from app.models import User, Post

app = create_app()

# Bu kısım hocanın dökümanındaki "Flask Shell" kullanımı için.
# Terminalde 'flask shell' yazınca bunları otomatik tanısın diye yapıyoruz.
@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Post': Post}