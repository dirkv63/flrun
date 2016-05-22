import competition.models_graph as mg
# import logging
# import datetime
import competition.p2n_wrapper as pu
from lib import my_env
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
def person_add(person_id=None):
    if request.method == "GET":
        if person_id:
            person = mg.Person(person_id=person_id)
            person_dict = person.props()
            name = person_dict['name']
            mf = person_dict['mf']
            form = PersonAdd(mf=mf)
            form.name.data = name
            if 'born' in person_dict:
                bornstr = person_dict['born']
                form.born.data = my_env.datestr2date(bornstr)
        else:
            name = None
            form = PersonAdd()
    else:
        # request.method == "POST":
        form = PersonAdd()
        name = None
        if form.validate_on_submit():
            person_dict = dict(name=form.name.data, mf=form.mf.data)
            if form.born.data:
                person_dict['born'] = form.born.data
            name = person_dict['name']
            if person_id:
                # This is from person edit function
                current_app.logger.debug("Person Dictionary: {person_dict}".format(person_dict=person_dict))
                person = mg.Person(person_id=person_id)
                person.edit(**person_dict)
            else:
                person = mg.Person()
                if not person.add(**person_dict):
                    flash(name + ' bestaat reeds, niet toegevoegd.')
            return redirect(url_for('main.person_add'))
    persons = mg.person_list()
    return render_template('person_add.html', form=form, name=name, persons=persons)


@main.route('/person/edit/<pers_id>', methods=['GET', 'POST'])
@login_required
def person_edit(pers_id):
    """
    This method will edit the person's information.
    :param pers_id:
    :return:
    """
    # Flask insists on getting a response back. Omitting 'return' in line below is an implicit 'Return None' and Flask
    # doesn't like this.
    return person_add(person_id=pers_id)


@main.route('/person/list')
def person_list():
    persons = mg.person_list()
    return render_template('person_list.html', persons=persons)


@main.route('/person/<pers_id>')
def person_summary(pers_id):
    """
    This method provides all information about a single participant. In case this is an 'isolated' participant
    (this means without link to races), then a 'Verwijder' (delete) button will be shown.
    :param pers_id: ID of the Participant for which overview info is required.
    :return:
    """
    part = mg.Person()
    part.set(pers_id)
    part_name = part.get()
    races = mg.races4person(pers_id)
    # Don't count on len(races), since this is this competition races. Remove person only if not used across all
    # competitions.
    if pu.relations(pers_id):
        conns = 1
    else:
        conns = 0
    persons = mg.person_list()
    return render_template('/person_races_list.html', pers_label=part_name, pers_id=pers_id, races=races,
                           conns=conns, persons=persons)


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
    if pu.relations(pers_id):
        current_app.logger.warning("Request to delete id {pers_id} but relations found".format(pers_id=pers_id))
    else:
        pu.remove_node(pers_id)
    return redirect(url_for('main.person_list'))


@main.route('/organization/list')
def organization_list():
    organizations = mg.organization_list()
    current_app.logger.debug(organizations)
    return render_template('organization_list.html', organizations=organizations)


@main.route('/organization/add', methods=['GET', 'POST'])
@login_required
def organization_add(org_id=None):
    current_app.logger.debug("Evaluate Organization/add")
    if request.method == "POST":
        form = OrganizationAdd()
        if form.validate_on_submit():
            org_dict = dict(name=form.name.data,
                            location=form.location.data,
                            datestamp=form.datestamp.data,
                            org_type=form.org_type.data)
            if org_id:
                current_app.logger.debug("Ready to edit organization")
                org = mg.Organization(org_id=org_id)
                if org.edit(**org_dict):
                    flash(org_dict["name"] + ' aangepast.')
                else:
                    flash(org_dict["name"] + ' bestaat reeds, niet aangepast.')
            else:
                current_app.logger.debug("Ready to add organization")
                if mg.Organization().add(**org_dict):
                    flash(org_dict["name"] + ' toegevoegd als organizatie')
                else:
                    flash(org_dict["name"] + ' bestaat reeds, niet toegevoegd.')
            # Form validated successfully, clear fields!
            return redirect(url_for('main.organization_list'))
    # Request Method is GET or Form did not validate
    # Note that in case Form did not validate, the fields will be reset.
    # But how can we fail on form_validate?
    organizations = mg.organization_list()
    if org_id:
        current_app.logger.debug("Get Form to edit organization")
        org = mg.Organization(org_id=org_id)
        name = org.name
        location = org.get_location()
        datestamp = org.get_date()
        org_type = org.get_org_type()
        form = OrganizationAdd(org_type=org_type)
        form.name.data = name
        form.location.data = location
        form.datestamp.data = my_env.datestr2date(datestamp)
    else:
        current_app.logger.debug("Get Form to add organization")
        name = None
        location = None
        datestamp = None
        form = OrganizationAdd()
    # Form did not validate successfully, keep fields.
    return render_template('organization_add.html', form=form, name=name, location=location,
                           datestamp=datestamp, organizations=organizations)


