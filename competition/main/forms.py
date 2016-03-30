from flask_wtf import Form
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length


class RegisterForm(Form):
    name = StringField('Participant: ', validators=[DataRequired(), Length(1, 24)])
    submit = SubmitField('Submit')


class OrganisationNewForm(Form):
    name = StringField('Naam', validators=[DataRequired(), Length(1, 24)])
    location = StringField('Plaats', validators=[DataRequired(), Length(1, 24)])
    datestamp = DateField('Datum')
    submit = SubmitField('OK')


class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired(), Length(1, 16)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('OK')
