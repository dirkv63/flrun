from flask_wtf import Form
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length


class PersonAdd(Form):
    name = StringField('Participant: ', validators=[DataRequired(), Length(1, 24)])
    submit = SubmitField('Submit')


class OrganizationAdd(Form):
    name = StringField('Naam', validators=[DataRequired(), Length(1, 24)])
    location = StringField('Plaats', validators=[DataRequired(), Length(1, 24)])
    datestamp = DateField('Datum')
    submit = SubmitField('OK')


class RaceAdd(Form):
    name = StringField('Naam', validators=[DataRequired(), Length(1, 12)])
    raceType = SelectField('Type Wedstrijd', coerce=int)
    submit = SubmitField('OK')


class ParticipantAdd(Form):
    name = SelectField('Naam', coerce=int)
    place = StringField('Plaats')
    time = StringField('Tijd')
    other = StringField('Opm.')
    prev_runner = SelectField('Aankomst na:', coerce=int)
    submit = SubmitField('OK')


class ParticipantRemove(Form):
    submit_ok = SubmitField('OK')
    submit_cancel = SubmitField('Cancel')


class Login(Form):
    username = StringField('Username', validators=[DataRequired(), Length(1, 16)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('OK')
