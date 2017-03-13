import logging
from . import lm
from competition import neostore
from flask_login import UserMixin
# from lib import my_env
from werkzeug.security import generate_password_hash, check_password_hash

# Todo: Get Username / Password from environment settings
ns = neostore.NeoStore()


class User(UserMixin):
    """
    The user class manages the registered users of the application. The Person class is for the people that participate
    in the race.
    """
    def __init__(self, user_id=None):
        if user_id:
            self.user_node = ns.node(user_id)
        else:
            self.user_node = "NotDefined"

    def __repr__(self):
        return "<User: {user}>".format(user=self.user_node["name"])

    def find(self, username):
        """
        This function will find the User object for the user with the specified username.
        If found, then the hashed password is returned. If not found, False is returned.
        :param username:
        :return: User node, then the caller can do whatever he wants with the information.
        """
        label = "User"
        props = dict(name=username)
        user_node = ns.get_node(label, **props)
        if user_node:
            try:
                self.user_node = user_node
                return self.user_node
            except KeyError:
                # Password not defined for user, return False
                return False
        else:
            # User not defined
            return False

    def get_id(self):
        return self.user_node["nid"]

    def register(self, username, password):
        if self.find(username):
            return False
        else:
            label = "User"
            props = dict(
                name=username,
                pwd=generate_password_hash(password)
            )
            user_node = ns.create_node(label, **props)
            return user_node["nid"]

    def validate_password(self, name, pwd):
        """
        Find the user. If the user exists, verify the password. If the passwords match, return nid of the User node.
        If the passwords don't match, return False.
        If the user does not exists, return False.
        :param name:
        :param pwd:
        :return:
        """
        if self.find(name):
            return check_password_hash(self.user_node["pwd"], pwd)
        else:
            return False


@lm.user_loader
def load_user(user_id):
    """
    This function will return the User object. user_id is the nid of the User node.
    :param user_id: nid of the user node.
    :return: user object.
    """
    return User(user_id)


class Participant:

    # List of calculated properties for the participant node.
    calc_props = ["nid", "points", "rel_pos"]

    def __init__(self, part_id=None, race_id=None, pers_id=None):
        """
        A Participant Object is the path: (person)-[:is]->(participant)-[:participates]->(race).
        If participant id is provided, then find race id and person id.
        If race id and person id are provided, then try to find participant id. If not successful, then create
        participant id. The application must call the 'add' method to add this participant in the correct sequence.
        At the end of initialization, participant node, id, race id and person id are set.
        When a participant is added or deleted, then the points for the race will be recalculated.
        :param part_id: nid of the participant
        :param race_id: nid of the race
        :param pers_id: nid of the person
        :return: Participant object with participant node and nid, race nid and person nid are set.
        """
        # Todo: rework classes so that objects are kept, not nids - replace race_nid with race_obj, ...
        self.part_node = None
        self.part_id = -1           # Unique ID (nid) of the Participant node
        if part_id:
            # I have a participant ID, find race and person information
            self.part_node = ns.node(part_id)
            self.part_id = part_id
            self.race_id = ns.get_end_node(start_node_id=part_id, rel_type="participates")
            self.pers_id = ns.get_start_node(end_node_id=part_id, rel_type="is")
        elif pers_id and race_id:
            self.race_id = race_id
            self.pers_id = pers_id
            self.part_node = ns.get_participant_in_race(pers_id=pers_id, race_id=race_id)
            if self.part_node:
                self.part_id = self.part_node["nid"]
            else:
                # Participant node not found, so create one.
                # First remember first arrival in the race
                self.first_arrival_in_race = participant_first_id(race_id)
                self.part_id = self.set_part_race()
        else:
            logging.fatal("No input provided.")
            raise ValueError("CannotCreateObject")
        return

    def get_id(self):
        """
        This method will return the Participant Node ID of this person's participation in the race
        :return: Participant Node ID (nid)
        """
        return self.part_id

    def get_person_nid(self):
        """
        This method will return the Person Node ID for this participant.
        :return:
        """
        return self.pers_id

    def get_props(self):
        """
        This method will get the properties for the node. All properties for the participant node will be collected,
        then the calculated properties (points, rel_pos, ...) will be removed from the dictionary.
        collected from the participant node and added to the list of properties that are set by the user.
        :return:
        """
        # Get participant node to ensure latest values for all calculated properties.
        # Ignore the user configurable properties, since these are managed in the **props dictionary.
        self.part_node = ns.node(self.part_id)
        # Convert node to node-dictionary.
        part_dict = dict(self.part_node)
        # Remove calculated properties from dictionary
        for attrib in self.calc_props:
            part_dict.pop(attrib, None)
        return part_dict

    def get_race_nid(self):
        """
        This method will return the Race Node ID for the participant.
        :return: Nid for the Race node.
        """
        return self.race_id

    def set_part_race(self):
        """
        This method will link the person to the race. This is done by creating an Participant Node. This function will
        not link the participant to the previous or next participant.
        The method will set the participant node and the participant nid.
        @return: Node ID of the participant node.
        """
        self.part_node = ns.create_node("Participant")
        self.part_id = self.part_node["nid"]
        race_node = ns.node(self.race_id)
        ns.create_relation(from_node=self.part_node, rel="participates", to_node=race_node)
        pers_node = ns.node(self.pers_id)
        ns.create_relation(from_node=pers_node, rel="is", to_node=self.part_node)
        return self.part_id

    def set_props(self, **props):
        """
        This method will set the properties for the node. The calculated properties (points, rel_pos, ...) will be
        collected from the participant node and added to the list of properties that are set by the user.
        :param props: list of user properties for the participant node.
        :return:
        """
        #ToDo: It may be better to use ns.node_set_attribs.
        # Get participant node to ensure latest values for all calculated properties.
        # Ignore the user configurable properties, since these are managed in the **props dictionary.
        self.part_node = ns.node(self.part_id)
        # Convert node to node-dictionary. This ensures that KeyError exception can be used.
        part_dict = dict(self.part_node)
        for attrib in self.calc_props:
            try:
                props[attrib] = part_dict[attrib]
            except KeyError:
                pass
        return ns.node_update(**props)

    @staticmethod
    def set_relation(next_id=None, prev_id=None):
        """
        This method will connect the next runner with the previous runner. The next runner is after the previous runner.
        @param next_id: Node ID of the next runner
        @param prev_id: Node ID of the previous runner
        @return:
        """
        prev_part_node = ns.node(prev_id)
        next_part_node = ns.node(next_id)
        if neostore.validate_node(prev_part_node, "Participant") \
                and neostore.validate_node(next_part_node, "Participant"):
            ns.create_relation(from_node=next_part_node, rel="after", to_node=prev_part_node)
        return

    def add(self, prev_pers_id=None):
        """
        This method will add the participant in the chain of arrivals. This is required only if there is more than one
        participant in the race.
        First action will be determined, then the action will be executed.
        Is there a previous arrival (prev_pers_id) for this runner? Remember nid for previous arrival. Else this
        participant is the first arrival.
        Is there a next arrival for this runner? Remove relation between previous and next, remember next.
        Now link current participant to previous arrival and to next arrival.
        :param prev_pers_id: nid of previous arrival, or -1 if current participant in first arrival
        :return:
        """
        # Count total number of arrivals. Process required only if there is more than one.
        nr_participants = len(participant_list(self.race_id))
        if nr_participants > 1:
            # Process required only if there is more than one participant in the race
            if prev_pers_id != "-1":
                # There is an arrival before current participant
                # Find participant nid for this person
                prev_arrival_obj = Participant(race_id=self.race_id, pers_id=prev_pers_id)
                prev_arrival_nid = prev_arrival_obj.get_id()
                # This can be linked to a next_arrival. Current participant will break this link
                next_arrival_nid = prev_arrival_obj.next_runner()
                if next_arrival_nid:
                    ns.remove_relation(start_nid=next_arrival_nid, end_nid=prev_arrival_nid, rel_type="after")
            else:
                # This participant is the first one in the race. Find the next participant.
                # Be careful, method 'participant_first_id' requires valid chain. So this needs to run before
                # set_part_race()
                prev_arrival_nid = False
                # Get participant nid for person nid first arrival.
                next_arrival_obj = Participant(race_id=self.race_id, pers_id=self.first_arrival_in_race)
                next_arrival_nid = next_arrival_obj.get_id()
            # Previous and next arrival have been calculated, create relation if required
            if prev_arrival_nid:
                self.set_relation(next_id=self.part_id, prev_id=prev_arrival_nid)
            if next_arrival_nid:
                self.set_relation(next_id=next_arrival_nid, prev_id=self.part_id)
        # Calculate points after adding participant
        points_for_race(self.race_id)
        return

    def prev_runner(self):
        """
        This method will get the node ID for this Participant's previous runner.
        The participant must have been created before.
        @return: ID of previous runner participant Node, False if there is no previous runner.
        """
        if not neostore.validate_node(self.part_node, "Participant"):       # pragma: no cover
            return False
        prev_part_id = ns.get_end_node(start_node_id=self.part_id, rel_type="after")
        return prev_part_id

    def next_runner(self):
        """
        This method will get the node ID for this Participant's next runner.
        The participant must have been created before.
        @return: ID of next runner participant Node, False if there is no next runner.
        """
        if not neostore.validate_node(self.part_node, "Participant"):       # pragma: no cover
            return False
        next_part_id = ns.get_start_node(end_node_id=self.part_id, rel_type="after")
        return next_part_id

    def remove(self):
        """
        This method will remove the participant from the race.
        Recalculate points for the race.
        @return:
        """
        if self.prev_runner() and self.next_runner():
            # There is a previous and next runner, link them
            ns.create_relation(from_node=ns.node(self.next_runner()), rel="after", to_node=ns.node(self.prev_runner()))
        # Remove Participant Node
        ns.remove_node_force(self.part_id)
        # Reset Object
        self.part_id = -1
        self.part_node = None
        points_for_race(self.race_id)
        return


