import json
import sys
import requests
from bson.json_util import dumps, loads

def clean_error_msg(s):
    '''clean OpenFaaS functions' error message for JSON encoder
    When an OpenFaaS function exit on error (i.e., via `sys.exit(..)`), the
    returned message looks like this:
    s = 'exit status 1\n{"status": "UsernameAlreadyExistError", "message":
    "username troubledEagle2 already exist"}\n'
    The beginning `exit status 1\n` and the last \n throws off the json encoder.
    '''
    return s.split("\n")[1]

def handle(req):
    """given usename and followee_name, look up user_id and followee_id, remove
    followee_id from user_id's followees list and user_id from followee_id's
    followers list
    Args:
        req (str): request body
        username
        followee_name
    """
    payload = json.loads(req)
    if ('username' not in payload or
       'followee_name' not in payload):
        msg = json.dumps({"status":"MissingFieldError",
                          "message":'Make sure the input has `username` and'+
                          '`followee_name` field'})
        sys.exit(msg)

    # get username's user_id
    req_str = json.dumps({'username':payload['username']})

    r = requests.get("http://gateway.openfaas:8080/function/get-user-id",
            data=req_str)

    if r.status_code != 200:
        message = clean_error_msg(r.text)
        sys.exit(json.dumps({"status":"FollowError",
                             "message": "Failed to get username's user_id. {}".format(message)}))
    user_id = loads(r.text)['user_id']

    # get followee_name's user_id
    req_str = json.dumps({'username':payload['followee_name']})

    r = requests.get("http://gateway.openfaas:8080/function/get-user-id",
            data=req_str)

    if r.status_code != 200:
        message = clean_error_msg(r.text)
        sys.exit(json.dumps({"status":"FollowError",
                             "message": "Failed to get followee_name's user_id. {}".format(message)}))
    followee_id = loads(r.text)['user_id']

    # call follow function in the social graph service
    req_str = json.dumps({'user_id':user_id, 'followee_id': followee_id})

    r = requests.get("http://gateway.openfaas:8080/function/social-graph-unfollow",
            data=req_str)

    if r.status_code != 200:
        message = clean_error_msg(r.text)
        sys.exit(json.dumps({"status":"FollowError",
                             "message": "social-graph-unfollow failed. {}".format(message)}))

    return r.text
