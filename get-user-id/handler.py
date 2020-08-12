import sys
import json
import pymongo
from bson.json_util import dumps

def handle(req):
    """Given a username, look up its user_id
    Args:
        req (str): request body
        
    DeathStarBench/socialNetwork/src/UserService/UserHandler.h:GetUserId()
    First try to look up the user_id in memcached. If not found, try to look up
    the user_id in mongodb and then cache the result in memcached
    """
    payload = json.loads(req)

    if ('username' not in payload):
        msg = json.dumps({"status":"MissingFieldError",
                          "message":'Make sure the input has `user_id` field'})
        sys.exit(msg)

    # Connect to MongoDB deployment on the same K8S cluster.
    # We will be using the `users` db and the `users` collection.
    client = pymongo.mongo_client.MongoClient('mongodb://mongo-0.mongo.default')
    # TODO: Error handling along the way
    db = client.users
    users = db.users

    found = users.find_one({"username": payload['username']})

    if found==None:
        msg = json.dumps({"status":"UsernameNotFoundError",
                          "message":'username ' + payload['username']+' not found'})
        sys.exit(msg)

    return json.dumps({"status": "success", "user_id": found['user_id']})