class Person:
    # Todo: add a person.remove() method: remove MF link, check no participant links available.

    def __init__(self, person_id=None):
        if person_id:
            self.person_id, self.name = self.set(person_id)
        else:
            self.name = 'NotYetDefined'
            self.person_id = person_id

    def find(self):
        """
        Find ID of the person with name 'name'. Return node ID, else return false.
        This function must be called from add(), so make it an internal function?
        @return: Node ID, or false if no node could be found.
        """
        props = {
            "name": self.name
        }
        person_node = ns.get_node("Person", **props)
        if person_node:
            self.person_id = person_node["nid"]
            return True
        else:
            return False

    def add(self, **properties):
        """
        Attempt to add the participant with name 'name'. The name must be unique. Person object is set to current
        participant. Name is set in this procedure, ID is set in the find procedure.
        @param properties: Properties (in dict) for the person
        @return: True, if registered. False otherwise.
        """
        self.name = properties['name']
        if self.find():
            # Person is found, Name and ID set, no need to register.
            return False
        else:
            # Person not found, register participant.
            ns.create_node("Person", **properties)
            # Now call find() again to set ID for the person
            self.find()
            return True

    def edit(self, **properties):
        """
        This method will update an existing person node. A check is done to guarantee that the name is not duplicated
        to an existing name on another node. Modified properties will be updated and removed properties will be deleted.
        @param properties: New set of properties for the node
        @return: True - in case node is rewritten successfully.
        """
        logging.fatal("Look here, properties: {p}".format(p=properties))
        properties["nid"] = self.person_id
        ns.node_update(**properties)
        return True

    def set(self, person_id):
        """
        This method will set the person associated with this ID. The assumption is that the person_id relates to a
        existing and valid person.
        @param person_id:
        @return: Person object is set to the participant.
        """
        person_node = ns.node(person_id)
        if person_node:
            self.name = person_node["name"]
            self.person_id = person_id
            return self.person_id, self.name
        else:
            raise ValueError("NodeNotFound")

    def get(self):
        return self.name

    def get_dict(self):
        """
        This function will return a dictionary with the person attributes. This can then be used for display in a
        html macro

        :return: Dictionary with person attributes nid, label, active (True: Active user, cannot be removed,
        False: inactive user, can be removed).
        """
        person_dict = dict(
            nid=self.person_id,
            label=self.get(),
            active=self.active()
        )
        return person_dict

    def get_mf(self):
        """
        This method will get 'MF' link for the person, and translates the value to 'man' or 'vrouw'.
        :return: 'man', 'vrouw' or 'False' in case 'MF' is not set.
        """
        mf_tx = dict(Heren="man", Dames="vrouw")
        mf_node_id = ns.get_end_node(start_node_id=self.person_id, rel_type="mf")
        if mf_node_id:
            mf_node = ns.node(mf_node_id)
            return mf_tx[mf_node["name"]]
        else:
            return False

    def active(self):
        """
        This method will check if a person is active. For now, this means that a person has 'participates' links.
        If the person is not active, then the person can be removed.
        @return: True if the person is active, False otherwise
        """
        return ns.get_end_nodes(start_node_id=self.person_id, rel_type="is")

    def props(self):
        """
        This method will return the properties for the node in a dictionary format.
        @return:
        """
        return ns.node_props(nid=self.person_id)

    def set_mf(self, mf_label):
        """
        This method will set 'MF' link for the person. It will check if a link exists already. If not, then link
        will be created. If link exists, but invalid link then required link will be created and invalid link will
        be removed.
        @param mf_label: Label to set (man/vrouw)
        @return:
        """
        mf_inv_tx = dict(man="Heren", vrouw="Dames")
        current_mf = self.get_mf()
        if current_mf:
            if current_mf == mf_label:
                # OK, required link exists already. Return
                return False
            else:
                # The opposite link exists. Remove it.
                props = dict(name=mf_inv_tx[current_mf])
                mf_node = ns.get_node("MF", **props)
                ns.remove_relation(start_nid=self.person_id, end_nid=mf_node["nid"], rel_type="mf")
        # On this point I'm sure no relation exists
        person_node = ns.node(self.person_id)
        props = dict(name=mf_inv_tx[mf_label])
        mf_node = ns.get_node("MF", **props)
        ns.create_relation(from_node=person_node, rel="mf", to_node=mf_node)
        return True


