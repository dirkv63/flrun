import competition.models_graph as mg
from flask import render_template, flash, current_app, redirect, url_for, request
from flask_login import login_required, login_user, logout_user
from .forms import *
from . import main
from ..models_sql import User


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = Login()
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


@main.route('/person/add', methods=['GET', 'POST'])
@login_required
def person_add():
    name = None
    form = PersonAdd()
    person = mg.Person()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        if person.add(name):
            flash(name + ' created as a Person (participant)')
        else:
            flash(name + ' does exist already, not created.')
    return render_template('person_add.html', form=form, name=name)


@main.route('/person/list')
def person_list():
    participants = mg.person_list()
    current_app.logger.debug("Participants: {participants}".format(participants=participants))
    return render_template('person_list.html', participants=participants)


@main.route('/person/<pers_id>')
def person_summary(pers_id):
    """
    This method provides all information about a single participant. In case this is an 'isolated' participant
    (this means without link to races), then a 'Verwijder' (delete) button will be shown.
    :param pers_id: ID of the Participant for which overview info is required.
    :return:
    """
    current_app.logger.debug("pers_id: " + pers_id)
    part = mg.Person()
    part.set(pers_id)
    part_name = part.get()
    return render_template('/race_list.html', org_label=part_name)


@main.route('/person/<pers_id>/delete')
@login_required
def person_delete(pers_id):
    """
    This method will get an id for a participant that can be removed. Checks have been done to make sure that there
    are no more connections (relations) with this participant.
    :param pers_id:
    :return:
    """
    part = mg.Person()
    part.set(pers_id)
    # part_name = part.get_name()
    if mg.relations(pers_id):
        current_app.logger.warning("Request to delete id {pers_id} but relations found".format(pers_id=pers_id))
    else:
        mg.remove_node(pers_id)
    return redirect(url_for('main.person_list'))


@main.route('/organization/add', methods=['GET', 'POST'])
@login_required
def organization_add():
    name = None
    location = None
    datestamp = None
    form = OrganizationAdd()
    if form.validate_on_submit():
        name = form.name.data
        location = form.location.data
        datestamp = form.datestamp.data
        if mg.Organization().add(name, location, datestamp):
            flash(name + ' created as an Organization')
        else:
            flash(name + ' does exist already, not created.')
        # Form validated successfully, clear fields!
        return redirect(url_for('main.organization_add'))
    else:
        # Form did not validate successfully, keep fields.
        return render_template('organization_add.html', form=form, name=name, location=location, datestamp=datestamp)


@main.route('/organization/list')
def organization_list():
    organizations = mg.organization_list()
    current_app.logger.debug(organizations)
    return render_template('organization_list.html', organizations=organizations)


@main.route('/race/<org_id>/list')
def race_list(org_id):
    """
    This method will manage races with an organization. It will get the organization object based on ID. Then it will
    show the list of existing races for the organization. Races need to be added, removed or modified.
    :param org_id: Organization ID
    :return:
    """
    current_app.logger.debug("org_id: " + org_id)
    org = mg.Organization()
    org.set(org_id)
    org_label = org.get()
    races = mg.race_list(org_id)
    return render_template('/race_list.html', org_label=org_label, org_id=org_id, races=races)


@main.route('/race/<org_id>/add', methods=['GET', 'POST'])
@login_required
def race_add(org_id):
    name = None
    form = RaceAdd()
    form.raceType.choices = mg.racetype_list()
    if form.validate_on_submit():
        name = form.name.data
        racetype = form.raceType.data
        if mg.Race(org_id).add(name, racetype):
            flash(name + ' created as a Race in Organization')
        else:
            flash(name + ' does exist already, not created.')
        # Form validated successfully, clear fields!
        return redirect(url_for('main.race_add', org_id=org_id))
    else:
        # Form did not validate successfully, keep fields.
        return render_template('race_add.html', form=form, name=name, org_id=org_id)


@main.route('/participant/<race_id>/add', methods=['GET', 'POST'])
@login_required
def participant_add(race_id):
    form = ParticipantAdd()
    form.name.choices = mg.next_participant(race_id)
    finishers = mg.participant_seq_list(race_id)
    current_app.logger.debug("Finishers: {finishers}".format(finishers=finishers))
    if request.method == "POST":
        # Add collected info as participant to race.
        runner_id = form.name.data
        runner_obj = mg.Person()
        runner_obj.set(runner_id)
        runner = runner_obj.get()
        current_app.logger.debug("Selected Runner: {runner}".format(runner=runner))
        participant = mg.Participant()
        participant.set(race_id=race_id, runner_id=runner_id)
        return redirect(url_for('main.participant_add', form=form, race_id=race_id, finishers=finishers))
    else:
        # Get method, initialize page.
        current_app.logger.debug("Initialize page")
        return render_template('participant_add.html', form=form, race_id=race_id, finishers=finishers)


@main.errorhandler(404)
def not_found(e):
    return render_template("404.html", err=e)