@main.route('/organization/edit/<org_id>', methods=['GET', 'POST'])
@login_required
def organization_edit(org_id):
    """
    This method will edit an existing organization.
    :param org_id: The Node ID of the organization.
    :return:
    """
    current_app.logger.debug("Evaluate Organization/edit")
    return organization_add(org_id=org_id)


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
    org_label = org.get_label()
    races = mg.race_list(org_id)
    return render_template('/organization_races.html', org_label=org_label, org_id=org_id, races=races)


@main.route('/race/<org_id>/add', methods=['GET', 'POST'])
@login_required
def race_add(org_id):
    name = None
    form = RaceAdd()
    org = mg.Organization(org_id=org_id)
    if org.has_wedstrijd_type(racetype="Hoofdwedstrijd"):
        del form.raceType
    if form.validate_on_submit():
        name = form.name.data
        if form.raceType:
            racetype = form.raceType.data
        else:
            racetype = False
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
    """
    This method will add a person to a race. The previous runner (earlier arrival) is selected from drop-down list.
    By default the person is appended as tha last position in the race, so the previous person was the last one in the
    race. First position is specified as previous runner equals -1.
    :param race_id: ID of the race.
    :return:
    """
    race_label = mg.race_label(race_id)
    if request.method == "POST":
        # Call form to get input values
        form = ParticipantAdd()
        # Add collected info as participant to race.
        runner_id = form.name.data
        # runner_obj = mg.Person()
        # runner_obj.set(runner_id)
        # runner = runner_obj.get()
        prev_runner_id = form.prev_runner.data
        # Create the participant node, connect to person and to race.
        part = mg.Participant()
        part.add(race_id=race_id, pers_id=runner_id, prev_pers_id=prev_runner_id)
        return redirect(url_for('main.participant_add', race_id=race_id))
    else:
        # Get method, initialize page.
        current_app.logger.debug("Initialize page")
        part_last = mg.participant_last_id(race_id)
        form = ParticipantAdd(prev_runner=part_last)
        form.name.choices = mg.next_participant(race_id)
        form.prev_runner.choices = mg.participant_after_list(race_id)
        finishers = mg.participant_seq_list(race_id)
        return render_template('participant_add.html', form=form, race_id=race_id, finishers=finishers,
                               race_label=race_label)


@main.route('/participant/remove/<race_id>/<pers_id>', methods=['GET', 'POST'])
@login_required
def participant_remove(race_id, pers_id):
    """
    This method will remove the participant from the race.
    :param race_id: ID of the race. This can be calculated, but it is always available.
    :param pers_id: Node ID of the participant in the race.
    :return:
    """
    person = mg.Person(person_id=pers_id)
    person_name = person.get()
    form = ParticipantRemove()
    race_label = mg.race_label(race_id)
    finishers = mg.participant_seq_list(race_id)
    if request.method == "GET":
        return render_template('participant_remove.html', form=form, race_id=race_id, finishers=finishers,
                               race_label=race_label, pers_label=person_name)
    elif request.method == "POST":
        if form.submit_ok.data:
            part = mg.Participant(race_id=race_id, pers_id=pers_id)
            part.remove()
    return redirect(url_for('main.participant_add', race_id=race_id))


@main.errorhandler(404)
def not_found(e):
    return render_template("404.html", err=e)
