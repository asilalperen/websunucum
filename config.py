import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Form güvenliği için. Eğer ortam değişkeninde yoksa varsayılanı kullanır.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'siyah-beyaz-sampiyon-besiktas'
    
    # Veritabanı dosyasının nerede duracağını söylüyoruz (app.db)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
        
    # Maksimum yükleme boyutunu (50MB) belirliyoruz
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024