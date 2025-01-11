from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed
from wtforms import SelectField

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=4, max=100)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    gender = SelectField('Gênero', choices=[('Masculino', 'Masculino'), ('Feminino', 'Feminino')], default='Masculino')
    avatar = FileField('Avatar', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Cadastrar')

class PostForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired()])
    content = TextAreaField('Conteúdo', validators=[DataRequired()])
    submit = SubmitField('Publicar')