class Organization:
    """
    This class instantiates to an organization.
    @return: Object
    """
    def __init__(self, org_id=None):
        self.name = 'NotYetDefined'
        self.org_id = -1
        self.org_node = None
        self.label = "NotYetDefined"
        self.org = None
        if org_id:
            self.set(org_id)

    def find(self, **org_dict):
        """
        This method searches for the organization based on organization name, location and datestamp. If found,
        then organization attributes will be set using method set_organization. If not found, 'False' will be returned.
        @param org_dict: New set of properties for the node. These properties are: name, location, datestamp and
         org_type
        @return: True if organization is found, False otherwise.
        """
        org_id = ns.get_organization(**org_dict)
        if org_id:
            self.org_id = org_id
            self.set(self.org_id)
            return True
        else:
            return False

    def add(self, **org_dict):
        """
        This method will check if the organization is registered already. If not, the organization graph object
        (exists of organization name with link to date and city where it is organized) will be created.
        The organization instance attributes will be set.
        @param org_dict: New set of properties for the node. These properties are: name, location, datestamp and
         org_type. Datestamp needs to be of the form 'YYYY-MM-DD'. org_type 1 for Wedstrijd, 2 for deelname.
        @return: True if the organization has been registered, False if it existed already.
        """
        org_type = org_dict["org_type"]
        del org_dict["org_type"]
        self.org = org_dict
        if self.find(**org_dict):
            # No need to register (Organization exist already), and organization attributes are set.
            return False
        else:
            # Organization on Location and datestamp does not yet exist, register the node.
            self.org_node = ns.create_node("Organization", name=self.org["name"])
            # graph.create(self.org_node)  # Node will be created on first Relation creation.
            # Organization node known, now I can link it with the Location.
            self.set_location(self.org["location"])
            # Set Date  for Organization
            self.set_date(self.org["datestamp"])
            # Set Organization Type
            org_type_node = get_org_type_node(org_type)
            ns.create_relation(from_node=self.org_node, rel="type", to_node=org_type_node)
            # Set organization parameters by finding the created organization
            self.find(**org_dict)
            return True

    def edit(self, **properties):
        """
        This method will check if the organization is registered already. If not, the organization graph object
        (exists of organization name with link to date and city where it is organized) will be created.
        The organization instance attributes will be set.
        Edit function needs to redirect relations, so it has begin and end nodes. This function can then remove single
        date nodes and location nodes if required. The Organization delete function will force to remove an organization
        node without a need to find the date and location first. Therefore the delete function requires a more generic
        date and location removal, where a check on all orphans is done.
        @param properties: New set of properties for the node. These properties are: name, location, datestamp and
         org_type. Datestamp must be of the form 'YYYY-MM-DD'
        @return: True if the organization has been updated, False if the organization (name, location, date) existed
         already. A change in Organization Type only is also a successful (True) change.
        """
        # Check Organization Type
        curr_org_type = self.get_org_type()
        if not curr_org_type == properties["org_type"]:
            self.set_org_type(new_org_type=properties["org_type"], curr_org_type=curr_org_type)
            # Organization type changed, so re-calculate points for all races in the organization
            racelist = race_list(self.org_id)
            for rec in racelist:
                # Probably not efficient, but then you should't change organization type too often.
                points_for_race(rec["race_id"])
        del properties["org_type"]
        # Check if name, date or location are changed
        changed_keys = [key for key in sorted(properties) if not (properties[key] == self.org[key])]
        if len(changed_keys) > 0:
            # Something is changed, so I need to end-up in unique combination of name, location, date
            if self.find(**properties):
                logging.error("Aangepaste Organisatie bestaat reeds: {props}".format(props=properties))
                return False
            else:
                if 'name' in changed_keys:
                    node_prop = dict(
                        name=properties["name"],
                        nid=self.org_id
                    )
                    ns.node_update(**node_prop)
                if 'location' in changed_keys:
                    # Remember current location - before fiddling around with relations!
                    curr_loc = Location(self.org["location"]).get_node()
                    curr_loc_id = ns.node_id(curr_loc)
                    # First create link to new location
                    self.set_location(properties["location"])
                    # Then remove link to current location
                    ns.remove_relation(start_nid=self.org_id, end_nid=curr_loc_id, rel_type="In")
                    # Finally check if current location is still required. Remove if there are no more links.
                    ns.remove_node(curr_loc_id)
                if 'datestamp' in changed_keys:
                    # Get Node for current day
                    curr_ds = self.org["datestamp"]
                    curr_date_node = ns.date_node(curr_ds)
                    # First create link to new date
                    self.set_date(properties["datestamp"])
                    # Then remove link from current date
                    ns.remove_relation(start_nid=self.org_id, end_nid=ns.node_id(curr_date_node), rel_type="On")
                    # Finally check if date (day, month, year) can be removed.
                    # Don't remove single date, clear all dates that can be removed. This avoids the handling of key
                    # because date nodes don't have a nid.
                    ns.clear_date()
                # New attributes configured, now set Organization again.
                self.set(self.org_id)
        return True

    def set(self, org_id):
        """
        This method will get the organization associated with this ID. The assumption is that the org_id relates to a
        existing and valid organization.
        It will set the organization labels.
        @param org_id:
        @return:
        """
        this_org = ns.get_organization_from_id(org_id)
        self.label = "{org_name} ({city}, {day:02d}-{month:02d}-{year})".format(org_name=this_org["org"],
                                                                                city=this_org["city"],
                                                                                day=this_org["day"],
                                                                                month=this_org["month"],
                                                                                year=this_org["year"])
        self.org = dict(
            name=this_org["org"],
            location=this_org["city"],
            datestamp=this_org["date"]
        )
        self.name = this_org["org"]
        self.org_id = org_id
        self.org_node = ns.node(org_id)
        return True

    def get_label(self):
        """
        This method will return the label of the Organization. (Organization name, city and date). Assumption is that
        the organization has been set already.
        @return:
        """
        return self.label

    def get_location(self):
        """
        This method will return the location for the Organization.
        @return: Location name (city name), or False if no location found.
        """
        loc_id = ns.get_end_node(self.org_id, "In")
        loc_node = ns.node(loc_id)
        city = loc_node["city"]
        return city

    def get_date(self):
        """
        This method will return the date for the Organization.
        @return: Date, Format YYYY-MM-DD
        """
        date_id = ns.get_end_node(self.org_id, "On")
        date_node = ns.node(date_id)
        datestamp = date_node["key"]
        return datestamp

    def get_org_id(self):
        """
        This method will return the nid of the Organization node.
        :return: nid of the Organization node
        """
        return self.org_id

    def get_org_type(self):
        """
        This method will return the organization type as a Number. If not available, then Organization type is
        Wedstrijd (1). Not sure what the purpose of this method is.
        @return: Organization Type. 1: Wedstrijd (Default) - 2: Deelname
        """
        # Todo: Review usage of this method.
        org_type = {
            "Wedstrijd": 1,
            "Deelname": 2
            }
        org_type_name = 'Wedstrijd'
        org_type_id = ns.get_end_node(self.org_id, "type")
        if org_type_id:
            org_type_node = ns.node(org_type_id)
            org_type_name = org_type_node["name"]
        return org_type[org_type_name]

    def has_wedstrijd_type(self, racetype="NotFound"):
        """
        This method will check the number of races of type racetype. It can be used to check if there is a
        'Hoofdwedstrijd' assigned with the Organization.
        @param racetype: Race Type (Hoofdwedstrijd, Bijwedstrijd, Deelname)
        @return: Number of races for this type, False if there are no races.
        """
        res = ns.get_wedstrijd_type(self.org_id, racetype)
        if res:
            return res
        else:
            return False

    def ask_for_hoofdwedstrijd(self):
        """
        This method will check if adding a race needs an option to select a 'Hoofdwedstrijd'. This is required if
        Organization Type is 'Wedstrijd' (1) and no hoofdwedstrijd has been selected.
        @return: True - if Hoofdwedstrijd option for race is required, False otherwise.
        """
        if self.get_org_type() == 1 and not self.has_wedstrijd_type("Hoofdwedstrijd"):
            return True
        else:
            return False

    def set_location(self, loc=None):
        """
        This method will create a relation between the organization and the location. Relation type is 'In'.
        Organization Node must be available for this method.
        @param loc: Name of the city.
        @return:
        """
        loc_node = Location(loc).get_node()   # Get Location Node
        ns.create_relation(from_node=self.org_node, to_node=loc_node, rel="In")
        return

    def set_date(self, ds=None):
        """
        This method will create a relation between the organization and the date. Relation type is 'On'.
        Organization Node must be available for this method.
        @param ds: Datestamp
        @return:
        """
        date_node = ns.date_node(ds)   # Get Date (day) node
        ns.create_relation(from_node=self.org_node, rel="On", to_node=date_node)
        return

    def set_org_type(self, new_org_type, curr_org_type=None):
        """
        This method will set or update the Organization Type. In case of update Organization Type, then the current link
        needs to be removed, and links between Races need to be updated. In case new organization type is 'Deelname',
        then all races will be updated to 'Deelname'. In case new organization type is 'Wedstrijd', then all races will
        be updated to 'Bijwedstrijd' since it is not possible to guess the 'Hoofdwedstrijd'. The user needs to remember
        to update the 'Hoofdwedstrijd'. (Maybe send a pop-up message to the user?)
        @param new_org_type:
        @param curr_org_type:
        @return:
        """
        # First get node and node_id for Organization Type Wedstrijd and Organization Type Deelname
        prop_type = {
            "name": "Wedstrijd"
        }
        org_type_wedstrijd = ns.get_node("OrgType", **prop_type)
        org_type_wedstrijd_id = org_type_wedstrijd["nid"]
        prop_type["name"] = "Deelname"
        org_type_deelname = ns.get_node("OrgType", **prop_type)
        org_type_deelname_id = org_type_deelname["nid"]
        prop_type["name"] = "Bijwedstrijd"
        race_type_wedstrijd = ns.get_node("RaceType", **prop_type)
        prop_type["name"] = "Deelname"
        race_type_deelname = ns.get_node("RaceType", **prop_type)
        # Set new_org_type for Organization
        if new_org_type == 1:
            org_type_node = org_type_wedstrijd
            race_type_node = race_type_wedstrijd
        elif new_org_type == 2:
            org_type_node = org_type_deelname
            race_type_node = race_type_deelname
        else:
            logging.error("Unrecognized New Organization Type: {org_type}".format(org_type=new_org_type))
            return False
        ns.create_relation(from_node=self.org_node, to_node=org_type_node, rel="type")
        # Remove curr_org_type for Organization
        if curr_org_type:
            if curr_org_type == 1:
                org_type_node_id = org_type_wedstrijd_id
            elif curr_org_type == 2:
                org_type_node_id = org_type_deelname_id
            else:
                logging.error("Unrecognized Current Organization Type: {org_type}".format(org_type=curr_org_type))
                return False
            ns.remove_relation(start_nid=self.org_id, end_nid=org_type_node_id, rel_type="type")
        # Set new_org_type for all races in Organization
        # Get all races for this organization
        races = ns.get_end_nodes(self.org_id, "has")
        # Set all race types.
        for race_id in races:
            set_race_type(race_id, race_type_node)
        return


