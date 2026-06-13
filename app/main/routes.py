import os
from werkzeug.utils import secure_filename
from flask import render_template, flash, redirect, url_for, request, current_app, session
from app import db
from app.main import bp
from app.main.forms import EditProfileForm, PostForm, CommentForm, VerifySecurityForm, EmptyForm
from app.models import User, Post, Comment, Notification, Group, Achievement
from app.achievements import check_achievements
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
    if current_user.is_authenticated:
        form.groups.choices = [(g.id, g.name) for g in current_user.groups]
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
        
        # Seçilen grupları posta ekle veya tek gruptaysa otomatik ekle
        if current_user.groups:
            if len(current_user.groups) > 1 and form.groups.data:
                for group_id in form.groups.data:
                    g = db.session.get(Group, group_id)
                    if g and g in current_user.groups:
                        post.groups.append(g)
                # Eğer birden fazla gruba üye ama hiçbirini seçmediyse, formun validasyonuna takılmamış olabilir (boş bırakmış).
                # Güvenlik olarak en azından bir atama yapalım (veya hepsine atalım).
                if not post.groups:
                    for g in current_user.groups:
                        post.groups.append(g)
            else:
                # Sadece 1 grubundaysa (ya da hiçbiri seçilmediyse fallback)
                for g in current_user.groups:
                    post.groups.append(g)
                    
        db.session.commit()
        check_achievements(current_user)
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
        if current_user.is_admin:
            query = db.select(User).filter(User.id != current_user.id)
        else:
            group_ids = [g.id for g in current_user.groups]
            if group_ids:
                query = db.select(User).join(User.groups).filter(
                    User.id != current_user.id,
                    Group.id.in_(group_ids)
                ).distinct()
            else:
                query = db.select(User).filter(sa.sql.false())
        discover_pagination = db.paginate(query, page=d_page, per_page=10, error_out=False)
        discover_users = discover_pagination.items
    
    # Global akış için tüm anılar (Mementgram için - sayfalamalı)
    if current_user.is_authenticated and not current_user.is_admin:
        group_ids = [g.id for g in current_user.groups]
        if group_ids:
            global_query = db.select(Post).join(Post.groups).filter(
                Post.is_global == True,
                Group.id.in_(group_ids)
            ).distinct().order_by(Post.timestamp.desc())
        else:
            global_query = db.select(Post).filter(sa.sql.false())
    else:
        global_query = db.select(Post).filter_by(is_global=True).order_by(Post.timestamp.desc())
        
    global_pagination = db.paginate(global_query, page=g_page, per_page=10, error_out=False)
    all_global_posts = global_pagination.items
    # Podyum (Liderlik Tablosu) verisi hesaplama
    group_leaderboards = {}
    if current_user.is_authenticated:
        groups_to_check = db.session.scalars(db.select(Group)).all() if current_user.is_admin else current_user.groups
        for g in groups_to_check:
            sorted_users = sorted(g.users, key=lambda x: x.points, reverse=True)[:3]
            group_leaderboards[g.id] = {
                'name': g.name,
                'top_users': sorted_users
            }

    return render_template('index.html', title='Ana Sayfa', form=form, comment_form=comment_form, edit_profile_form=edit_profile_form, empty_form=empty_form, posts=posts_pagination.items if posts_pagination else [], on_this_day_posts=on_this_day_posts, all_global_posts=all_global_posts, discover_users=discover_users, all_user_posts=all_user_posts, global_pagination=global_pagination, discover_pagination=discover_pagination, posts_pagination=posts_pagination, group_leaderboards=group_leaderboards)

