from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email
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
    submit = SubmitField('Kayıt Ol')

    def validate_username(self, username):
        user = db.session.scalar(db.select(User).filter_by(username=username.data))
        if user is not None:
            raise ValidationError('Lütfen farklı bir kullanıcı adı kullanın.')

    def validate_email(self, email):
        user = db.session.scalar(db.select(User).filter_by(email=email.data))
        if user is not None:
            raise ValidationError('Lütfen farklı bir e-posta adresi kullanın.')