class Race:
    """
    This class instantiates to a race. This can be done as a new race that links to an organization, in which case
    org_id needs to be specified, or it can be done as a race node ID (in which case org_id should be none).
    """
    def __init__(self, org_id=None, race_id=None):
        """
        Define the Race object.
        @param org_id: Node ID of the Organization, used to create a new race.
        @param race_id: Node ID of the Race, to handle an existing race.
        @return:
        """
        self.name = 'NotYetDefined'
        self.label = 'NotYetDefined'
        self.org_id = 'NotYetDefined'
        self.race_id = 'NotYetDefined'
        if org_id:
            self.org_id = org_id
        elif race_id:
            self.node_set(nid=race_id)

    def find(self, racetype_id):
        """
        This method searches for the race of the specified type and name in the organization. If found, True will be
        returned, else False.
        Note that racetype_id is the only parameter required, since race name and org_id are known as part of Race
        Object.

        :param racetype_id: Type of the Race

        :return: True if a race is found for this organization and racetype, False otherwise.
        """
        try:
            (race_nid, org_name) = ns.get_race_in_org(org_id=self.org_id, racetype_id=racetype_id, name=self.name)
        except TypeError:
            return False
        else:
            self.race_id = race_nid
            self.label = self.set_label()
            return True

    def add(self, name, racetype=None):
        """
        This method will check if the race is registered for this organization. If not, the race graph object
        (exists of race name with link to race type and the organization) will be created.

        :param name: Name of the race

        :param racetype: 1 then Hoofdwedstrijd. If False: then calculate (bijwedstrijd or Deelname).

        :return: True if the race has been registered, False if it existed already.
        """
        # Todo - add tests on race type: deelname must be for each race of organization, hoofdwedstrijd only one.
        self.name = name
        org_type = get_org_type(self.org_id)
        if racetype:
            # RaceType defined, so it must be Hoofdwedstrijd.
            racetype = "Hoofdwedstrijd"
        elif org_type == "Wedstrijd":
            racetype = "Bijwedstrijd"
        else:
            racetype = "Deelname"
        racetype_node = get_race_type_node(racetype)
        racetype_id = racetype_node["nid"]
        if self.find(racetype_id):
            # No need to register (Race exist already).
            return False
        else:
            # Race for Organization does not yet exist, register it.
            props = {
                "name": name
            }
            race_node = ns.create_node("Race", **props)
            self.race_id = race_node["nid"]
            org_node = ns.node(self.org_id)
            ns.create_relation(from_node=org_node, rel="has", to_node=race_node)
            set_race_type(race_id=ns.node_id(race_node), race_type_node=racetype_node)
            # Set organization parameters by finding the created organization
            self.find(racetype_id)
            return True

    def edit(self, name):
        """
        This method will update the name of the race. It is not possible to modify the race type in this step.
        @param name: Name of the race
        @return: True if the race has been updated, False otherwise.
        """
        # Todo - add tests on race type: deelname must be for each race of organization, hoofdwedstrijd only one.
        self.name = name
        props = dict(name=self.name, nid=self.race_id)
        ns.node_update(**props)
        return True

    def node_set(self, nid=None):
        """
        Given the node_id, this method will configure the race object.
        @param nid: Node ID of the race node.
        @return: Fully configured race object.
        """
        self.race_id = nid
        race_node = ns.node(self.race_id)
        self.name = race_node['name']
        self.org_id = self.get_org_id()
        self.label = self.set_label()
        return

    def get_org_id(self):
        """
        This method set and return the org_id for a race node_id. A valid race_id must be set.
        @return: org_id
        """
        org_node_nid = ns.get_start_node(end_node_id=self.race_id, rel_type="has")
        return org_node_nid

    def get_name(self):
        """
        This method get the name of the race.
        @return: org_id
        """
        return self.name

    def get_racetype(self):
        """
        This method will return type of the race.
        @return: Type of the race: Hoofdwedstrijd, Bijwedstrijd or Deelname
        """
        racetype_node_id = ns.get_end_node(start_node_id=self.race_id, rel_type="type")
        racetype_node = ns.node(racetype_node_id)
        return racetype_node["name"]

    def set_label(self):
        """
        This method will set the label for the race. Assumptions are that the race name and the organization ID are set
        already.
        @return:
        """
        org_node = ns.node(self.org_id)
        org_name = org_node["name"]
        self.label = "{race_name} ({org_name})".format(race_name=self.name, org_name=org_name)
        return self.label


