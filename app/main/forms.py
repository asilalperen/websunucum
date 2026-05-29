from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, HiddenField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_wtf.file import FileField, FileAllowed

class EditProfileForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired()])
    email = StringField('E-posta (Değiştirmek istersen)', validators=[DataRequired(), Email()])
    about_me = TextAreaField('Hakkımda', validators=[Length(min=0, max=140)])
    profile_pic = FileField('Profil Fotoğrafı', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    require_2fa = BooleanField('Her girişte e-posta ile doğrula (2FA)')
    new_password = PasswordField('Yeni Şifre (Değiştirmek istemiyorsan boş bırak)')
    new_password_again = PasswordField('Yeni Şifre Tekrar', validators=[EqualTo('new_password', message='Şifreler eşleşmelidir.')])
    submit = SubmitField('Kaydet')

class VerifySecurityForm(FlaskForm):
    code = StringField('Doğrulama Kodu', validators=[DataRequired()])
    submit = SubmitField('Onayla ve Değiştir')

# BİZİM MEŞHUR ANI (TIMESTASH) FORMUMUZ
class PostForm(FlaskForm):
    post = TextAreaField('Anı', validators=[DataRequired()])
    image = FileField('Fotoğraf', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    existing_images = HiddenField('Mevcut Fotoğraflar')
    comments_enabled = BooleanField('Yoruma İzin Ver', default=True)
    submit = SubmitField('Sisteme Kaydet')

class CommentForm(FlaskForm):
    body = TextAreaField('Yorumun', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Gönder')