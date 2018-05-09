"""Functions to serve as REST API routes."""

from pprint import pprint
import flask
import json
from flask import request
from database import get_db
from search import *
from bson import objectid
from bson.objectid import ObjectId
from bson.errors import InvalidId

import sendgrid
import os
from sendgrid.helpers.mail import *


class APIException(Exception):
    """Exception type for REST API."""
    
    def __init__(self, status_code=400, message='', payload=None):
        """Initialize exception."""
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    
    def to_dict(self):
        """Convert exception to dict for later conversion to JSON."""
        output = dict(self.payload or ())
        output["status_code"] = self.status_code
        output["message"] = self.message
        return output


# App is a single object used by all the code modules in this package
app = flask.Flask(__name__)  # pylint: disable=invalid-name


@app.errorhandler(APIException)
def handle_api_exception(error):
    """Return JSON error messages instead of default HTML."""
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route("/")
def hello():
    """Display message on index screen."""
    return "<h1 style='color:blue'>Hello There, Gainzzzasasas!</h1>"


# Sahil's testing route for verification code handling
@app.route("/applications/")
def view_applications():
    return 'hello'


@app.route("/api/v1/sendapplication/", methods=["POST"])
def send_application_email():
    """Send application email to mentors."""
    # pprint(request.json)
    
    TEXT = ('Dear ' + str(request.json['email']) + ',\n\nThank you for expressing your interest in' +
            ' becoming a mentor for theRightFit.\n\nAs a next step, we would like' +
            ' to invite you to fill in our mentor application form at https://goo.gl/forms/ft1mzyiQbJkazhkQ2' +
            '\n\nIf you have any questions, feel free to reach out to us directly ' +
            'at apply.therightfit@gmail.com.\n\nThanks,\n\ntheRightFit Team')
        
    sg = sendgrid.SendGridAPIClient(apikey='')
    from_email = Email("apply.therightfit@gmail.com")
    to_email = Email(str(request.json['email']))
    subject = "theRightFit Mentor Application"
    content = Content("text/plain", TEXT)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)
    return 'Application email sent!', 200


@app.route("/api/v1/verificationemail/<id>/", methods=["GET"])
def send_verification_code(id):
    """Send verification email."""
    db = get_db()
    users = db.users
    
    # Check if the user_id is valid BSON
    if objectid.ObjectId.is_valid(str(id)) is False:
        raise APIException(status_code=404, message='user_id not found')
    
    # Search database for the specific mentee
    cursor = users.find({"role": "Mentor", "_id": ObjectId(str(id))})

    full_name = ""
    email_address = ""
    for document in cursor:
        full_name = document['name']
        email_address = document['email']


    TEXT = ('Dear ' + str(full_name) + ',\n\nCongratulations! You have been approved to' +
        ' become a mentor for theRightFit.\n\n Your unique verification code is: ATPUG\n\n' +
        'Please enter this in the application verification screen to get started.' +
        '\n\nIf you have any questions, feel free to reach out to us directly ' +
        'at apply.therightfit@gmail.com.\n\nThanks,\n\ntheRightFit Team')

    sg = sendgrid.SendGridAPIClient(apikey='')
    from_email = Email("apply.therightfit@gmail.com")
    to_email = Email(str(email_address))
    subject = "theRightFit Mentor Application Approval"
    content = Content("text/plain", TEXT)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)
    
    return 'Verification email sent!', 200


@app.route("/api/v1/mentees/", methods=["GET"])
def get_mentee_list():
    """Return list of Mentees in database."""
    # Get db object and users table
    db = get_db()
    users = db.users
    
    # Search database for mentees
    cursor = users.find({"role": "Mentee"})
    
    context = {'mentees': []}
    
    for document in cursor:
        temp = document
        del temp['_id']
        context['mentees'].append(temp)
    
    context['url'] = "/api/v1/mentees/"
    return flask.jsonify(**context)



@app.route("/api/v1/mentees/<user_id>/", methods=["GET"])
def get_mentee(user_id, with_partners=1):
    """Lookup a Mentee based on their user_id."""
    # Get db object and users table
    db = get_db()
    users = db.users
    
    # Check if the user_id is a string
    if not isinstance(user_id, str):
        raise APIException(status_code=400, message='user_id not a string')
    
    # Search database for the specific mentee
    cursor = users.find({"role": "Mentee", "user_id": user_id})

    # Raise exception if no user is found
    if cursor.count() is 0:
        raise APIException(status_code=404, message='no Mentee with user_id found')
    
    context = {}
    
    for document in cursor:
        temp = document
        del temp['_id']
        
        if with_partners is 0:
            del temp['partners']
            return temp
        
        if with_partners is 1:
            temp2 = []
            for partner_id in document['partners']:
                #Gets mentor profile but without its 'partners' field
                val = get_mentor(partner_id, with_partners=0)
                temp2.append(val)
            temp['partners'] = temp2
        
        context = temp

    context['url'] = "/api/v1/mentees/" + user_id + "/"
    return flask.jsonify(**context)



@app.route("/api/v1/mentors/", methods=["GET"])
def get_mentor_list():
    """Return list of Mentors in the database."""
    # Get db object and users table
    db = get_db()
    users = db.users
    
    # Search database for mentors
    cursor = users.find({"role": "Mentor"})
    
    context = {'mentors': []}
    
    for document in cursor:
        temp = document
        del temp['_id']
        context['mentors'].append(temp)
    
    context['url'] = "/api/v1/mentors/"
    return flask.jsonify(**context)


