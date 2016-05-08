from flask_wtf import Form
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField, RadioField
from wtforms.fields.html5 import DateField
import wtforms.validators as wtv


class PersonAdd(Form):
    name = StringField('Participant: ', validators=[wtv.InputRequired(), wtv.Length(1, 24)])
    mf = RadioField(choices=[('man', 'man'), ('vrouw', 'vrouw')], default='man', validators=[wtv.InputRequired()])
    born = DateField('Geboren: ', validators=[wtv.Optional()])
    submit = SubmitField('Submit')


class OrganizationAdd(Form):
    name = StringField('Naam', validators=[wtv.InputRequired(), wtv.Length(1, 24)])
    location = StringField('Plaats', validators=[wtv.InputRequired(), wtv.Length(1, 24)])
    datestamp = DateField('Datum')
    submit = SubmitField('OK')


class RaceAdd(Form):
    name = StringField('Naam', validators=[wtv.InputRequired(), wtv.Length(1, 12)])
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
    username = StringField('Username', validators=[wtv.InputRequired(), wtv.Length(1, 16)])
    password = PasswordField('Password', validators=[wtv.InputRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('OK')