@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(db.select(User).filter_by(username=username))
    
    # İzolasyon Kontrolü: Admin değilse ve kendisi değilse ortak grup var mı diye bak
    if not current_user.is_admin and user != current_user:
        my_group_ids = set([g.id for g in current_user.groups])
        their_group_ids = set([g.id for g in user.groups])
        if not my_group_ids.intersection(their_group_ids):
            from flask import abort
            abort(404)
            
    page = request.args.get('page', 1, type=int)
    
    if current_user.is_admin or user == current_user:
        query = user.posts.select().filter_by(is_global=True).order_by(Post.timestamp.desc())
    else:
        # Sadece ortak gruplara atılan gönderileri görsün
        my_group_ids = [g.id for g in current_user.groups]
        query = user.posts.select().join(Post.groups).filter(
            Post.is_global == True,
            Group.id.in_(my_group_ids)
        ).distinct().order_by(Post.timestamp.desc())
        
    posts_pagination = db.paginate(query, page=page, per_page=10, error_out=False)
    comment_form = CommentForm()
    empty_form = EmptyForm()
    all_achievements = db.session.scalars(db.select(Achievement).order_by(Achievement.points)).all()
    return render_template('user.html', user=user, posts_pagination=posts_pagination, comment_form=comment_form, empty_form=empty_form, all_achievements=all_achievements)

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
    if post is None or (post.author != current_user and not current_user.is_admin):
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
        comment_body = form.body.data
        comment = Comment(body=comment_body, author=current_user, post=post)
        db.session.add(comment)
        
        # Etiketleme (Mentions) kontrolü
        import re
        mentions = re.findall(r'@([a-zA-Z0-9_]+)', comment_body)
        for username in set(mentions):
            if username.lower() != current_user.username.lower():
                user_to_notify = db.session.scalar(db.select(User).where(User.username.ilike(username)))
                if user_to_notify:
                    mention_notif = Notification(user=user_to_notify, message=f"{current_user.username} senden bir yorumda bahsetti.", link=url_for('main.post', post_id=post.id))
                    db.session.add(mention_notif)

        if post.author != current_user:
            notif = Notification(user=post.author, message=f"{current_user.username} bir anına yorum yaptı.", link=url_for('main.post', post_id=post.id))
            db.session.add(notif)
        db.session.commit()
        check_achievements(current_user)
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
    check_achievements(current_user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
        return {'liked': current_user.has_liked_post(post), 'like_count': len(post.likes)}
        
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/save_post/<int:post_id>', methods=['POST'])
@login_required
def save_post(post_id):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Geçersiz işlem (CSRF doğrulaması başarısız).')
        return redirect(request.referrer or url_for('main.index'))
        
    post = db.session.get(Post, post_id)
    if post is None:
        flash('Anı bulunamadı.')
        return redirect(request.referrer or url_for('main.index'))
    if current_user.has_saved_post(post):
        current_user.unsave_post(post)
    else:
        current_user.save_post(post)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
        return {'saved': current_user.has_saved_post(post)}
        
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/saved_posts')
@login_required
def saved_posts():
    empty_form = EmptyForm()
    from app.main.forms import CommentForm
    comment_form = CommentForm()
    page = request.args.get('page', 1, type=int)
    query = current_user.saved_posts.select().order_by(Post.timestamp.desc())
    posts_pagination = db.paginate(query, page=page, per_page=10, error_out=False)
    posts = posts_pagination.items
    return render_template('saved_posts.html', title='Kaydedilenler', posts=posts, empty_form=empty_form, comment_form=comment_form, pagination=posts_pagination)

@bp.route('/like_comment/<int:comment_id>', methods=['POST'])
@login_required
def like_comment(comment_id):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Geçersiz işlem (CSRF doğrulaması başarısız).')
        return redirect(request.referrer or url_for('main.index'))
        
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        flash('Yorum bulunamadı.')
        return redirect(request.referrer or url_for('main.index'))
    if current_user.has_liked_comment(comment):
        current_user.unlike_comment(comment)
    else:
        current_user.like_comment(comment)
        if comment.author != current_user:
            notif = Notification(user=comment.author, message=f"{current_user.username} bir yorumunu beğendi.", link=url_for('main.post', post_id=comment.post_id))
            db.session.add(notif)
    db.session.commit()
    check_achievements(current_user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
        return {'liked': current_user.has_liked_comment(comment), 'like_count': len(comment.likes)}
        
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
    if comment.author != current_user and comment.post.author != current_user and not current_user.is_admin:
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

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/admin')
@login_required
@admin_required
def admin_panel():
    unapproved_users = db.session.scalars(db.select(User).filter_by(is_approved=False).order_by(User.id.desc())).all()
    approved_users = db.session.scalars(db.select(User).filter_by(is_approved=True).order_by(User.id.desc())).all()
    groups = db.session.scalars(db.select(Group).order_by(Group.name)).all()
    form = EmptyForm()
    group_form = GroupForm()
    return render_template('admin_panel.html', title='Admin Paneli', unapproved_users=unapproved_users, approved_users=approved_users, groups=groups, form=form, group_form=group_form)

@bp.route('/admin/approve/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        flash('Yetkiniz yok.')
        return redirect(url_for('main.index'))
    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Geçersiz işlem.')
        return redirect(url_for('main.admin_panel'))
    user = db.session.get(User, user_id)
    if user and user != current_user:
        user.is_approved = not user.is_approved
        db.session.commit()
        if user.is_approved:
            flash(f'{user.username} adlı kullanıcı onaylandı (Ban açıldı).')
        else:
            flash(f'{user.username} adlı kullanıcı YASAKLANDI (Banlandı).')
    return redirect(url_for('main.admin_panel'))

@bp.route('/admin/reset_password/<int:user_id>', methods=['POST'])
@login_required
def admin_reset_password(user_id):
    if not current_user.is_admin:
        flash('Yetkiniz yok.')
        return redirect(url_for('main.index'))
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.get(User, user_id)
        if user:
            user.set_password('123456')
            db.session.commit()
            flash(f'{user.username} adlı kullanıcının şifresi başarıyla "123456" olarak sıfırlandı.')
    return redirect(url_for('main.admin_panel'))

@bp.route('/admin/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    form = EmptyForm()
    if not form.validate_on_submit():
        flash('Geçersiz işlem.')
        return redirect(url_for('main.admin_panel'))
    user = db.session.get(User, user_id)
    if user:
        if user == current_user:
            flash('Kendinizi silemezsiniz!')
        else:
            db.session.delete(user)
            db.session.commit()
            flash(f'{user.username} adlı kullanıcı silindi.')
    return redirect(url_for('main.admin_panel'))

from app.main.forms import GroupForm, UserGroupForm

@bp.route('/admin/create_group', methods=['POST'])
@login_required
@admin_required
def create_group():
    form = GroupForm()
    if form.validate_on_submit():
        if db.session.scalar(db.select(Group).filter_by(name=form.name.data)):
            flash('Bu isimde bir grup zaten var.')
        else:
            g = Group(name=form.name.data)
            db.session.add(g)
            db.session.commit()
            flash(f'{g.name} adlı grup oluşturuldu!')
    return redirect(url_for('main.admin_panel'))

@bp.route('/admin/delete_group/<int:group_id>', methods=['POST'])
@login_required
@admin_required
def delete_group(group_id):
    form = EmptyForm()
    if form.validate_on_submit():
        g = db.session.get(Group, group_id)
        if g:
            db.session.delete(g)
            db.session.commit()
            flash('Grup silindi.')
    return redirect(url_for('main.admin_panel'))



@bp.route('/admin/manage_group_users/<int:group_id>', methods=['POST'])
@login_required
@admin_required
def manage_group_users(group_id):
    g = db.session.get(Group, group_id)
    if g:
        user_ids = request.form.getlist('user_ids', type=int)
        g.users.clear()
        for uid in user_ids:
            u = db.session.get(User, uid)
            if u:
                g.users.append(u)
        db.session.commit()
        for u in g.users:
            check_achievements(u)
        flash(f'{g.name} grubunun üyeleri güncellendi.')
    return redirect(url_for('main.admin_panel'))

import os
from flask import current_app

@bp.context_processor
def inject_global_radio():
    radio_url = None
    try:
        radio_path = os.path.join(current_app.root_path, 'global_song.txt')
        if os.path.exists(radio_path):
            with open(radio_path, 'r', encoding='utf-8') as f:
                radio_url = f.read().strip()
    except Exception as e:
        pass
    return dict(global_spotify_url=radio_url)

import re

@bp.route('/admin/set_radio', methods=['POST'])
@login_required
def set_radio():
    if not current_user.is_admin:
        flash('Yetkiniz yok.')
        return redirect(url_for('main.index'))
    
    spotify_link = request.form.get('spotify_link', '').strip()
    radio_path = os.path.join(current_app.root_path, 'global_song.txt')
    
    try:
        if not spotify_link:
            if os.path.exists(radio_path):
                os.remove(radio_path)
            flash('Mementgram Radyosu kapatıldı.')
        else:
            if 'open.spotify.com' in spotify_link and '/embed/' not in spotify_link:
                # Regex ile track/playlist türünü ve ID'sini ayıklıyoruz (intl-tr vb. atlamak için)
                match = re.search(r'(track|playlist|album|artist|episode)/([a-zA-Z0-9]+)', spotify_link)
                if match:
                    embed_url = f"https://open.spotify.com/embed/{match.group(1)}/{match.group(2)}?utm_source=generator&theme=0"
                    with open(radio_path, 'w', encoding='utf-8') as f:
                        f.write(embed_url)
                    flash('Mementgram Radyosu güncellendi!')
                else:
                    flash('Lütfen geçerli bir Spotify linki girin.')
            elif '/embed/' in spotify_link:
                with open(radio_path, 'w', encoding='utf-8') as f:
                    f.write(spotify_link)
                flash('Mementgram Radyosu güncellendi!')
            else:
                flash('Lütfen geçerli bir Spotify linki girin.')
    except Exception as e:
        flash('Radyo güncellenirken bir hata oluştu.')
        
    return redirect(url_for('main.admin_panel'))

@bp.route('/api/mentionable_users')
@login_required
def mentionable_users():
    if current_user.is_admin:
        users = db.session.scalars(db.select(User)).all()
    else:
        group_ids = [g.id for g in current_user.groups]
        if not group_ids:
            return {'users': []}
        users = db.session.scalars(db.select(User).join(User.groups).filter(Group.id.in_(group_ids)).distinct()).all()
        
    return {'users': [{'username': u.username, 'avatar': u.avatar(30)} for u in users if u != current_user]}