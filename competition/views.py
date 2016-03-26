from .models import Person, Organization, get_organizations, get_participants
from flask import Flask, request, flash, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

app = Flask(__name__)
bootstrap = Bootstrap(app)


class RegisterForm(Form):
    name = StringField('Participant: ', validators=[DataRequired(), Length(1, 24)])
    submit = SubmitField('Submit')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/participant/register', methods=['GET', 'POST'])
def register():
    name = None
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        if Person(name).register():
            flash(name + ' created as a Person (participant)')
        else:
            flash(name + ' does exist already, not created.')
    return render_template('register.html', form=form, name=name)


@app.route('/participant/list')
def participant_list():
    participants = get_participants()
    app.logger.debug("Participants: {participants}".format(participants=participants))
    return render_template('display_participants.html', participants=participants)


@app.route('/organization', methods=['GET', 'POST'])
def organization():

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        datestamp = request.form['date']

        if Organization().register(name, location, datestamp):
            flash(name + ' created as an Organization')
        else:
            flash(name + ' does exist already, not created.')
    return render_template('organization.html')


@app.route('/organization/list')
def organization_list():
    organizations = get_organizations()
    app.logger.debug(organizations)
    return render_template('display_organizations.html', organizations=organizations)


@app.route('/organization/<org_id>')
def organization_races(org_id):
    """
    This method will manage races with an organization. It will get the organization object based on ID. Then it will
    the list of existing races for the organization. Races need to be added, removed or modified.
    :param org_id: Organization ID
    :return:
    """
    app.logger.debug("org_id: " + org_id)
    org = Organization()
    org.set_organization(org_id)
    org_label = org.get_label()
    return render_template('/organization_races.html', org_label=org_label)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", err=e)
