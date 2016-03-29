from flask import render_template, flash, current_app, redirect, url_for
from .forms import RegisterForm, OrganisationNewForm
from . import main
from ..models import Person, Organization, get_organizations, get_participants


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/participant/register', methods=['GET', 'POST'])
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


@main.route('/participant/list')
def participant_list():
    participants = get_participants()
    current_app.logger.debug("Participants: {participants}".format(participants=participants))
    return render_template('display_participants.html', participants=participants)


@main.route('/organization', methods=['GET', 'POST'])
def organization():
    name = None
    location = None
    datestamp = None
    form = OrganisationNewForm()
    if form.validate_on_submit():
        name = form.name.data
        location = form.location.data
        datestamp = form.datestamp.data
        if Organization().register(name, location, datestamp):
            flash(name + ' created as an Organization')
        else:
            flash(name + ' does exist already, not created.')
        # Form validated successfully, clear fields!
        return redirect(url_for('main.organization'))
    else:
        # Form did not validate successfully, keep fields.
        return render_template('organization.html', form=form, name=name, location=location, datestamp=datestamp)


@main.route('/organization/list')
def organization_list():
    organizations = get_organizations()
    current_app.logger.debug(organizations)
    return render_template('display_organizations.html', organizations=organizations)


@main.route('/organization/<org_id>')
def organization_races(org_id):
    """
    This method will manage races with an organization. It will get the organization object based on ID. Then it will
    the list of existing races for the organization. Races need to be added, removed or modified.
    :param org_id: Organization ID
    :return:
    """
    current_app.logger.debug("org_id: " + org_id)
    org = Organization()
    org.set_organization(org_id)
    org_label = org.get_label()
    return render_template('/organization_races.html', org_label=org_label)


@main.errorhandler(404)
def not_found(e):
    return render_template("404.html", err=e)
