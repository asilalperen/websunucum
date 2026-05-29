from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    u = db.session.query(User).filter_by(username='alperen').first()
    if u:
        u.set_password('123456')
        db.session.commit()
        print("Şifre başarıyla '123456' olarak güncellendi!")
    else:
        print("alperen isimli kullanıcı bulunamadı!")
