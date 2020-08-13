import json
import pymongo
import sys
from bson.json_util import dumps

def handle(req):
    """Given a user_id, return its followee list if the user exists
    Args:
        req (str): request body

        user_id
    """
    payload = json.loads(req)

    if ('user_id' not in payload):
        msg = 'Make sure the input has `user_id`'
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)

    client = pymongo.mongo_client.MongoClient('mongodb://mongo-0.mongo.default')
    # TODO: Error handling along the way
    db = client.social_graph
    collection = db.social_graph

    found = collection.find_one({"user_id": payload['user_id']})

    if found == None:
        sys.exit(json.dumps({"status":"UserIDNotExistError", "message": 'user_id' +
            payload['user_id']+' does not exist in social graph'}))

    return dumps({"status": "success", "followees": found['followees']})