class Location:
    def __init__(self, loc):
        self.loc = loc

    def find(self):
        """
        Find the location node
        @return:
        """
        props = {
            "city": self.loc
        }
        loc = ns.get_node("Location", **props)
        return loc

    def add(self):
        if not self.find():
            ns.create_node("Location", city=self.loc)
            return True
        else:
            return False

    def get_node(self):
        """
        This method will get the node that is associated with the location. If the node does not exist already, it will
        be created.
        @return:
        """
        self.add()    # Register if required, ignore else
        node = self.find()
        return node


def organization_list():
    """
    This function will return a list of organizations. Each item in the list is a dictionary with fields date,
    organization, city, id (for organization nid) and type.

    :return:
    """
    return ns.get_organization_list()


def organization_delete(org_id=None):
    """
    This method will delete an organization. This can be done only if there are no more races attached to the
    organization. If an organization is removed, then check is done for orphan date and orphan location. If available,
    these will also be removed.
    @param org_id:
    @return:
    """
    if ns.get_end_nodes(start_node_id=org_id, rel_type="has"):
        logging.info("Organization with id {org_id} cannot be removed, races are attached.".format(org_id=org_id))
        return False
    else:
        # Remove Organization
        logging.debug("trying to remove org")
        ns.remove_node_force(org_id)
        # Check if this results in orphan dates, remove these dates
        logging.debug("Then trying to remove date")
        ns.clear_date()
        # Check if this results in orphan locations, remove these locations.
        logging.debug("Trying to delete organization")
        ns.clear_locations()
        logging.debug("All done")
        logging.info("Organization with id {org_id} removed.".format(org_id=org_id))
        return True


