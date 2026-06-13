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

user_group = sa.Table(
    'user_group',
    db.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('group_id', sa.Integer, sa.ForeignKey('group.id'), primary_key=True)
)

post_group = sa.Table(
    'post_group',
    db.metadata,
    sa.Column('post_id', sa.Integer, sa.ForeignKey('post.id'), primary_key=True),
    sa.Column('group_id', sa.Integer, sa.ForeignKey('group.id'), primary_key=True)
)

user_achievement = sa.Table(
    'user_achievement',
    db.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('achievement_id', sa.Integer, sa.ForeignKey('achievement.id'), primary_key=True),
    sa.Column('date_earned', sa.DateTime, default=lambda: datetime.now(timezone.utc))
)

saved_posts = sa.Table(
    'saved_posts',
    db.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('post_id', sa.Integer, sa.ForeignKey('post.id'), primary_key=True)
)

story_group = sa.Table(
    'story_group',
    db.metadata,
    sa.Column('story_id', sa.Integer, sa.ForeignKey('story.id'), primary_key=True),
    sa.Column('group_id', sa.Integer, sa.ForeignKey('group.id'), primary_key=True)
)

story_views = sa.Table(
    'story_views',
    db.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('story_id', sa.Integer, sa.ForeignKey('story.id'), primary_key=True),
    sa.Column('viewed_at', sa.DateTime, default=lambda: datetime.now(timezone.utc))
)

story_likes = sa.Table(
    'story_likes',
    db.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('story_id', sa.Integer, sa.ForeignKey('story.id'), primary_key=True),
    sa.Column('liked_at', sa.DateTime, default=lambda: datetime.now(timezone.utc))
)

class Story(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), index=True)
    media_file: so.Mapped[str] = so.mapped_column(sa.String(120))
    is_video: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    
    author: so.Mapped['User'] = so.relationship(back_populates='stories')
    groups: so.Mapped[list['Group']] = so.relationship(secondary=story_group, back_populates='stories')
    viewers: so.Mapped[list['User']] = so.relationship(secondary=story_views, back_populates='viewed_stories')
    likers: so.Mapped[list['User']] = so.relationship(secondary=story_likes, back_populates='liked_stories')

    def __repr__(self):
        return f'<Story {self.id} by {self.author.username}>'

class Achievement(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, index=True)
    description: so.Mapped[str] = so.mapped_column(sa.String(256))
    icon: so.Mapped[str] = so.mapped_column(sa.String(64)) # E.g., '🥇', '🏆', or a CSS class
    points: so.Mapped[int] = so.mapped_column(default=0)
    
    users: so.Mapped[list['User']] = so.relationship(secondary=user_achievement, back_populates='achievements')
    
    def __repr__(self):
        return f'<Achievement {self.name}>'

class Group(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, index=True)
    
    users: so.Mapped[list['User']] = so.relationship(secondary=user_group, back_populates='groups')
    posts: so.Mapped[list['Post']] = so.relationship(secondary=post_group, back_populates='groups')
    stories: so.Mapped[list['Story']] = so.relationship(secondary=story_group, back_populates='groups')
    
    def __repr__(self):
        return f'<Group {self.name}>'

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
    is_admin: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, server_default=sa.text('0'))
    is_approved: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, server_default=sa.text('0'))
    points: so.Mapped[int] = so.mapped_column(sa.Integer, default=0, server_default=sa.text('0'))
    
    # İlişkiler
    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author', cascade='all, delete-orphan')
    comments: so.WriteOnlyMapped['Comment'] = so.relationship(back_populates='author', cascade='all, delete-orphan')
    likes: so.WriteOnlyMapped['Like'] = so.relationship(back_populates='author', cascade='all, delete-orphan')
    comment_likes: so.WriteOnlyMapped['CommentLike'] = so.relationship(back_populates='author', cascade='all, delete-orphan')
    notifications: so.WriteOnlyMapped['Notification'] = so.relationship(back_populates='user', cascade='all, delete-orphan')
    saved_posts: so.WriteOnlyMapped['Post'] = so.relationship(secondary=saved_posts, passive_deletes=True)
    stories: so.WriteOnlyMapped['Story'] = so.relationship(back_populates='author', cascade='all, delete-orphan')
    viewed_stories: so.WriteOnlyMapped['Story'] = so.relationship(secondary=story_views, back_populates='viewers')
    liked_stories: so.WriteOnlyMapped['Story'] = so.relationship(secondary=story_likes, back_populates='likers')
    
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
    
    groups: so.Mapped[list['Group']] = so.relationship(secondary=user_group, back_populates='users')
    achievements: so.Mapped[list['Achievement']] = so.relationship(secondary=user_achievement, back_populates='users')

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

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followed.select().subquery())
        return db.session.scalar(query)

    def has_saved_post(self, post):
        query = self.saved_posts.select().where(Post.id == post.id)
        return db.session.scalar(query) is not None

    def save_post(self, post):
        if not self.has_saved_post(post):
            self.saved_posts.add(post)

    def unsave_post(self, post):
        if self.has_saved_post(post):
            self.saved_posts.remove(post)

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

    def has_liked_comment(self, comment):
        query = self.comment_likes.select().where(CommentLike.comment_id == comment.id)
        return db.session.scalar(query) is not None

    def like_comment(self, comment):
        if not self.has_liked_comment(comment):
            like = CommentLike(author=self, comment=comment)
            db.session.add(like)

    def unlike_comment(self, comment):
        if self.has_liked_comment(comment):
            query = self.comment_likes.select().where(CommentLike.comment_id == comment.id)
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
    
    groups: so.Mapped[list['Group']] = so.relationship(secondary=post_group, back_populates='posts')

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
    likes: so.Mapped[list['CommentLike']] = so.relationship(back_populates='comment', cascade='all, delete-orphan')

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

class CommentLike(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    comment_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Comment.id), index=True)

    author: so.Mapped[User] = so.relationship(back_populates='comment_likes')
    comment: so.Mapped[Comment] = so.relationship(back_populates='likes')

    def __repr__(self):
        return f'<CommentLike user:{self.user_id} comment:{self.comment_id}>'

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