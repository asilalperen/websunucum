from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

# İŞTE AJANIN ARADIĞI 3. MODEL (TAKİPÇİ ARA TABLOSU)
followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    profile_pic: so.Mapped[Optional[str]] = so.mapped_column(sa.String(120))
    is_verified: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, server_default=sa.text('0'))
    verification_code: so.Mapped[Optional[str]] = so.mapped_column(sa.String(10))
    require_2fa: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, server_default=sa.text('0'))
    # İlişkiler
    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author', cascade='all, delete-orphan')
    comments: so.WriteOnlyMapped['Comment'] = so.relationship(back_populates='author', cascade='all, delete-orphan')
    likes: so.WriteOnlyMapped['Like'] = so.relationship(back_populates='author', cascade='all, delete-orphan')
    notifications: so.WriteOnlyMapped['Notification'] = so.relationship(back_populates='user', cascade='all, delete-orphan')
    
    # Takipçi ilişkisi (Many-to-Many)
    followed: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers'
    )
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers,
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='followed'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'reset_password': self.id})

    @staticmethod
    def verify_reset_password_token(token, expires_in=600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            id = s.loads(token, max_age=expires_in)['reset_password']
        except:
            return None
        return db.session.get(User, id)

    def avatar(self, size):
        if self.profile_pic:
            return f'/static/profile_pics/{self.profile_pic}'
        return f'https://ui-avatars.com/api/?name={self.username}&background=E56B1F&color=fff&size={size}'

    def __repr__(self):
        return f'<User {self.username}>'

    def follow(self, user):
        if not self.is_following(user):
            self.followed.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        query = self.followed.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def has_liked_post(self, post):
        query = self.likes.select().where(Like.post_id == post.id)
        return db.session.scalar(query) is not None

    def like(self, post):
        if not self.has_liked_post(post):
            like = Like(author=self, post=post)
            db.session.add(like)

    def unlike(self, post):
        if self.has_liked_post(post):
            query = self.likes.select().where(Like.post_id == post.id)
            like = db.session.scalar(query)
            if like:
                db.session.delete(like)

    def followed_posts(self):
        # Takip edilenlerin gönderilerini getiren sorgu
        return db.select(Post).join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id).order_by(
                    Post.timestamp.desc())

class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    image_file: so.Mapped[Optional[str]] = so.mapped_column(sa.String(1000))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    comments_enabled: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=True)
    is_global: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, server_default=sa.text('0'))

    author: so.Mapped[User] = so.relationship(back_populates='posts')
    comments: so.Mapped[list['Comment']] = so.relationship(back_populates='post', cascade='all, delete-orphan')
    likes: so.Mapped[list['Like']] = so.relationship(back_populates='post', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Post {self.body}>'

class Comment(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.Text)
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Post.id), index=True)

    author: so.Mapped[User] = so.relationship(back_populates='comments')
    post: so.Mapped[Post] = so.relationship(back_populates='comments')

    def __repr__(self):
        return f'<Comment {self.body}>'

class Like(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Post.id), index=True)

    author: so.Mapped[User] = so.relationship(back_populates='likes')
    post: so.Mapped[Post] = so.relationship(back_populates='likes')

    def __repr__(self):
        return f'<Like user:{self.user_id} post:{self.post_id}>'

class Notification(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    message: so.Mapped[str] = so.mapped_column(sa.String(256))
    link: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    is_read: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)

    user: so.Mapped[User] = so.relationship(back_populates='notifications')

    def __repr__(self):
        return f'<Notification {self.message}>'

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))