@app.route("/api/v1/mentors/<user_id>/", methods=["GET"])
def get_mentor(user_id, with_partners=1):
    """Lookup a mentor based on their user id."""
    # Get db object and users table
    db = get_db()
    users = db.users
    
    # Check if the user_id is a string
    if not isinstance(user_id, str):
        raise APIException(status_code=400, message='user_id not a string')
    
    # Search database for the specific mentor
    cursor = users.find({"role": "Mentor", "user_id": user_id})

    # Raise exception if no user is found
    if cursor.count() is 0:
        raise APIException(status_code=404, message='no Mentor with user_id found')
    
    context = {}
    
    for document in cursor:
        temp = document
        del temp['_id']
        
        if with_partners is 0:
            del temp['partners']
            return temp
        
        if with_partners is 1:
            temp2 = []
            for partner_id in document['partners']:
                #Gets mentee profile but without its 'partners' field
                val = get_mentee(partner_id, with_partners=0)
                temp2.append(val)
            temp['partners'] = temp2
        
        context = temp

    context['url'] = "/api/v1/mentors/" + user_id + "/"
    return flask.jsonify(**context)


@app.route("/api/v1/role/<user_id>/", methods=["GET"])
def get_role(user_id):
    """Return the role (Mentee or Mentor) of a user with the specified user_id"""
    # Get db object and users table
    db = get_db()
    users = db.users

    # Check if user_id is a valid user in the users collection
    cursor = users.find({"user_id": str(user_id)})
    # if cursor.count() is 0:
    #     raise APIException(status_code=404, message='user_id not found')
    # elif cursor.count() > 1:
    #     raise APIException(status_code=500, message="Error, multiple users with same user_id found, which is not allowed")

    context = {}

    if cursor.count() is 0:
        context['role'] = ""
    elif cursor.count() > 1:
        raise APIException(status_code=500, message="Error, multiple users with same user_id found, which is not allowed")
    else:
        for document in cursor:
            context['role'] = document['role']

    context['url'] = "/api/v1/role/" + str(user_id) + "/"
    return flask.jsonify(**context)



#TODO: check for upper and lower case permutations
@app.route("/api/v1/exercises/<name>/", methods=["GET"])
def get_exercise(name):
    """Return a single exercise that matches the name"""
    # Get db object and exercises table
    db = get_db()
    exercises = db.exercises
    
    # Search database for exercises with matching name
    cursor = exercises.find({"name": str(name)})
    if cursor.count() is 0:
        raise APIException(status_code=404, message='exercise with specified name not found')
    
    context = {}
    for document in cursor:
        temp = document
        temp['exercise_id'] = str(document['_id'])
        del temp['_id']
        context = temp
    
    context['url'] = "/api/v1/exercises/" + name + "/"
    return flask.jsonify(**context)


#TODO: return an error if user_id does not exist
@app.route("/api/v1/<user_id>/workouts/", methods=["GET"])
def get_workouts(user_id):
    """Return all the workouts that are either made by or made for user_id"""
    # Get db object and exercises table
    db = get_db()
    workouts = db.workouts
    
    # Check if the user_id is a string
    if not isinstance(user_id, str):
        raise APIException(status_code=400, message='user_id not a string')
    
    # List all workouts that include the user
    context = {'workouts': []}
    cursor = workouts.find({"$or":[ {"mentor_id": user_id}, {"mentee_id": user_id}]})
    for document in cursor:
        temp = document
        temp['workout_id'] = str(document['_id'])
        del temp['_id']
        context['workouts'].append(temp)
    
    context['url'] = "/api/v1/" + user_id + "/workouts/"
    return flask.jsonify(**context)


# TODO: return error if user_id does not have workout with workout_id
@app.route("/api/v1/<user_id>/workouts/<workout_id>/", methods=["GET"])
def get_workout_by_id(user_id, workout_id):
    """Return specific workout that is either made by or made of user with specified id"""
    # Get db object and exercises table
    db = get_db()
    workouts = db.workouts
    
    # Check if the user id is a string and workout id is a valid BSON
    if not isinstance(user_id, str):
        raise APIException(status_code=400, message='user_id not a string')
    if objectid.ObjectId.is_valid(workout_id) is False:
        raise APIException(status_code=400, message='workout_id not a valid BSON')

    # List the workout that includes the user and has the specific workout_id
    context = {}
    cursor = workouts.find({"$and":[{"_id":ObjectId(workout_id)},
                                    {"$or":[ {"mentor_id": user_id}, {"mentee_id": user_id}]} ]})
    for document in cursor:
        temp = document
        temp['workout_id'] = str(document['_id'])
        del temp['_id']
        context = temp

    context['url'] = "/api/v1/" + user_id + "/workouts/" + str(workout_id) + "/"
    return flask.jsonify(**context)


@app.route("/api/v1/<user_id>/requests/", methods=["GET"])
def get_all_requests(user_id):
    """Return info about all active and non active requests that the user with <id> is involved in"""
    db = get_db()
    requests = db.requests
    
    # Check if the user_id is a string
    if not isinstance(user_id, str):
        raise APIException(status_code=400, message='user_id not a string')
    
    cursor = requests.find({"$or":[ {"mentor_id": user_id}, {"mentee_id": user_id}]})
    context = {"requests": []}
    for document in cursor:
        temp = document
        temp['request_id'] = str(document['_id'])
        temp['mentee_profile'] =  get_mentee(document['mentee_id'], with_partners=0)
        temp['mentor_profile'] =  get_mentor(document['mentor_id'], with_partners=0)
        del temp['_id']
        del temp['mentor_id']
        del temp['mentee_id']
        context["requests"].append(temp)
    
    context['url'] = "/api/v1/" + user_id + "/requests/"
    return flask.jsonify(**context)


