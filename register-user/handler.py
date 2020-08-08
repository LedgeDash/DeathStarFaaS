import json
import uuid
import pymongo
import hashlib
import secrets
import string

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    payload = json.loads(req)

    if ('username' not in payload or
       'first_name' not in payload or
       'last_name' not in payload or
       'password' not in payload):
        return ('Error: Missing input. Make sure the input has `username`, '+
                '`first_name`, `last_name` and `password` fields')

    # TODO: Error handling along the way
    # Connect to MongoDB deployment on the same K8S cluster.
    # We will be using the `users` db and the `users` collection.
    client = pymongo.mongo_client.MongoClient('mongodb://mongo-0.mongo.default')
    db = client.users
    users = db.users

    found = users.find_one({"username": payload['username']})

    if found:
        return('username ' + payload['username']+' already exist')

    new_user_doc = payload

    user_id = uuid.uuid4()
    # we use uuid as the _id field in MongoDB. The original DeathStar uses
    # a 'user_id' field.
    new_user_doc['_id'] = user_id

    pwd = new_user_doc['password']
    salt = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for i
            in range(32)) 
    h = hashlib.sha256()
    h.update(pwd.encode('utf-8'))
    h.update(salt.encode('utf-8'))

    new_user_doc['salt'] = salt
    new_user_doc['password'] = h.hexdigest()

    print('creating new user account: {}'.format(new_user_doc))
    res = users.insert_one(new_user_doc)