def get_org_id(race_id):
    """
    This method will return the organization ID for a Race ID: Organization has Race.
    @param race_id: Node ID of the race.
    @return: Node ID of the organization.
    """
    org_id = ns.get_start_node(end_node_id=race_id, rel_type="has")
    return org_id


def get_org_type(org_id):
    """
    This method will get the organization Type for this organization. Type can be 'Wedstrijd' or 'Deelname'.
    @param org_id: Node ID of the Organization.
    @return: Type of the Organization: Wedstrijd or Deelname, or False in case type could not be found.
    """
    org_type_id = ns.get_end_node(start_node_id=org_id, rel_type="type")
    org_type_node = ns.node(org_type_id)
    if org_type_node:
        return org_type_node["name"]
    else:
        return False


def get_org_type_node(org_type_id):
    """
    This method will find the Organization Type Node.
    @param org_type_id: RadioButton selected for Organization Type.
    @return: Organization Type Node. "Wedstrijd" if org_type_id is 1, "Deelname" in every other case.
    """
    if org_type_id == 1:
        name = "Wedstrijd"
    else:
        name = "Deelname"
    props = {
        "name": name
    }
    return ns.get_node("OrgType", **props)


def get_race_type_node(racetype):
    """
    This method will return the racetype node associated with this racetype.
    @param racetype: Racetype specifier (Hoofdwedstrijd, Bijwedstrijd, Deelname)
    @return: Racetype Node, or False if it could not be found.
    """
    if racetype in ["Hoofdwedstrijd", "Bijwedstrijd", "Deelname"]:
        # RaceType defined, so it must be Hoofdwedstrijd.
        props = {
            "name": racetype
        }
        racetype_node = ns.get_node("RaceType", **props)
        return racetype_node
    else:
        logging.error("RaceType unknown: {racetype}.".format(racetype=racetype))
        return False


def get_races_for_org(org_id):
    """
    This method will return the list of races for an Organization ID: Organization has Race.
    @param org_id: Node ID of the Organization.
    @return: List of node IDs of races.
    """
    races = ns.get_end_nodes(start_node_id=org_id, rel_type="has")
    return races


def race_list(org_id):
    """
    This function will return a list of races for an organization ID
    @param org_id: nid of the organization
    @return: List of races (empty list if there are no races).
    """
    return ns.get_race_list(org_id)


def race_label(race_id):
    """
    This function will return the label for the Race nid
    @param race_id:
    @return:
    """
    record = ns.get_race_label(race_id)
    label = "{day:02d}-{month:02d}-{year} - {city}, {race} ({d})"\
        .format(race=record["race"], city=record["city"], d=record["type"],
                day=record["day"], month=record["month"], year=record["year"])
    return label


def races4person(pers_id):
    """
    This method is pass-thru for a method in neostore module.
    This method will get a list of race_ids per person, sorted on date. The information per race will be provided in
    a list of dictionaries. This includes date, organization, type of race, and race results.

    :param pers_id:

    :return: list of Participant (part),race, date, organization (org) and racetype Node dictionaries in date
    sequence.
    """
    recordlist = ns.get_race4person(pers_id)
    # races = [{'race_id': record["race_id"], 'race_label': race_label(record["race_id"])} for record in recordlist]
    return recordlist


def races4person_org(pers_id):
    """
    This method gets the result of races4person method, then converts the result in a dictionary with key org_nid and
    value race dictionary.

    :param pers_id:

    :return: Dictionary with key org_nid and value dictionary of node race attributes for the person. This can be used
    for the Results Overview page.
    """
    races = races4person(pers_id=pers_id)
    race_org = {}
    for race in races:
        race_org[race["org"]["nid"]] = dict(
            race=race["race"],
            part=race["part"]
        )
    return race_org


def race_delete(race_id=None):
    """
    This method will delete a race. This can be done only if there are no more participants attached to the
    race.
     race_id: Node ID of the race to be removed.
    @return: True if race is removed, False otherwise.
    """
    if ns.get_start_nodes(end_node_id=race_id, rel_type="participates"):
        logging.info("Race with id {race_id} cannot be removed, participants are attached.".format(race_id=race_id))
        return False
    else:
        # Remove Organization
        ns.remove_node_force(race_id)
        logging.info("Race with id {race_id} removed.".format(race_id=race_id))
        return True