@app.route("/api/v1/requests/<request_id>/", methods=["GET"])
def get_request_by_id(request_id):
    """Return info about the active requests with <request_id>."""
    db = get_db()
    requests = db.requests
    
    # Check if request_id is valid BSON
    if objectid.ObjectId.is_valid(request_id) is False:
        raise APIException(status_code=400, message='request_id not a valid BSON')
    
    cursor = requests.find({"_id": ObjectId(request_id)})
    context = {}
    for document in cursor:
        temp = document
        temp['request_id'] = str(document['_id'])
        temp['mentee_profile'] =  get_mentee(document['mentee_id'], with_partners=0)
        temp['mentor_profile'] =  get_mentor(document['mentor_id'], with_partners=0)
        del temp['_id']
        del temp['mentor_id']
        del temp['mentee_id']
        context = temp
    
    context['url'] = "/api/v1/requests/" + str(request_id) + "/"
    return flask.jsonify(**context)


# ---------------------------------------HELPER FUNCTIONS FOR PUT/POST SANITIZING AND VERIFICATION ------------------------ #
# Validate/sanatize data for both the add user and edit user routes
def validate_user_data(data, is_adding_new_user):
    if not 'role' in data:
        raise APIException(status_code=400, message='data must have a role field')
    elif not isinstance(data['role'], str):
        raise APIException(status_code=400, message='role must be a string')

    expected_fields = ['name', 'role', 'phone', 'email', 'VenmoUsername', 'gender', 'height', 'weight', 'age',
                       'tags', 'bio', 'location', 'pic_url', 'rating'] # 'partners' not expected if editing user

    if is_adding_new_user:
        expected_fields.append('partners')
    
    if data['role'].lower() == "mentor":
        data['role'] = "Mentor" #Sanitizing
        expected_fields.append('accepting_clients')
        expected_fields.append('rates')
    elif data['role'].lower() == "mentee":
        data['role'] = "Mentee" #Sanitizing
    else:
        raise APIException(status_code=400, message="user has to be either a Mentor or a Mentee")

    # Raise error if the feilds in data don't match the expected fields
    if not set(expected_fields) == set(data):
        raise APIException(status_code=400, message='data does not match the expected fields')
    
    if not ( isinstance(data['location'], dict) and isinstance(data['height'], dict) and isinstance(data['weight'], dict) and
            isinstance(data['tags'], list) and isinstance(data['rating'], dict)):
        raise APIException(status_code=400, message='Expected dictionary or list fields, incorrect data type')
            
    expected_location_subfields = ["city", "state"]
    if not set(expected_location_subfields) == set(data['location']):
        raise APIException(status_code=400, message='location must have exactly a city and a state')
    expected_height_subfields = ["feet", "inches"]
    if not set(expected_height_subfields) == set(data['height']):
        raise APIException(status_code=400, message='height must have exactly feet and inches')
    expected_weight_subfields = ["lbs"]
    if not set(expected_weight_subfields) == set(data['weight']):
        raise APIException(status_code=400, message='weight must only have lbs')
    expected_rating_subfields = ["number_of_ratings", "total_score"]
    if not set(expected_rating_subfields) == set(data['rating']):
        raise APIException(status_code=400, message='rating must have only/both number_of_ratings and total_score')
    if data['role'] is "Mentor":
        if not (isinstance(data['rates'], dict)):
            raise APIException(status_code=400, message='rates needs to be a dict, it is not')
        expected_rates_subfields = ["try", "loyalty"]
        if not set(expected_rates_subfields) == set(data['rates']):
            raise APIException(status_code=400, message='rates must have only/both try and loyalty')

    # Check that each field is its expected data type
    NumberTypes = (int, float)
    if not ( isinstance(data['name'], str) and isinstance(data['role'], str) and isinstance(data['phone'], str)
            and isinstance(data['email'], str) and isinstance(data['VenmoUsername'], str) and isinstance(data['gender'], str)
            and isinstance(data['age'], NumberTypes) and isinstance(data['bio'], str) and isinstance(data['pic_url'], str)):
        raise APIException(status_code=400, message='at least one string or number feild is not the correct datatype')
    for tag in data['tags']:
        if not isinstance(tag, str):
            raise APIException(status_code=400, message='tags must be strings')
    if not ( isinstance(data['rating']['number_of_ratings'], NumberTypes)
            and isinstance(data['rating']['total_score'], (int)) ):
        raise APIException(status_code=400, message='total_score must be ints or long, number_of_ratings must be a number (rating)')
    if not ( isinstance(data['height']['feet'], NumberTypes)
            and isinstance(data['height']['inches'], NumberTypes) ):
        raise APIException(status_code=400, message='feet and inches (height) must be numbers')
    if not isinstance(data['weight']['lbs'], NumberTypes):
        raise APIException(status_code=400, message='lbs (weight) must be a number')
    if not ( isinstance(data['location']['city'], str)
            and isinstance(data['location']['state'], str) ):
        raise APIException(status_code=400, message='city and state (location) must be strings')
    if data['role'] is "Mentor":
        if not isinstance(data['accepting_clients'], bool):
            raise APIException(status_code=400, message='accepting_clients must be a boolean')
        if not ( isinstance(data['rates']['try'], NumberTypes)
                and isinstance(data['rates']['loyalty'], NumberTypes) ):
            raise APIException(status_code=400, message='try and loyalty (rates) must be numbers')

    #If adding a new user, the "partners" and "rating" fields should be empty
    if is_adding_new_user:
        if not (isinstance(data['partners'], list)):
            raise APIException(status_code=400, message='when creating a user, partners needs to be an empty list, it is not')
        if not len(data['partners']) == 0:
            raise APIException(status_code=400, message='partners field must be empty when creating new user')
        if not (data['rating']['number_of_ratings'] == 0 and data['rating']['total_score'] == 0):
            raise APIException(status_code=400, message='number_of_ratings and total_score (rating) must be 0 when creating new user')
            
            
