import os
from werkzeug.utils import secure_filename
from flask import render_template, flash, redirect, url_for, request, current_app, session
from app import db
from app.main import bp
from app.main.forms import EditProfileForm, PostForm, CommentForm, VerifySecurityForm, EmptyForm
from app.models import User, Post, Comment, Notification
import random
import re
from flask_mail import Message
from app import mail
import sqlalchemy as sa
from flask_login import current_user, login_required
from datetime import datetime, timezone, timedelta

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

@bp.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        unread_count = db.session.scalar(sa.select(sa.func.count(Notification.id)).where(Notification.user_id == current_user.id, Notification.is_read == False))
        return dict(unread_notifications_count=unread_count or 0)
    return dict(unread_notifications_count=0)

@bp.app_template_filter('local_time')
def local_time_filter(dt, format='%d-%m-%Y %H:%M:%S'):
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Türkiye 2016'dan beri sabit UTC+3 kullanmaktadır.
    # Windows sistemlerde ZoneInfo paketi varsayılan olarak bulunmadığı için
    # timedelta ile doğrudan +3 saat ekleyerek basit ve kesin bir çözüm uyguluyoruz.
    local_dt = dt + timedelta(hours=3)
    return local_dt.strftime(format)

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    comment_form = CommentForm()
    edit_profile_form = EditProfileForm()
    empty_form = EmptyForm()
    if request.method == 'GET' and current_user.is_authenticated:
        edit_profile_form.username.data = current_user.username
        edit_profile_form.email.data = current_user.email
        edit_profile_form.about_me.data = current_user.about_me
        edit_profile_form.require_2fa.data = current_user.require_2fa
    
    if form.validate_on_submit():
        image_filename = None
        import uuid
        image_filenames = []
        for picture_file in request.files.getlist('image'):
            if picture_file and picture_file.filename:
                base_filename = secure_filename(picture_file.filename)
                name, ext = os.path.splitext(base_filename)
                if not name:
                    name = "image"
                unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
                picture_path = os.path.join(current_app.root_path, 'static', 'memory_pics', unique_filename)
                os.makedirs(os.path.dirname(picture_path), exist_ok=True)
                picture_file.save(picture_path)
                image_filenames.append(unique_filename)
                
        existing_images_data = request.form.get('existing_images') or form.existing_images.data
        if existing_images_data:
            existing_imgs = existing_images_data.split(',')
            for img in existing_imgs:
                if img.strip():
                    image_filenames.append(img.strip())
                
        if image_filenames:
            image_filename = ','.join(image_filenames)
        form_type = request.form.get('form_type')
        if form_type == 'mementgram':
            is_global = True
            comments_enabled = True
        else:
            is_global = False
            comments_enabled = False
            
        post = Post(body=form.post.data, image_file=image_filename, author=current_user, comments_enabled=comments_enabled, is_global=is_global)
        db.session.add(post)
        db.session.commit()
        flash('Anı başarıyla arşive kaldırıldı!')
        return redirect(url_for('main.index'))

    # SAYFALAMA (PAGINATION) MOTORU ve TARİHTE BUGÜN
    page = request.args.get('page', 1, type=int)
    g_page = request.args.get('g_page', 1, type=int)
    d_page = request.args.get('d_page', 1, type=int)
    posts_pagination = None
    on_this_day_posts = []
    
    if current_user.is_authenticated:
        query = current_user.posts.select().order_by(Post.timestamp.desc())
        posts_pagination = db.paginate(query, page=page, per_page=10, error_out=False)
        
        # Tarihte Bugün Algoritması (Aynı ay ve gün, farklı yıl)
        all_user_posts = db.session.scalars(current_user.posts.select()).all()
        today = datetime.now(timezone.utc)
        for p in all_user_posts:
            if p.timestamp.month == today.month and p.timestamp.day == today.day and p.timestamp.year < today.year:
                on_this_day_posts.append(p)

    discover_users = []
    discover_pagination = None
    if current_user.is_authenticated:
        query = db.select(User).filter(User.id != current_user.id)
        discover_pagination = db.paginate(query, page=d_page, per_page=10, error_out=False)
        discover_users = discover_pagination.items
    
    # Global akış için tüm anılar (Mementgram için - sayfalamalı)
    global_query = db.select(Post).filter_by(is_global=True).order_by(Post.timestamp.desc())
    global_pagination = db.paginate(global_query, page=g_page, per_page=10, error_out=False)
    all_global_posts = global_pagination.items
    
    return render_template('index.html', title='Ana Sayfa', form=form, comment_form=comment_form, edit_profile_form=edit_profile_form, empty_form=empty_form, posts=posts_pagination.items if posts_pagination else [], on_this_day_posts=on_this_day_posts, all_global_posts=all_global_posts, discover_users=discover_users, all_user_posts=all_user_posts, global_pagination=global_pagination, discover_pagination=discover_pagination, posts_pagination=posts_pagination)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(db.select(User).filter_by(username=username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().filter_by(is_global=True).order_by(Post.timestamp.desc())
    posts_pagination = db.paginate(query, page=page, per_page=10, error_out=False)
    comment_form = CommentForm()
    empty_form = EmptyForm()
    return render_template('user.html', user=user, posts_pagination=posts_pagination, comment_form=comment_form, empty_form=empty_form)

@bp.route('/post/<int:post_id>')
@login_required
def post(post_id):
    post = db.first_or_404(db.select(Post).filter_by(id=post_id))
    comment_form = CommentForm()
    empty_form = EmptyForm()
    return render_template('post.html', title='Anı Detayı', post=post, comment_form=comment_form, empty_form=empty_form)

@bp.route('/feed')
@login_required
def feed():
    page = request.args.get('page', 1, type=int)
    query = current_user.followed_posts()
    posts_pagination = db.paginate(query, page=page, per_page=10, error_out=False)
    comment_form = CommentForm()
    empty_form = EmptyForm()
    return render_template('feed.html', title='Akış', posts=posts_pagination.items, comment_form=comment_form, posts_pagination=posts_pagination, empty_form=empty_form)

@bp.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Geçersiz işlem (CSRF doğrulaması başarısız).')
        return redirect(request.referrer or url_for('main.index'))
        
    post = db.session.get(Post, post_id)
    if post is None or post.author != current_user:
        from flask import abort
        abort(403)
    images_to_check = []
    if post.image_file:
        images_to_check = [img.strip() for img in post.image_file.split(',') if img.strip()]

    db.session.delete(post)
    db.session.commit()
    
    # Güvenli Fotoğraf Silme Mantığı
    for img in images_to_check:
        usage_count = db.session.scalar(
            sa.select(sa.func.count(Post.id)).where(Post.image_file.like(f"%{img}%"))
        )
        if usage_count == 0:
            img_path = os.path.join(current_app.root_path, 'static/memory_pics', img)
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except Exception as e:
                    pass

    flash('Anı başarıyla silindi.')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    post = db.session.get(Post, post_id)
    if post is None or not post.comments_enabled:
        flash('Bu anı yorumlara kapalıdır veya bulunamadı.')
        return redirect(request.referrer or url_for('main.index'))
    
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, author=current_user, post=post)
        db.session.add(comment)
        if post.author != current_user:
            notif = Notification(user=post.author, message=f"{current_user.username} bir anına yorum yaptı.", link=url_for('main.post', post_id=post.id))
            db.session.add(notif)
        db.session.commit()
        flash('Yorumun eklendi!')
    return redirect(request.referrer or url_for('main.index'))

def send_security_email(user, code):
    import os
    if not os.environ.get('MAIL_USERNAME'):
        print(f"\n==========\n[{user.email} için Güvenlik Doğrulama Kodu]: {code}\n==========\n", flush=True)
    else:
        msg = Message('MementOS Güvenlik Doğrulama Kodu',
                      sender=os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@mementos.com',
                      recipients=[user.email])
        msg.html = render_template('email_security_code.html', code=code)
        mail.send(msg)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        if form.profile_pic.data:
            picture_file = form.profile_pic.data
            _, f_ext = os.path.splitext(picture_file.filename)
            picture_filename = current_user.username + f_ext
            picture_path = os.path.join(current_app.root_path, 'static', 'profile_pics', picture_filename)
            os.makedirs(os.path.dirname(picture_path), exist_ok=True)
            picture_file.save(picture_path)
            current_user.profile_pic = picture_filename
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.require_2fa = form.require_2fa.data
        
        email_changed = form.email.data != current_user.email
        password_changed = bool(form.new_password.data)
        
        if email_changed or password_changed:
            code = str(random.randint(100000, 999999))
            session['security_code'] = code
            session['pending_email'] = form.email.data if email_changed else None
            session['pending_password'] = form.new_password.data if password_changed else None
            
            send_security_email(current_user, code)
            db.session.commit() # Save username, about_me etc.
            flash('Güvenlik ayarlarınızı değiştirmek için mevcut e-postanıza bir onay kodu gönderdik.')
            return redirect(url_for('main.verify_security'))
            
        db.session.commit()
        flash('Değişiklikleriniz kaydedildi.')
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.about_me.data = current_user.about_me
        form.require_2fa.data = current_user.require_2fa
    return render_template('edit_profile.html', title='Profili Düzenle', form=form)

@bp.route('/verify_security', methods=['GET', 'POST'])
@login_required
def verify_security():
    if 'security_code' not in session:
        return redirect(url_for('main.index'))
        
    form = VerifySecurityForm()
    if form.validate_on_submit():
        clean_code = re.sub(r'\D', '', form.code.data)
        if clean_code == session['security_code']:
            if session.get('pending_email'):
                current_user.email = session['pending_email']
            if session.get('pending_password'):
                current_user.set_password(session['pending_password'])
            
            db.session.commit()
            
            # Temizlik
            session.pop('security_code', None)
            session.pop('pending_email', None)
            session.pop('pending_password', None)
            
            flash('Güvenlik ayarlarınız başarıyla güncellendi!')
            return redirect(url_for('main.index'))
        else:
            flash('Hatalı doğrulama kodu. Lütfen tekrar deneyin.')
            
    return render_template('verify_security.html', title='Güvenlik Doğrulaması', form=form)

@bp.route('/cancel_security_update')
@login_required
def cancel_security_update():
    session.pop('security_code', None)
    session.pop('pending_email', None)
    session.pop('pending_password', None)
    flash('Güvenlik güncelleme işlemi iptal edildi.')
    return redirect(url_for('main.index'))

@bp.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like(post_id):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Geçersiz işlem (CSRF doğrulaması başarısız).')
        return redirect(request.referrer or url_for('main.index'))
        
    post = db.session.get(Post, post_id)
    if post is None:
        flash('Anı bulunamadı.')
        return redirect(request.referrer or url_for('main.index'))
    if current_user.has_liked_post(post):
        current_user.unlike(post)
    else:
        current_user.like(post)
        if post.author != current_user:
            notif = Notification(user=post.author, message=f"{current_user.username} bir anını beğendi.", link=url_for('main.post', post_id=post.id))
            db.session.add(notif)
    db.session.commit()
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Geçersiz işlem (CSRF doğrulaması başarısız).')
        return redirect(request.referrer or url_for('main.index'))
        
    user = db.session.scalar(db.select(User).filter_by(username=username))
    if user is None:
        flash(f'Kullanıcı {username} bulunamadı.')
        return redirect(request.referrer or url_for('main.index'))
    if user == current_user:
        flash('Kendinizi takip edemezsiniz!')
        return redirect(request.referrer or url_for('main.index'))
    current_user.follow(user)
    
    notif = Notification(user=user, message=f"{current_user.username} seni takip etmeye başladı.", link=url_for('main.user', username=current_user.username))
    db.session.add(notif)
    
    db.session.commit()
    flash(f'{username} artık takip ediliyor!')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Geçersiz işlem (CSRF doğrulaması başarısız).')
        return redirect(request.referrer or url_for('main.index'))
        
    user = db.session.scalar(db.select(User).filter_by(username=username))
    if user is None:
        flash(f'Kullanıcı {username} bulunamadı.')
        return redirect(request.referrer or url_for('main.index'))
    if user == current_user:
        flash('Kendinizi takipten çıkamazsınız!')
        return redirect(request.referrer or url_for('main.index'))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'{username} takipten çıkarıldı.')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Geçersiz işlem (CSRF doğrulaması başarısız).')
        return redirect(request.referrer or url_for('main.index'))
        
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        flash('Yorum bulunamadı.')
        return redirect(request.referrer or url_for('main.index'))
    if comment.author != current_user and comment.post.author != current_user:
        from flask import abort
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Yorum silindi.')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/notifications')
@login_required
def notifications():
    query = current_user.notifications.select().order_by(Notification.timestamp.desc())
    page = request.args.get('page', 1, type=int)
    pagination = db.paginate(query, page=page, per_page=20, error_out=False)
    
    unread = db.session.scalars(current_user.notifications.select().filter_by(is_read=False)).all()
    for notif in unread:
        notif.is_read = True
    if unread:
        db.session.commit()
        
    return render_template('notifications.html', title='Bildirimler', notifications=pagination.items, pagination=pagination)