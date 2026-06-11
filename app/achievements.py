from app import db
from app.models import Achievement, Post, Comment, Notification, user_achievement
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

def check_achievements(user):
    # This function checks the user's stats and awards badges if conditions are met
    # Returns a list of newly unlocked achievements to display in flash messages or notifications
    
    unlocked_names = []
    
    # Pre-fetch all user's achievements to avoid multiple queries
    user_achievements = [a.name for a in user.achievements]
    
    # 1. İlk Adım (1 post)
    if "İlk Adım" not in user_achievements and db.session.scalar(user.posts.select().limit(1)) is not None:
        unlocked_names.append("İlk Adım")
        
    # 2. Global Elçi (1 global post)
    if "Global Elçi" not in user_achievements:
        global_post = db.session.scalar(user.posts.select().where(Post.is_global == True).limit(1))
        if global_post:
            unlocked_names.append("Global Elçi")
            
    # 3. Sohbet Başlatıcı (1 comment)
    if "Sohbet Başlatıcı" not in user_achievements and db.session.scalar(user.comments.select().limit(1)) is not None:
        unlocked_names.append("Sohbet Başlatıcı")
        
    # 4. Sevgi Pıtırcığı (10 likes given)
    # We need to count likes by this user
    if "Sevgi Pıtırcığı" not in user_achievements:
        like_count = db.session.scalar(db.select(func.count()).select_from(user.likes.select().subquery()))
        if like_count >= 10:
            unlocked_names.append("Sevgi Pıtırcığı")
            
    # Photo counting logic (5, 6, 7)
    # Count how many photos the user has uploaded
    if "Çırak Fotoğrafçı" not in user_achievements or "Usta Fotoğrafçı" not in user_achievements or "NE 20 FOTOĞRAF MI?" not in user_achievements:
        posts = db.session.scalars(user.posts.select()).all()
        photo_count = sum(len(p.image_file.split(',')) for p in posts if p.image_file)
        
        if "Çırak Fotoğrafçı" not in user_achievements and photo_count >= 3:
            unlocked_names.append("Çırak Fotoğrafçı")
        if "Usta Fotoğrafçı" not in user_achievements and photo_count >= 5:
            unlocked_names.append("Usta Fotoğrafçı")
        if "NE 20 FOTOĞRAF MI?" not in user_achievements and photo_count >= 20:
            unlocked_names.append("NE 20 FOTOĞRAF MI?")
            
    # 8. Sosyal Kelebek (3 groups)
    if "Sosyal Kelebek" not in user_achievements and len(user.groups) >= 3:
        unlocked_names.append("Sosyal Kelebek")
        
    # 9. Gece Kuşu (Post between 00:00 and 04:00)
    if "Gece Kuşu" not in user_achievements:
        posts = db.session.scalars(user.posts.select()).all()
        for p in posts:
            if p.timestamp:
                local_time = p.timestamp + timedelta(hours=3) # Assuming Turkey time UTC+3
                if 0 <= local_time.hour < 4:
                    unlocked_names.append("Gece Kuşu")
                    break

    # Process unlocks
    if unlocked_names:
        achievements_to_add = db.session.scalars(db.select(Achievement).where(Achievement.name.in_(unlocked_names))).all()
        for ach in achievements_to_add:
            user.achievements.append(ach)
            user.points += ach.points
            # Create notification
            notif = Notification(user=user, message=f"🏆 Tebrikler! '{ach.name}' rozetini kazandın! (+{ach.points} Puan)", link="/user/" + user.username)
            db.session.add(notif)
            
            # Flash message for the Steam-style popup
            from flask import flash
            flash(f"{ach.icon}|{ach.name}|{ach.description}|{ach.points}", "achievement")
            
        db.session.commit()
        
    return unlocked_names