# HELPER FUNCTION FOR VALIDATING WORKOUTS WHEN ADDING OR EDITING
def validate_workout_data(data):
    """ This function only validates the contents of the workouts, so it does not take in mentor_id, mentee_id, or paid"""
    expected_fields = ['workout_name', 'workout_length', 'assigned_date', 'exercises']
    expected_date_subfields = ["month", "day", "year", "day_of_week"]
    
    # Raise error if the feilds in data don't match the expected fields
    if not set(expected_fields) == set(data):
        raise APIException(status_code=400, message='data does not match the expected fields')

    # Make sure each field is the right datatype
    if not ( isinstance(data['workout_name'], str) and isinstance(data['workout_length'], str)
            and isinstance(data['exercises'], list) and isinstance(data['assigned_date'], dict) ):
        raise APIException(status_code=400, message='one or more fields are not in their correct datatype')
            
    if not set(expected_date_subfields) == set(data['assigned_date']):
        raise APIException(status_code=400, message='date_assigned must only/exactly have month, day, year, and day_of_week')
            
    # Make sure "date_assigned" is a valid object
    if not ( isinstance(data['assigned_date']['month'], str) and isinstance(data['assigned_date']['day'], str)
            and isinstance(data['assigned_date']['year'], str) and isinstance(data['assigned_date']['day_of_week'], str)):
        raise APIException(status_code=400, message="assigned_date not correct format")

    # Validate each exercise in data
    db = get_db()
    exercises = db.exercises
    NumberTypes = (int, float)
    for exercise in data['exercises']:
        # Check for fields/format of each exerise
        expected_subfields = ["exercise_id", "exercise_name", "pic_urls", "instructions", "notes", "description"]
        if not set(expected_subfields) == set(exercise):
            raise APIException(status_code=400, message='exercises in workout do not have/match the required subfields')
        
        # Check if each field and subfield has expected data type
        if not ( isinstance(exercise['exercise_id'], str) and isinstance(exercise['exercise_name'], str)
                and isinstance(exercise['instructions'], str) and isinstance(exercise['notes'], str)
                and isinstance(exercise['description'], str) and isinstance(exercise['pic_urls'],  list)):
            raise APIException(status_code=400, message='Expected strings are not in type string (exercise subfields)')
        if not (isinstance(exercise['pic_urls'], list)):
            raise APIException(status_code=400, message='pic_urs must be a list/array')
        for pic in exercise['pic_urls']:
            if not isinstance(pic, str):
                raise APIException(status_code=400, message='Expected strings are not in type string (pic_urls)')

        # Check if the exercise id is valid BSON
        if objectid.ObjectId.is_valid(str(exercise['exercise_id'])) is False:
            raise APIException(status_code=404, message='exercise_id not found')
        
        # Check if the exercise is a valid exercise in the database
        cursor = exercises.find({"_id": ObjectId(exercise['exercise_id'])})
        if cursor.count() is 0:
            raise APIException(status_code=400, message='one or more exercise_id not found')


# -----------------------------------------------PUT REQUESTS-------------------------------------------------------#
@app.route("/api/v1/users/edit/<user_id>/", methods=["PUT"])
def edit_user(user_id):
    """Update fields in a single user from the users collection"""
    """Cannot update a user's role"""
    db = get_db()
    users = db.users
    data = request.json
    
    # Check if user_id is a string
    if not isinstance(user_id, str):
        raise APIException(status_code=400, message='user_id not a string')
    
    # Check if user_id is actually an entry in the users collection
    cursor = users.find({"user_id": user_id})
    if cursor.count() is 0:
        raise APIException(status_code=404, message='user_id does not exist yet')
    elif cursor.count() > 1:
        raise APIException(status_code=500, message='Error, multiple entries with same user_id found. user_id must be unique')
    
    # Validate that the data matches the required format
    # user_id = data['user_id']
    # del data['user_id']
    validate_user_data(data, is_adding_new_user=False)
    # data['user_id'] = user_id

    result = users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "name": data["name"],
                "phone": data["phone"],
                "email": data["email"],
                "VenmoUsername": data["VenmoUsername"],
                "gender": data["gender"],
                "height": data["height"],
                "weight": data["weight"],
                "age": data["age"],
                "bio": data["bio"],
                "tags": data["tags"],
                "location": data["location"],
                "pic_url": data["pic_url"]
            }
        }
    )
    
    if "role" not in data:
        return '', 200
    if data["role"] == "Mentor":
        result = users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "rates": data["rates"],
                    "accepting_clients": data["accepting_clients"]
                }
            }
        )
    return '', 200

            
# NOT NEEDED ANYMORE
#@app.route("/api/v1/exercises/edit/<exercise_id>/", methods=["PUT"])
#def edit_exercise(exercise_id):
#    """Update fields in a single exercise from the exercises collection"""
#    db = get_db()
#    exercises = db.exercises
#    data = request.json
#
#    # Check if exercise_id is valid BSON
#    if objectid.ObjectId.is_valid(id) is False:
#        raise APIException(status_code=400, message='exercise_id not a valid BSON')
#
#    result = exercises.update_one(
#        {"_id": ObjectId(id)},
#        {
#            "$set": {
#                "name": data["name"],
#                "pic_urls": data["pic_urls"]
#            }
#        }
#    )
#    return '', 200


