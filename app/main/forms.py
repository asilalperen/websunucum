from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
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
    submit = SubmitField('Sisteme Kaydet')