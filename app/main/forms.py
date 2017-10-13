from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, FileField, ValidationError
from wtforms.validators import Required, Length, Email, Regexp
from ..models import Role, User
from flask_pagedown.fields import PageDownField
from flask import current_app

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')

class EditProfileForm(FlaskForm):
    real_name = StringField("Real name", validators=[Length(0,64)])
    location = StringField("Location", validators=[Length(0,64)])
    about_me = StringField("About me")
    submit = SubmitField("Submit")

class EditProfileAdminForm(FlaskForm):
    email = StringField("Email", validators=[Required(), Length(1, 64),
                                           Email()])
    username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots or underscores')])
    role = SelectField('Role', coerce=int)
    real_name = StringField("Real name", validators=[Length(0,64)])
    location = StringField("Location", validators=[Length(0,64)])
    about_me = StringField("About me")
    submit = SubmitField("Submit")

    def __init__(self, user, *args, **kw):
        super(EditProfileAdminForm,self).__init__(*args,**kw)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and  User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class PostForm(FlaskForm):
    body = PageDownField("What's on your mind?", validators=[Required()])
    submit = SubmitField("Submit")


class EditPostForm(FlaskForm):
    body = PageDownField("What's on your mind?", validators=[Required()])
    submit = SubmitField("Submit")


class CommentForm(FlaskForm):
    body = PageDownField("Enter your comment", validators=[Required()])
    submit = SubmitField("Submit")

class ChangeAvatarForm(FlaskForm):
    avatar = FileField('Profile picture')
    submit = SubmitField("Upload")

    def validate_avatar(self, field):
        filename = field.data.filename
        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        ALLOWED_EXTENSIONS = ['png','jpg','jpeg','gif','PNG','JPG','JPEG','GIF']
        flag = '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS
        if not flag:
            raise ValidationError('Invalid picture format!')
        #size = len(field.data.read())
        #current_app.logger.warning(size)
        #if size > 1024*1024:
        #    raise ValidationError('Avatar size has to be under 1MB!')