@app.route("/api/v1/workouts/edit/<workout_id>/", methods=["PUT"])
def edit_workouts(workout_id):
    """Update fields in a single workout specified by <id> in the workout collections
        It does not update mentor_id or mentee_id"""
    db = get_db()
    workouts = db.workouts
    data = request.json
    
    # Check if the workout_id is valid BSON
    if objectid.ObjectId.is_valid(workout_id) is False:
        raise APIException(status_code=400, message='workout_id not a valid BSON')
    
    # Check if workout_id is actually an entry in the workouts collection
    cursor = workouts.find({"_id": ObjectId(workout_id)})
    if cursor.count() is 0:
        raise APIException(status_code=404, message='workout_id does not exist yet')
    elif cursor.count() > 1:
        raise APIException(status_code=500, message='Error, multiple entries with same workout_id found. workout_id must be unique')

    # Validate that data matches every format required
    validate_workout_data(data)

    # Update the workout
    result = workouts.update_one(
        {"_id": ObjectId(workout_id)},
        {
            "$set": {
                "workout_name": data["workout_name"],
                "workout_length": data["workout_length"],
                "assigned_date": data["assigned_date"],
                "exercises": data["exercises"]
            }
        }
    )
    return '', 200


@app.route("/api/v1/users/<mentor_id>/acceptrequest/<request_id>/", methods=["PUT"])
def accept_request(mentor_id, request_id):
    """This route is called when a Mentor hits accept on a pending request"""
    db = get_db()
    users = db.users
    requests = db.requests

    # Make sure mentor_id is a string
    if not isinstance(mentor_id, str):
        raise APIException(status_code=400, message='mentor_id must be a string')
    # Check if the request_id is valid BSON
    if objectid.ObjectId.is_valid(request_id) is False:
        raise APIException(status_code=400, message='request_id not a valid BSON')

    # Check if mentor_id is actually a Mentor
    cursor1 = users.find({"role": "Mentor", "user_id": mentor_id})
    if cursor1.count() is 0:
        raise APIException(status_code=404, message='mentor_id not a Mentor')
    # Check if request_id is an actual request, and that mentor_id is the valid Mentor in the request
    cursor2 = requests.find({"mentor_id": mentor_id, "_id": ObjectId(request_id)})
    if cursor2.count() is 0:
        raise APIException(status_code=404, message='request_id is not found or does not involve mentor_id')

    # Find out the mentee_id of in the request with <request_id>
    mentee_id = ""
    for document in cursor2:
        if document['mentor_accepted'] is True:
            raise APIException(status_code=400, message='mentor_id has already accepted the request_id')
        mentee_id = document['mentee_id']
    # Make sure that mentor_id and mentee_id only have one open transaction
    cursor3 = requests.find({"mentor_id": mentor_id, "mentee_id": mentee_id, "transaction_over": False})
    if cursor3.count() is 0:
        raise APIException(status_code=403, message='request_id is not active')
    elif cursor3.count() > 1:
        raise APIException(status_code=500, message='Error, mentor-mentee pair have multiple open transaction, which is not allowed')

    # Update the workout
    result = requests.update_one(
        {"_id": ObjectId(request_id)},
        {
            "$set": {
                "mentor_accepted": True
            }
        }
    )

    # Check if they are already partners
    cursor3 = users.find({"role": "Mentor", "user_id": mentor_id})
    are_already_partners = False
    for document in cursor3:
        if mentee_id in document['partners']:
            are_already_partners = True
    cursor4 = users.find({"role": "Mentee", "user_id": mentee_id})
    for document in cursor4:
        if mentor_id in document['partners'] and are_already_partners is False:
            raise APIException(status_code=500, message="Error, mentee_id not in mentor's partners array, but mentor_id in mentee_id's partners array")

    if are_already_partners is False:
        # Add mentee_id to mentor_id's 'partners' field and vice versa
        postid1 = users.update_one(
            { "user_id": mentor_id },
            { '$push': { "partners": mentee_id} }
        )
        postid2 = users.update_one(
            { "user_id": mentee_id },
            { '$push': { "partners": mentor_id} }
        )

    return '', 200


@app.route("/api/v1/users/<mentor_id>/denyrequest/<request_id>/", methods=["PUT"])
def deny_request(mentor_id, request_id):
    """This route is called when a Mentor hits deny on a pending request"""
    db = get_db()
    users = db.users
    requests = db.requests

    # Make sure mentor_id is a string
    if not isinstance(mentor_id, str):
        raise APIException(status_code=400, message='mentor_id must be a string')
    # Check if the request_id is valid BSON
    if objectid.ObjectId.is_valid(request_id) is False:
        raise APIException(status_code=400, message='request_id not a valid BSON')

    # Check if mentor_id is actually a Mentor
    cursor1 = users.find({"role": "Mentor", "user_id": mentor_id})
    if cursor1.count() is 0:
        raise APIException(status_code=404, message='mentor_id not a Mentor')
    # Check if request_id is an actual request, and that mentor_id is the valid Mentor in the request
    cursor2 = requests.find({"mentor_id": mentor_id, "_id": ObjectId(request_id)})
    if cursor2.count() is 0:
        raise APIException(status_code=404, message='request_id is not valid or does not involve mentor_id')
    for document in cursor2:
        if document['mentor_accepted'] is True:
            raise APIException(status_code=400, message='Cannot deny a request that aready has been accepted')

    # remove the request document from the requests collection
    result = requests.delete_one({"_id": ObjectId(request_id)})
    return '', 200


