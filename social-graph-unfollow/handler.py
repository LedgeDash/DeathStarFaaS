import json
import sys
import pymongo
from pymongo import ReturnDocument
from datetime import datetime
from bson.json_util import dumps

def handle(req):
    """Remove followee_id from the followee list of user_id and remove user_id
    from the follower list of the followee_id in the social_graph database
    Args:
        req (str): request body
        
        user_id
        followee_id
    """
    payload = json.loads(req)
    if ('user_id' not in payload or
       'followee_id' not in payload):
        msg = json.dumps({"status":"MissingFieldError",
                          "message":'Make sure the input has `user_id` and'+
                          '`followee_id` field'})
        sys.exit(msg)

    # current date and time
    now = datetime.now()

    timestamp = datetime.timestamp(now)

    client = pymongo.mongo_client.MongoClient('mongodb://mongo-0.mongo.default')
    db = client.social_graph
    collection = db.social_graph
    
    db = client.social_graph
    collection = db.social_graph

    # Update the followee list of user_id
    # check if `user_id` exists. If yes, remove `followee_id` from user_id's
    # followees list.
    query = {"user_id": payload['user_id']}
    update = {"$pull":{"followees":{"user_id":payload['followee_id']}}}
    user_ret = collection.find_one_and_update(query, update,
            return_document=ReturnDocument.AFTER)

    if user_ret == None:
        sys.exit(json.dumps({"status": "UnfollowError", "message": "user_id "+
            "does not exist"}))

    # Update the follower list of followee_id
    # check if user_id is already in the followers list of followee_id
    query = {"user_id": payload['followee_id']}
    update = {"$pull":{"followers":{"user_id":payload['user_id']}}}
    followee_ret = collection.find_one_and_update(query, update,
            return_document=ReturnDocument.AFTER)

    if user_ret == None:
        sys.exit(json.dumps({"status": "UnfollowError", "message": "followee_id "+
            "does not exist"}))

    return dumps({"status": "success", "user": user_ret, "followee":followee_ret})
