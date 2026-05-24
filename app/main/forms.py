from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed

class EditProfileForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired()])
    about_me = TextAreaField('Hakkımda', validators=[Length(min=0, max=140)])
    profile_pic = FileField('Profil Fotoğrafı', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Kaydet')

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