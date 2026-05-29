import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Form güvenliği için. Eğer ortam değişkeninde yoksa varsayılanı kullanır.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'siyah-beyaz-sampiyon-besiktas'
    
    # Veritabanı dosyasının nerede duracağını söylüyoruz (app.db)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
        
    # Maksimum yükleme boyutunu (50MB) belirliyoruz
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024

    # E-posta (SMTP) Sunucu Ayarları
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None or True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # Doğrulama e-postaları hangi isimden gitsin?
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@mementos.com'