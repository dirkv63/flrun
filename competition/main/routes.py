from flask import render_template, flash, current_app, redirect, url_for, request
from flask_login import login_required, login_user, logout_user
from .forms import RegisterForm, OrganisationNewForm, LoginForm
from . import main
from ..models_graph import Person, Organization, get_organizations, get_participants, get_race_types, \
    relations, remove_node
from ..models_sql import User


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            current_app.logger.debug('Login not successful')
            return redirect(url_for('main.login', **request.args))
        login_user(user, form.remember_me.data)
        return redirect(request.args.get('next') or url_for('main.index'))
    return render_template('login.html', form=form)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@main.route('/participant/register', methods=['GET', 'POST'])
@login_required
def register():
    name = None
    form = RegisterForm()
    participant = Person()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        if participant.register(name):
            flash(name + ' created as a Person (participant)')
        else:
            flash(name + ' does exist already, not created.')
    return render_template('register.html', form=form, name=name)


@main.route('/participant/list')
def participant_list():
    participants = get_participants()
    current_app.logger.debug("Participants: {participants}".format(participants=participants))
    return render_template('display_participants.html', participants=participants)


@main.route('/participant/<part_id>')
def participant_summary(part_id):
    """
    This method provides all information about a single participant. In case this is an 'isolated' participant
    (this means without link to races), then a 'Verwijder' (delete) button will be shown.
    :param part_id: ID of the Participant for which overview info is required.
    :return:
    """
    current_app.logger.debug("part_id: " + part_id)
    part = Person()
    part.set_person(part_id)
    part_name = part.get_name()
    return render_template('/organization_races.html', org_label=part_name)


@main.route('/participant/remove/<part_id>')
@login_required
def participant_remove(part_id):
    """
    This method will get an id for a participant that can be removed. Checks have been done to make sure that there
    are no more connections (relations) with this participant.
    :param part_id:
    :return:
    """
    part = Person()
    part.set_person(part_id)
    # part_name = part.get_name()
    if relations(part_id):
        current_app.logger.warning("Request to delete id {part_id} but relations found".format(part_id=part_id))
    else:
        remove_node(part_id)
    return redirect(url_for('main.participant_list'))


@main.route('/organization', methods=['GET', 'POST'])
@login_required
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
    show the list of existing races for the organization. Races need to be added, removed or modified.
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
