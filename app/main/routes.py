import os
from werkzeug.utils import secure_filename
from flask import render_template, flash, redirect, url_for, request, current_app
from app import db
from app.main import bp
from app.main.forms import EditProfileForm, PostForm
from app.models import User, Post
from flask_login import current_user, login_required
from datetime import datetime, timezone

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    form = PostForm()
    
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
                picture_path = os.path.join(current_app.root_path, 'static/memory_pics', unique_filename)
                picture_file.save(picture_path)
                image_filenames.append(unique_filename)
                
        if image_filenames:
            image_filename = ','.join(image_filenames)
            
        post = Post(body=form.post.data, image_file=image_filename, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Anı başarıyla arşive kaldırıldı!')
        return redirect(url_for('main.index'))

    # SAYFALAMA (PAGINATION) MOTORU ve TARİHTE BUGÜN
    page = request.args.get('page', 1, type=int) 
    posts_pagination = None
    on_this_day_posts = []
    
    if current_user.is_authenticated:
        query = current_user.posts.select().order_by(Post.timestamp.desc())
        posts_pagination = db.paginate(query, page=page, per_page=10, error_out=False)
        
        # Tarihte Bugün Algoritması (Aynı ay ve gün, farklı yıl)
        all_posts = db.session.scalars(current_user.posts.select()).all()
        today = datetime.now(timezone.utc)
        for p in all_posts:
            if p.timestamp.month == today.month and p.timestamp.day == today.day and p.timestamp.year < today.year:
                on_this_day_posts.append(p)

    users = db.session.scalars(db.select(User).limit(5)).all()
    
    return render_template('index.html', title='Ana Sayfa', users=users, form=form, posts=posts_pagination.items if posts_pagination else [], on_this_day_posts=on_this_day_posts)

@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(db.select(User).filter_by(username=username))
    return render_template('user.html', user=user)

@bp.route('/feed')
@login_required
def feed():
    page = request.args.get('page', 1, type=int)
    query = current_user.followed_posts()
    posts_pagination = db.paginate(query, page=page, per_page=10, error_out=False)
    return render_template('feed.html', title='Akış', posts=posts_pagination.items)

@bp.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = db.session.get(Post, post_id)
    if post is None or post.author != current_user:
        from flask import abort
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Anı başarıyla silindi.')
    return redirect(url_for('main.index'))

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        if form.profile_pic.data:
            picture_file = form.profile_pic.data
            _, f_ext = os.path.splitext(picture_file.filename)
            picture_filename = current_user.username + f_ext
            picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_filename)
            picture_file.save(picture_path)
            current_user.profile_pic = picture_filename
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Değişiklikleriniz kaydedildi.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Profili Düzenle', form=form)