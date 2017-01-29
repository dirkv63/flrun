from flask_wtf import FlaskForm as Form
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField, RadioField
from wtforms.fields.html5 import DateField
import wtforms.validators as wtv


class PersonAdd(Form):
    name = StringField('Naam: ', validators=[wtv.InputRequired(), wtv.Length(1, 24)])
    mf = RadioField(choices=[('man', 'man'), ('vrouw', 'vrouw')], default='man', validators=[wtv.InputRequired()])
    born = DateField('Geboren: ', validators=[wtv.Optional()])
    submit = SubmitField('OK')


class OrganizationAdd(Form):
    name = StringField('Naam', validators=[wtv.InputRequired(), wtv.Length(1, 24)])
    location = StringField('Plaats', validators=[wtv.InputRequired(), wtv.Length(1, 24)])
    datestamp = DateField('Datum')
    org_type = RadioField(choices=[(1, 'Wedstrijd'), (2, 'Deelname')], default=1, coerce=int,
                          validators=[wtv.InputRequired()])
    submit = SubmitField('OK')


class RaceAdd(Form):
    name = StringField('Naam', validators=[wtv.InputRequired(), wtv.Length(1, 12)])
    # raceType = SelectField('Type Wedstrijd', coerce=int)
    raceType = BooleanField('Hoofdwedstrijd')
    submit = SubmitField('OK')


class ParticipantAdd(Form):
    """
    Form to Add a participant to a race. Timefield is not included. It is not part of wtforms 2 (wait for wtforms
    version 3), it is currently not used and it may not be required in the future.
    """
    name = SelectField('Naam', coerce=str)
    pos = StringField('Plaats')
    remark = StringField('Opm.')
    prev_runner = SelectField('Aankomst na:', coerce=str)
    submit = SubmitField('OK')


class ParticipantEdit(Form):
    pos = StringField('Plaats')
    remark = StringField('Opm.')
    submit = SubmitField('OK')


class ParticipantRemove(Form):
    submit_ok = SubmitField('OK')
    submit_cancel = SubmitField('Cancel')


class Login(Form):
    username = StringField('Username', validators=[wtv.InputRequired(), wtv.Length(1, 16)])
    password = PasswordField('Password', validators=[wtv.InputRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('OK')
