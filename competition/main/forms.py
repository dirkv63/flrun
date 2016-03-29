from flask_wtf import Form
from wtforms import StringField, SubmitField
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