@app.route("/api/v1/users/<mentee_id>/paid/<workout_id>/", methods=["PUT"])
def pay_workout(mentee_id, workout_id):
    """This route is called when a Mentee pays for a workout"""
    db = get_db()
    users = db.users
    workouts = db.workouts
    requests = db.requests
    
    # Make sure mentee_id is a string
    if not isinstance(mentee_id, str):
        raise APIException(status_code=400, message='mentee_id must be a string')
    # Check if the request_id is valid BSON
    if objectid.ObjectId.is_valid(workout_id) is False:
        raise APIException(status_code=400, message='workout_id not a valid BSON')

    # Check if mentee_id is actually a Mentee
    cursor1 = users.find({"role": "Mentee", "user_id": mentee_id})
    if cursor1.count() is 0:
        raise APIException(status_code=404, message='mentee_id not a Mentee')
    # Check if workout_id is an actual workout, and that mentee_id is the valid Mentee in the workout
    cursor2 = workouts.find({"mentee_id": mentee_id, "_id": ObjectId(workout_id)})
    if cursor2.count() is 0:
        raise APIException(status_code=404, message='workout_id is not valid or does not involve mentee_id')
    # Make sure an open request confirms that workout_id was created by mentor_id for mentee_id
    cursor = requests.find({"mentee_id": mentee_id, "workouts_created": workout_id, "transaction_over": False})
    if cursor.count() is 0:
        raise APIException(status_code=404, message='no workout request found where workout_id was created for mentee_id, or the transaction is already over')

    request_id = ""
    transaction_will_be_over_after_this_payment = False
    for document in cursor:
        if document['mentor_accepted'] is False:
            raise APIException(status_code=400, message='Mentor is yet to accept workout request')
        if workout_id in document['workouts_paid']:
            raise APIException(status_code=400, message='this workout has already been paid for')
        if len(document['workouts_paid']) >= document['num_workouts_requested']:
            raise APIException(status_code=500, message='Error, transaction_over is false but workouts_paid has more workouts than requested')
        elif len(document['workouts_paid']) == (document['num_workouts_requested'] - 1):
            transaction_will_be_over_after_this_payment = True
        request_id = str(document["_id"])


    # Update the request
    result_request = requests.update_one(
        {"_id": ObjectId(request_id)},
        { '$push': { "workouts_paid": workout_id} }
    )
    if transaction_will_be_over_after_this_payment is True:
        result_request = requests.update_one(
            { "_id": ObjectId(request_id) },
            { "$set": {"transaction_over": True} }
        )

    return '', 200


# ----------------------------------------------------------POST REQUESTS-----------------------------------------#
#TODO: do not allow specifying user_id for mentor
@app.route("/api/v1/users/new/", methods=["POST"])
def new_user():
    """Create a new user in the database"""
    db = get_db()
    users = db.users
    data = request.json
    
    # Validate that the data has a 'role' field
    if not "role" in data:
        raise APIException(status_code=400, message='data must have a role field')
    elif not isinstance(data['role'], str):
        raise APIException(status_code=400, message='role must be a string')
            
    if data['role'].lower() == "mentee":
        # Validate that the data has a user_id in it, and that there isn't already a user with the same user_id
        if not "user_id" in data:
            raise APIException(status_code=400, message='data must have a user_id field for a new Mentee')
        cursor = users.find({"user_id": data['user_id']})
        if cursor.count() is 1:
            raise APIException(status_code=403, message='a user with user_id already exists')
        elif cursor.count() > 1:
            raise APIException(status_code=500, message='Error, multiple users with same user_id exist, which is not allowed')
    elif data['role'].lower() == "mentor":
        data['user_id'] = ""
    else:
        raise APIException(status_code=400, message="user has to be either a Mentor or a Mentee")

    # Remove user_id from data so before the validation function, then add it back after
    user_id = data['user_id']
    del data['user_id']
    validate_user_data(data, is_adding_new_user=True)
    data['user_id'] = user_id
    
    # Insert user and return the newly created user_id
    postid = users.insert_one(data)
    return_data = {"user_id": user_id, "mongo_id": str(postid.inserted_id)}
    return flask.jsonify(**return_data), 200


@app.route("/api/v1/mentors/setuserid/", methods=["POST"])
def set_mentor_user_id():
    """set the user_id on a Mentor, which isn't done when a Mentor is created"""
    db = get_db()
    users = db.users
    data = request.json

    expected_fields = ['mongo_id', 'user_id']
    if not set(expected_fields) == set(data):
        raise APIException(status_code=400, message='data does not match the expected fields')

    mongo_id = data['mongo_id']

    # Check if the mongo_id is valid BSON
    if objectid.ObjectId.is_valid(str(mongo_id)) is False:
        raise APIException(status_code=400, message='mongo_id not a valid BSON')

    # Verify that a Mentor with mongo_id exists and that their user_id is empty
    cursor = users.find({"_id": ObjectId(mongo_id) })
    if cursor.count() is 0:
        raise APIException(status_code=404, message='no user found with specified mongo_id')
    for document in cursor:
        if document['role'] != "Mentor":
            raise APIException(status_code=403, message='specified mongo_id represents a Mentee not a Mentor')
        if document['user_id'] != "":
            raise APIException(status_code=403, message='user represented by mongo_id already has a non-empty user_id. It cannot be modified now')

    # Set the user_id
    postid = users.update_one(
        {"_id": ObjectId(mongo_id)},
        {
            "$set": {
                "user_id": data['user_id']
            }
        }
    )
    return_data = {"user_id": data['user_id']}
    return flask.jsonify(**return_data), 200