def person_list(nr_races=None):
    """
    Return the list of persons as person objects.
    @param nr_races: if True then add number of races for the person to the list.
    @return: List of persons objects. Each person is represented in a list with nid and name of the person.
    """
    res = ns.get_nodes('Person')
    person_arr = []
    for node in res:
        attribs = [node["nid"], node["name"]]
        if nr_races:
            attribs.append(len(ns.get_race4person(person_id=node["nid"])))
        person_arr.append(attribs)
    if nr_races:
        person_arr.sort(key=lambda x: -x[2])
    else:
        person_arr.sort(key=lambda x: x[1])
    return person_arr


def person4participant(part_id):
    """
    This method will get the person name from a participant ID. First it will convert the participant ID to a
    participant node. Then it gets the (reverse) relation ('is') from participant to person.
    Finally it will return the id and the name of the person in a hash.
    @param part_id: Node ID of the participant.
    @return: Person dictionary with name and nid, or False if no person found for participant id nid.
    """
    person_nid = ns.get_start_node(end_node_id=part_id, rel_type="is")
    if person_nid:
        person_node = ns.node(person_nid)
        person_name = person_node["name"]
        return dict(name=person_name, nid=person_nid)
    else:
        logging.error("Cannot find person for participant node nid: {part_id}".format(part_id=part_id))
        return False


def participant_list(race_id):
    """
    Returns the list of participants in hash of id, name.
    @param race_id: ID of the race for which current participants are returned
    @return: List of Person Objects. Each person object is represented as a list with id, name of the participant.
    """
    res = ns.get_start_nodes(end_node_id=race_id, rel_type="participates")
    part_arr = []
    for part_nid in res:
        person_nid = ns.get_start_node(end_node_id=part_nid, rel_type="is")
        person_node = ns.node(person_nid)
        attribs = [person_node["nid"], person_node["name"]]
        part_arr.append(attribs)
    return part_arr


def get_cat4part(part_nid):
    """
    This method will return category for the participant. Category will be 'Dames' or 'Heren'.
    @param part_nid: Nid of the participant node.
    @return: Category (Dames or Heren), or False if no category could be found.
    """
    return ns.get_cat4part(part_nid)


def points_position(pos):
    """
    This method will return points for a specific position.
    Points are in sequence of arrival: 50 - 45 - 40 - 39 - 38 - ...
    :param pos: Position in the race
    :return: Points associated for this position. Minimum is one point.
    """
    if pos == 1:
        points = 50
    elif pos == 2:
        points = 45
    elif pos == 3:
        points = 40
    else:
        points = 39-pos
    if points < 15:
        points = 15
    return points


def points_for_race(race_id):
    """
    This method will calculate the points for a race and the relative position. The relative position is the position
    in relation to other OLSE runners in the race.
    If race type is 'Deelname', then points_deelname function is
    called. Else points for every race in the organization need to be recalculated.
    :param race_id:
    :return:
    """
    race_obj = Race(race_id=race_id)
    race_type = race_obj.get_racetype()
    if race_type == "Deelname":
        points_deelname(race_id)
    else:
        org_id = race_obj.get_org_id()
        races = get_races_for_org(org_id=org_id)
        for rid in races:
            r_obj = Race(race_id=rid)
            r_type = r_obj.get_racetype()
            if r_type == "Hoofdwedstrijd":
                points_hoofdwedstrijd(rid)
            else:
                points_bijwedstrijd(rid)
    return


def points_bijwedstrijd(race_id):
    """
    This method will assign points to participants in a race for type 'Bijwedstrijd'. It will add 'bijwedstrijd' points
    to every participant. Participant list is sufficient, sequence list is not required. But this function does not
    exist (I think).
    :param race_id:
    :return:
    """
    # Get min value from hoofdwedstrijd.
    # If found, go to next value (45,40,39, ...)
    # If not found, assign 50.
    # Count number of Category participants in the Hoofdwedstrijd. Points for participant is next available one, after
    # all participants on main race have been calculated.
    # This allows to calculate points for the participant.
    main_race_id = ns.get_main_race_id(race_id)
    d_parts = ns.get_nr_participants(race_id=main_race_id, cat="Dames")
    m_parts = ns.get_nr_participants(race_id=main_race_id, cat="Heren")
    d_rel_pos = d_parts + 1
    m_rel_pos = m_parts + 1
    d_points = points_position(d_rel_pos)
    m_points = points_position(m_rel_pos)
    # Now add points for everyone in the race.
    node_list = ns.get_participant_seq_list(race_id)
    if node_list:
        for part in node_list:
            mf = get_cat4part(part["nid"])
            if mf == "Heren":
                points = m_points
                rel_pos = m_rel_pos
            else:
                points = d_points
                rel_pos = d_rel_pos
            props = dict(nid=part["nid"], points=points, rel_pos=rel_pos)
            ns.node_set_attribs(**props)
    return


def points_hoofdwedstrijd(race_id):
    """
    This method will assign points to participants in a race. It gets the participant nids in sequence of arrival. For
    each participant, it will extract Category (Dames, Heren) then assign points for the participant.
    This method should be called for 'Hoofdwedstrijd' only.
    :param race_id:
    :return:
    """
    cnt = dict(Dames=0, Heren=0)
    node_list = ns.get_participant_seq_list(race_id)
    if node_list:
        for part in node_list:
            mf = get_cat4part(part["nid"])
            cnt[mf] += 1
            points = points_position(cnt[mf])
            rel_pos = cnt[mf]
            # Set points for participant
            props = dict(nid=part["nid"], points=points, rel_pos=rel_pos)
            ns.node_set_attribs(**props)
    return


def points_deelname(race_id):
    """
    This method will assign points to participants in a race for type 'Deelname'. It will add 'deelname' points to
    every participant. Participant list is sufficient, sequence list is not required. But this function does not
    exist (I think).
    :param race_id:
    :return:
    """
    node_list = ns.get_participant_seq_list(race_id)
    points = 20
    if node_list:
        for part in node_list:
            props = dict(nid=part["nid"], points=points)
            ns.node_set_attribs(**props)
    return


