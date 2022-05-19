from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField('Post')


class RegisterForm(FlaskForm):
    name = StringField('Enter yur full name', validators=[DataRequired()])
    email = StringField('Enter yur email', validators=[DataRequired()])
    password = PasswordField('Enter yur password', validators=[DataRequired()])
    submit = SubmitField("Register Me")
class LoginForm(FlaskForm):
    username = StringField('Enter your email')
    password = PasswordField('Enter your password')
    submit = SubmitField('Log In')

class CommentForm(FlaskForm):
    body = CKEditorField('Type your comment')
    submit = SubmitField('Comment')