@app.route("/api/v1/exercises/new/", methods=["POST"])
def new_exercise():
    """Insert a new exercise into the exercises collection"""
    db = get_db()
    users = db.users
    exercises = db.exercises
    data = request.json
    
    expected_fields = ['name', 'pic_urls', 'instructions', 'created_by']
    # If the feilds in data don't match the expected fields
    if not set(expected_fields) == set(data):
        raise APIException(status_code=400, message='data does not match the expected fields')
    if not ( isinstance(data['name'], str) and isinstance(data['instructions'], str)
            and isinstance(data['created_by'], str) and isinstance(data['pic_urls'], list) ):
        raise APIException(status_code=400, message='name, created_by, and instructions must be strings')

    for pic in data['pic_urls']:
        if not isinstance(pic, str):
            raise APIException(status_code=400, message='each pic_url must be a string')

    # Check if created_by is an existing user
    cursor = users.find({"user_id": data['created_by']})
    if cursor.count() is 0:
        raise APIException(status_code=404, message='user_id represented by created_by does not exist')
    elif cursor.count() > 1:
        raise APIException(status_code=500, message='Error, multiple users with same user_id (created_by) exist, which is not allowed')
    
    data['workouts_used_in'] = 0

    # Create n grams for exercise to be used in search
    data['ngrams'] = ' '.join(make_ngrams(str(data['name']).lower()))

    # Insert the new exercise and return its newly created key
    postid = exercises.insert_one(data)

    # Index the exercises in the database to be able to be searched
    exercises.search.create_index(
        [
            ('ngrams', 'text'),
        ],
        name='search_exercises',
        weights={
            'ngrams': 100
        }
    )

    return_data = {"exercise_id": str(postid.inserted_id)}
    return flask.jsonify(**return_data), 200


@app.route("/api/v1/workouts/new/", methods=["POST"])
def new_workout():
    """Insert a new workout into the workouts collection"""
    db = get_db()
    users = db.users
    workouts = db.workouts
    exercises = db.exercises
    requests = db.requests
    data = request.json
    
    # Check if mentor_id and mentee_id are present in data
    if not ("mentor_id" in data and "mentee_id" in data):
        raise APIException(status_code=400, message='data must contain both mentor_id and mentee_id')
    if not ( isinstance(data['mentor_id'], str) and isinstance(data['mentee_id'], str) ):
        raise APIException(status_code=400, message='mentor_id and mentee_id must be strings')

    mentor_id = data['mentor_id']
    mentee_id = data['mentee_id']

    # Check if mentor_id is in the users collection
    cursor_mentor = users.find({"role": "Mentor", "user_id": mentor_id})
    if cursor_mentor.count() is 0:
        raise APIException(status_code=400, message='mentor_id not a Mentor')
    elif cursor_mentor.count() > 1:
        raise APIException(status_code=500, message='Error, multiple Mentors with same user_id (mentor_id) exist, which is not allowed')
    
    # Check if mentee_id is in the users collection
    cursor_mentee = users.find({"role": "Mentee", "user_id": mentee_id})
    if cursor_mentee.count() is 0:
        raise APIException(status_code=400, message='mentee_id not a Mentee')
    elif cursor_mentee.count() > 1:
        raise APIException(status_code=500, message='Error, multiple Mentees with same user_id (mentee_id) exist, which is not allowed')

    # Check if mentor_id has an open request with mentee_id, otherwise a workout cannot be assigned
    cursor_request = requests.find({"mentor_id": mentor_id, "mentee_id": mentee_id, "transaction_over": False})
    if cursor_request.count() is 0:
        raise APIException(status_code=404, message='mentee_is either does not have a request with mentor_id, or the transaction is already over')
    
    request_id = ""
    for document in cursor_request:
        if document['mentor_accepted'] is False:
            raise APIException(status_code=400, message='Mentor is yet to accept workout request')
        if len(document['workouts_created']) >= document['num_workouts_requested']:
            raise APIException(status_code=400, message='the number of workouts that was requested have all been created already')
        request_id = str(document["_id"])

    # Need to delete these 2 fields for the validation function, then bring them back afterwards
    del data['mentor_id']
    del data['mentee_id']
    validate_workout_data(data)
    data['mentor_id'] = mentor_id
    data['mentee_id'] = mentee_id
    
    # Insert the new workout and store its newly created workout_id
    postid = workouts.insert_one(data)
    workout_id = str(postid.inserted_id)

    # For each exercise that was in the workout, update its "workouts_used_in"
    for exercise in data['exercises']:
        result_exercise = exercises.update_one(
            {"_id": ObjectId( exercise["exercise_id"] )},
            {
                "$inc": {
                    "workouts_used_in": 1
                }
            }
        )

    # Update the request object to include the newly created workout
    result_exercise = requests.update_one(
        {"_id": ObjectId( request_id )},
        { '$push': { "workouts_created": workout_id} }
    )

    # return the newly created workout_id
    return_data = {"workout_id": workout_id}
    return flask.jsonify(**return_data), 200

# Done in accept_request already
# @app.route("/api/v1/users/addpartner/", methods=["POST"])
# def add_partner():
#     """Add a mentee to a mentor's partners array and vice versa"""
#     db = get_db()
#     users = db.users
#     data = request.json
    
#     expected_fields = ['mentee_id', 'mentor_id']
#     # If the feilds in data don't match the expected fields
#     if not set(expected_fields) == set(data):
#         raise APIException(status_code=400, message='data does not match the expected fields')
    
#     # Make sure both id's are strings
#     if not ( isinstance(data['mentor_id'], str) and isinstance(data['mentee_id'], str) ):
#         raise APIException(status_code=400, message='mentor_id and mentee_id must be strings')
    
#     mentor_id = data['mentor_id']
#     mentee_id = data['mentee_id']
    