def points_sum(point_list):
    """
    This function will calculate the total of the points for this participant. For now, the sum of all points is
    calculated.
    :param point_list: list of the points for the participant.
    :return: sum of the points
    """
    nr_races = 7
    add_points_per_race = 10
    max_list = sorted(point_list)[-nr_races:]
    if len(point_list) > nr_races:
        add_points = (len(point_list) - nr_races) * add_points_per_race
    else:
        add_points = 0
    points = sum(max_list) + add_points
    return points


def results_for_category(cat):
    """
    This method will calculate the points for all participants in a category.

    :param cat: Category to calculate the points

    :return: Sorted list with tuples (name, points, number of races, nid for person).
    """
    res = ns.points_per_category(cat)
    # 1. Add points to list per person
    result_list = {}
    result_total = []
    nid4name = {}
    while res.forward():
        rec = res.current()
        # Remember the nid for this participant.
        nid4name[rec["name"]] = rec["nid"]
        try:
            result_list[rec["name"]].append(rec["points"])
        except KeyError:
            result_list[rec["name"]] = [rec["points"]]
    # 2. Calculate points per person
    for name in result_list:
        result_total.append([name, points_sum(result_list[name]), len(result_list[name]), nid4name[name]])
    result_sorted = sorted(result_total, key=lambda x: -x[1])
    return result_sorted


def participant_seq_list(race_id):
    """
    This method will collect the people in a race in sequence of arrival.

    :param race_id: nid of the race for which the participants are returned in sequence of arrival.

    :return: List of participants items in the race. Each item is a tuple of the person dictionary (from the person
     object) and the participant dictionary (the properties of the participant node). False if no participants in the
     list.
    """
    node_list = ns.get_participant_seq_list(race_id)
    if node_list:
        finisher_list = []
        # If there are finishers, then recordlist has one element, which is a nodelist
        for part in node_list:
            part_obj = Participant(part_id=part["nid"])
            person_obj = Person(person_id=part_obj.get_person_nid())
            person_dict = person_obj.get_dict()
            pers_part_tuple = (person_dict, dict(part))
            finisher_list.append(pers_part_tuple)
        return finisher_list
    else:
        return False


def participant_after_list(race_id):
    """
    This method will return the participant sequence list as a SelectField list. It will call participant_seq_list
    and 'prepend' a value for 'eerste aankomer' (value -1).

    :param race_id: Node ID of the race

    :return: List of the Person objects (list of Person nid and Person name) in sequence of arrival and value for
    'eerste aankomer'.
    """
    eerste = [-1, 'Eerste aankomst']
    finisher_tuple = participant_seq_list(race_id)
    if finisher_tuple:
        finisher_list = [[person['nid'], person['label']] for (person, part) in finisher_tuple]
        finisher_list.insert(0, eerste)
    else:
        finisher_list = [eerste]
    return finisher_list


def participant_last_id(race_id):
    """
    This method will return the nid of the last participant in the race. It calls check participant_after_list and
    fetches the last ID of the runner. This way no special treatment is required in case there are no participants. The
    ID of the last runner will redirect to -1 then.

    :param race_id: Node nid of the race.

    :return: nid of the Person Node of the last finisher so far in the race, -1 if no finishers registered yet.
    """
    finisher_list = participant_after_list(race_id)
    part_arr = finisher_list.pop()
    part_last = part_arr[0]
    return part_last


def participant_first_id(race_id):
    """
    This method will get the ID of the first person in the race.
    @param race_id: Node ID of the race.
    @return: Node ID of the first person so far in the race, False if no participant registered for this race.
    """
    finisher_tuple = participant_seq_list(race_id)
    if finisher_tuple:
        (person, part) = finisher_tuple[0]
        person_id = person['nid']
        return person_id
    else:
        return False


def next_participant(race_id):
    """
    This method will get the list of potential next participants. This is the list of all persons minus the people that
    have been selected already in this race. Also all people that have been selected in other races for this
    organization will no longer be available for selection.
    @param race_id:
    @return: List of the Person objects (Person nid and Person name) that can be selected as participant in the race.
    """
    # Todo: extend to participants that have been selected for this organization (one participation per race per org.)
    # Get Organization for this race
    # org_id = get_org_id(race_id)
    org_id = get_org_id(race_id)
    races = get_races_for_org(org_id)
    participants = []
    for race_id in races:
        parts_race = participant_list(race_id)
        participants += parts_race
    persons = person_list()
    next_participants = [part for part in persons if part not in participants]
    return next_participants


def racetype_list():
    """
    This method will get all the race types. It will return them as a list of tuples with race type ID and race type
    name.
    @return:
    """
    race_nodes = ns.get_nodes("RaceType")
    race_types = []
    for node in race_nodes:
        race_tuple = (node["nid"], node["name"])
        race_types.append(race_tuple)
    return race_types


def relations(node_id):
    """
    This method will return True if the node with node_id has relations, False otherwise.
    @param node_id:
    @return:
    """
    return ns.relations(node_id)


def remove_node(node_id):
    """
    This function will remove the node with node ID node_id, on condition that there are no more relations to the node.
    @param node_id:
    @return: True if node is deleted, False otherwise
    """
    return ns.remove_node(node_id)


def remove_node_force(node_id):
    """
    This function will remove the node with node ID node_id, including relations with the node.
    @param node_id:
    @return: True if node is deleted, False otherwise
    """
    return ns.remove_node_force(node_id)


def set_race_type(race_id=None, race_type_node=None):
    """
    Check if old node type is defined. If so, remove the link.
    Then add new link.

    :param race_id: Node ID for the race

    :param race_type_node:

    :return:
    """
    race_node = ns.node(race_id)
    # Check if there is a link now.
    curr_race_type_id = ns.get_end_node(race_id, "type")
    if curr_race_type_id:
        ns.remove_relation(race_id, curr_race_type_id, "type")
    ns.create_relation(from_node=race_node, to_node=race_type_node, rel="type")
    return
