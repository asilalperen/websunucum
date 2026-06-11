import sys
from app import create_app, db
from app.models import User

app = create_app()

def set_admin(username):
    with app.app_context():
        user = db.session.scalar(db.select(User).filter_by(username=username))
        if user is None:
            print(f"Hata: '{username}' adında bir kullanıcı bulunamadı.")
            print("Lütfen önce siteye girip normal bir şekilde kayıt olun.")
            return

        user.is_admin = True
        user.is_approved = True
        db.session.commit()
        print(f"BAŞARILI: '{username}' artık bir YÖNETİCİ (Admin) ve hesabı onaylandı!")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Kullanım: python set_admin.py <kullanici_adiniz>")
        sys.exit(1)
    
    username = sys.argv[1]
    set_admin(username)
