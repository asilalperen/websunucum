from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User
from app import db

class LoginForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    remember_me = BooleanField('Beni Hatırla')
    submit = SubmitField('Giriş Yap')

class RegistrationForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired()])
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    password_again = PasswordField('Şifre Tekrar', validators=[DataRequired(), EqualTo('password', message='Şifreler eşleşmelidir.')])
    require_2fa = BooleanField('Her yeni girişimde e-posta ile doğrula (2FA)')
    submit = SubmitField('Kayıt Ol')

class VerifyEmailForm(FlaskForm):
    code = StringField('Doğrulama Kodu', validators=[DataRequired()])
    submit = SubmitField('Doğrula')

    def validate_username(self, username):
        user = db.session.scalar(db.select(User).filter_by(username=username.data))
        if user is not None:
            raise ValidationError('Lütfen farklı bir kullanıcı adı kullanın.')

    def validate_email(self, email):
        user = db.session.scalar(db.select(User).filter_by(email=email.data))
        if user is not None:
            raise ValidationError('Lütfen farklı bir e-posta adresi kullanın.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    submit = SubmitField('Şifre Sıfırlama Bağlantısı İste')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Yeni Şifre', validators=[DataRequired()])
    password_again = PasswordField('Yeni Şifre Tekrar', validators=[DataRequired(), EqualTo('password', message='Şifreler eşleşmelidir.')])
    submit = SubmitField('Şifremi Sıfırla')