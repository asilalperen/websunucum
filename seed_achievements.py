from app import create_app, db
from app.models import Achievement

app = create_app()

badges = [
    {
        "name": "İlk Adım",
        "description": "Mementgram'a ilk anını başarıyla kaydettin.",
        "icon": "🥇",
        "points": 10
    },
    {
        "name": "Global Elçi",
        "description": "Tüm dünyanın görebileceği ilk global anını paylaştın.",
        "icon": "🌍",
        "points": 15
    },
    {
        "name": "Sohbet Başlatıcı",
        "description": "Bir gönderiye ilk yorumunu yaptın.",
        "icon": "💬",
        "points": 5
    },
    {
        "name": "Sevgi Pıtırcığı",
        "description": "Diğer insanların anılarına tam 10 kez kalp bıraktın.",
        "icon": "❤️",
        "points": 10
    },
    {
        "name": "Çırak Fotoğrafçı",
        "description": "Sisteme 3 fotoğraf yükledin. Flaşlar patlıyor!",
        "icon": "📸",
        "points": 10
    },
    {
        "name": "Usta Fotoğrafçı",
        "description": "5 fotoğraf paylaşarak vizörün efendisi oldun.",
        "icon": "🎬",
        "points": 20
    },
    {
        "name": "NE 20 FOTOĞRAF MI?",
        "description": "Tam 20 fotoğraf paylaştın! Kameranın hafızası doldu sayende.",
        "icon": "🤯",
        "points": 50
    },
    {
        "name": "Sosyal Kelebek",
        "description": "3 farklı gruba üye olarak sosyalliğini kanıtladın.",
        "icon": "🦋",
        "points": 25
    },
    {
        "name": "Gece Kuşu",
        "description": "Gece yarısı (00:00 - 04:00) arasında anı paylaştın.",
        "icon": "🦉",
        "points": 20
    }
]

with app.app_context():
    for b in badges:
        existing = db.session.scalar(db.select(Achievement).where(Achievement.name == b['name']))
        if not existing:
            new_badge = Achievement(name=b['name'], description=b['description'], icon=b['icon'], points=b['points'])
            db.session.add(new_badge)
            print(f"Added: {b['name']}")
        else:
            # Update existing if changed
            existing.description = b['description']
            existing.icon = b['icon']
            existing.points = b['points']
            print(f"Updated: {b['name']}")
            
    db.session.commit()
    print("All achievements seeded successfully!")