#     # Check if mentee_id is actually a Mentee
#     cursor_mentee = users.find({"role": "Mentee", "user_id": mentee_id})
#     if cursor_mentee.count() is 0:
#         raise APIException(status_code=404, message='mentee_id not a Mentee')
#     elif cursor_mentee.count() > 1:
#         raise APIException(status_code=500, message='Error, multiple Mentees with same user_id (mentee_id) exist, which is not allowed')
#     # Check if mentor_id is actually a Mentor
#     cursor_mentor = users.find({"role": "Mentor", "user_id": mentor_id})
#     if cursor_mentor.count() is 0:
#         raise APIException(status_code=404, message='mentor_id not a Mentor')
#     elif cursor_mentor.count() > 1:
#         raise APIException(status_code=500, message='Error, multiple Mentors with same user_id (mentor_id) exist, which is not allowed')
    
    
#     # Check if they are already partners
#     for document in cursor_mentor:
#         if mentee_id in document['partners']:
#             raise APIException(status_code=403, message='mentee_id is already a partner of mentor_id')
#     for document in cursor_mentee:
#         if mentor_id in document['partners']:
#             raise APIException(status_code=500, message="mentee_id not in mentor's partners array, but mentor_id in mentee_id's partners array")

#     # Add mentee_id to mentor_id's 'partners' field and vice versa
#     postid1 = users.update_one(
#         { "user_id": mentor_id },
#         { '$push': { "partners": mentee_id} }
#     )
#     postid2 = users.update_one(
#         { "user_id": mentee_id },
#         { '$push': { "partners": mentor_id} }
#     )
        
#     # return the id's that were just partnered up
#     return_data = {"mentor_id": mentor_id, "mentee_id": mentee_id}
#     return flask.jsonify(**return_data), 200


@app.route("/api/v1/exercises/search/<keyphrase>/", methods=["GET"])
def get_exercises(keyphrase):
    db = get_db()
    exercises = db['exercises']
    query = ' '.join(make_ngrams(keyphrase.lower()))
    cursor = exercises.find(
        {
            "$text": {
                "$search": query
            }
        },
        {
            "name": True,
            "instructions": True,
            "score": {
                "$meta": "textScore"
            }
        }
    ).sort([("score", {"$meta": "textScore"})])

    context = {'exercises': []}

    for document in cursor:
        temp = document
        temp['exercise_id'] = str(document['_id'])
        del temp['_id']
        context['exercises'].append(temp)

    context['url'] = "/api/v1/exercises/search/" + str(keyphrase)
    print (context)
    return flask.jsonify(**context)


#TODO: check for negative amount of workouts
@app.route("/api/v1/requests/new/", methods=["POST"])
def send_request():
    """This route is called when a Mentee sends a workout request to a Mentor"""
    db = get_db()
    users = db.users
    requests = db.requests
    data = request.json
    
    expected_fields = ['mentee_id', 'mentor_id', 'num_workouts_requested', 'message']
    # If the feilds in data don't match the expected fields
    if not set(expected_fields) == set(data):
        raise APIException(status_code=400, message='data does not match the expected fields')
    
    # Make sure everything matches its datatype
    if not ( isinstance(data['mentor_id'], str) and isinstance(data['mentee_id'], str)
            and isinstance(data['num_workouts_requested'], int) and isinstance(data['message'], str) ):
        raise APIException(status_code=400, message='mentor_id, mentee_id, and message must be strings, num_workouts_requested must be an int')
            
    mentor_id = data['mentor_id']
    mentee_id = data['mentee_id']

    # Check if mentee_id is actually a Mentee
    cursor_mentee = users.find({"role": "Mentee", "user_id": mentee_id})
    if cursor_mentee.count() is 0:
        raise APIException(status_code=404, message='mentee_id not a Mentee')
    elif cursor_mentee.count() > 1:
        raise APIException(status_code=500, message='Error, multiple Mentees with same user_id (mentee_id) exist, which is not allowed')
    # Check if mentor_id is actually a Mentor
    cursor_mentor = users.find({"role": "Mentor", "user_id": mentor_id})
    if cursor_mentor.count() is 0:
        raise APIException(status_code=404, message='mentor_id not a Mentor')
    elif cursor_mentor.count() > 1:
        raise APIException(status_code=500, message='Error, multiple Mentors with same user_id (mentor_id) exist, which is not allowed')

    # Make sure that mentor_id and mentee_id have no other open transaction
    cursor = requests.find({"mentor_id": mentor_id, "mentee_id": mentee_id, "transaction_over": False})
    if cursor.count() > 0:
        raise APIException(status_code=403, message='a Mentee and and Mentor can only have one open transaction at a time')

    context = {}
    context['mentee_id'] = mentee_id
    context['mentor_id'] = mentor_id
    context['message'] = data['message']
    context['mentor_accepted'] = False
    context['num_workouts_requested'] = data['num_workouts_requested']
    context['workouts_created'] = []
    context['workouts_paid'] = []
    context['transaction_over'] = False
    
    postid =  requests.insert_one(context)
    return_data = {"request_id": str(postid.inserted_id)}
    return flask.jsonify(**return_data), 200


# this function creates ngrams in the database for existsing exercises
# used for the conception of ngrams
def make_some_n_grams():
    db = get_db()
    exercises = db.exercises
    documents = exercises.find()
    for d in documents:
        pprint(d)
        result = exercises.update_one(
            {"name": d["name"]},
            {
                "$set": {
                    "ngrams": u' '.join(make_ngrams(str(d["name"]).lower()))
                }
            }
        )
    exercises.create_index(
        [
            ('ngrams', 'text'),
        ],
        name='search_exercises',
        weights={
            'ngrams': 100
        }
    )

def update_id():
    db = get_db()
    users = db.users
    doc = users.find({"_id": ObjectId("5a2850227df0b306d1675e71")})
    doc._id = ObjectId("WWfPWp8oTXRvHFGrHa2AlOpqtpc2")
    users.insert(doc)
    users.remove({"_id": ObjectId("5a2850227df0b306d1675e71")})


if __name__ == "__main__":
    # hey = get_exercises("Bench")
    # print(hey)
    #make_some_n_grams()
    update_id()
    app.run(host='0.0.0.0')
    

