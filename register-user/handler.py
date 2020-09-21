import json
import uuid
import pymongo
import hashlib
import secrets
import string
import requests
import sys
from bson.json_util import dumps

def handle(req):
    """create a new user account document in the DB if the username doesn't
    already exists 
    Args:
        req (str): A JSON string with 'username', 'first_name', 'last_name'
        and 'password' as fields

    Code adapted from:
    DeathStarBench/socialNetwork/src/UserService/UserHandler.h
    """
    payload = json.loads(req)

    if ('username' not in payload or
       'first_name' not in payload or
       'last_name' not in payload or
       'password' not in payload):
        msg = 'Make sure the input has `username`, `first_name`, `last_name` and `password` fields'
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)

    # Connect to MongoDB deployment on the same K8S cluster.
    # We will be using the `users` db and the `users` collection.
    client = pymongo.mongo_client.MongoClient('mongodb://mongo-0.mongo.default')
    # TODO: Error handling along the way
    db = client.users
    users = db.users

    found = users.find_one({"username": payload['username']})

    if found:
        sys.exit(json.dumps({"status":"UsernameAlreadyExistError", "message": 'username ' +
            payload['username']+' already exist'}))

    new_user_doc = payload

    user_id = uuid.uuid4()
    new_user_doc['user_id'] = user_id.hex

    pwd = new_user_doc['password']
    salt = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for i
            in range(32)) 
    h = hashlib.sha256()
    h.update(pwd.encode('utf-8'))
    h.update(salt.encode('utf-8'))

    new_user_doc['salt'] = salt
    new_user_doc['password'] = h.hexdigest()

    res = users.insert_one(new_user_doc)

    # call insertUser function in the social graph service
    req_str = json.dumps({'user_id':new_user_doc['user_id']})

    r = requests.get("http://gateway.openfaas:8080/function/social-graph-insert-user",
            data=req_str)

    if r.status_code != 200:
        sys.exit(json.dumps({"status":"SocialGraphInsertUserError",
                             "message": "Received: %d".format(r.status_code)}))

    # need to use bson.json_util.dumps because `insert_one(new_user_doc)`
    # returns the new BSON document inserted into MongoDB which adds a field
    # '_id' of type ObjectId. Default JSON decoder cannot process ObjectId type.
    return dumps({"status":"success", "user": new_user_doc})
