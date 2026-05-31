from flask import render_template, redirect, url_for, flash, request, session
from urllib.parse import urlsplit
from flask_login import login_user, logout_user, current_user
import random
import re
from flask_mail import Message
from app import db, mail
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, VerifyEmailForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User

def send_verification_email(user):
    code = str(random.randint(100000, 999999))
    user.verification_code = code
    db.session.commit()
    
    import os
    if not os.environ.get('MAIL_USERNAME'):
        print(f"\n==========\n[{user.username} için Doğrulama Kodu]: {code}\n==========\n", flush=True)
    else:
        msg = Message('MementOS Doğrulama Kodu',
                      sender=os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@mementos.com',
                      recipients=[user.email])
        msg.body = f'MementOS doğrulama kodunuz: {code}'
        msg.html = render_template('email_template.html', code=code)
        mail.send(msg)

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    
    import os
    if not os.environ.get('MAIL_USERNAME'):
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        print(f"\n==========\n[{user.email} için Şifre Sıfırlama Linki]: {reset_url}\n==========\n", flush=True)
    else:
        msg = Message('MementOS Şifre Sıfırlama',
                      sender=os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@mementos.com',
                      recipients=[user.email])
        msg.html = render_template('email_reset_password.html', token=token)
        mail.send(msg)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).filter_by(username=form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Geçersiz kullanıcı adı veya şifre')
            return redirect(url_for('auth.login'))
            
        if not user.is_verified:
            send_verification_email(user)
            session['verify_user_id'] = user.id
            flash('Hesabınız doğrulanmamış. Lütfen doğrulama kodunu giriniz.')
            return redirect(url_for('auth.verify_email'))
            
        if user.require_2fa and not form.remember_me.data:
            send_verification_email(user)
            session['verify_user_id'] = user.id
            session['remember_me'] = form.remember_me.data
            flash('İki aşamalı doğrulama: Lütfen doğrulama kodunu giriniz.')
            return redirect(url_for('auth.verify_email'))
            
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('login.html', title='Giriş Yap', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, require_2fa=form.require_2fa.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        send_verification_email(user)
        session['verify_user_id'] = user.id
        flash('Lütfen doğrulama kodunu giriniz.')
        return redirect(url_for('auth.verify_email'))
    return render_template('register.html', title='Kayıt Ol', form=form)

@bp.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    user_id = session.get('verify_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
        
    user = db.session.get(User, user_id)
    if not user:
        return redirect(url_for('auth.login'))
        
    form = VerifyEmailForm()
    if form.validate_on_submit():
        # Yapıştırma hatalarını önlemek için sadece rakamları alıyoruz
        clean_code = re.sub(r'\D', '', form.code.data)
        if clean_code == user.verification_code:
            user.is_verified = True
            user.verification_code = None
            db.session.commit()
            
            remember = session.pop('remember_me', False)
            session.pop('verify_user_id', None)
            
            login_user(user, remember=remember)
            flash('Doğrulama başarılı! Hoş geldiniz.')
            return redirect(url_for('main.index'))
        else:
            flash('Hatalı doğrulama kodu. Lütfen tekrar deneyin.')
            
    return render_template('verify_email.html', title='E-posta Doğrulama', form=form, user=user)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).filter_by(email=form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Şifre sıfırlama yönergeleri e-posta adresinize gönderildi. (Geliştirici Notu: Siyah terminal ekranını kontrol edin)')
        return redirect(url_for('auth.login'))
    return render_template('reset_password_request.html', title='Şifre Sıfırlama Talebi', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Şifre sıfırlama bağlantısı geçersiz veya süresi dolmuş.')
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Şifreniz başarıyla sıfırlandı. Lütfen giriş yapın.')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html', title='Şifre Sıfırla', form=form)