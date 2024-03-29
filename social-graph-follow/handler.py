import json
import sys
import pymongo
from pymongo import ReturnDocument
from datetime import datetime
from bson.json_util import dumps

def handle(req):
    """Add followee_id into the followee list of user_id and add user_id into
    the follower list of the followee_id in the social_graph database
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
    # check if followee_id is already in the followees list of user_id
    query = {"user_id": payload['user_id'], "followees": {"$not":{"$elemMatch": {"user_id": payload['followee_id']}}}}
    update = {"$push":{"followees":{"user_id":payload['followee_id'],"timestamp":timestamp}}}
    user_ret = collection.find_one_and_update(query, update,
            return_document=ReturnDocument.AFTER)

    if user_ret == None:
        sys.exit(json.dumps({"status": "FollowError", "message": "Either user_id "+
            "or followee_id do not exist or user_id already follows followee_id"}))

    # Update the follower list of followee_id
    # check if user_id is already in the followers list of followee_id
    query = {"user_id": payload['followee_id'], "followers": {"$not":{"$elemMatch": {"user_id": payload['user_id']}}}}
    update = {"$push":{"followers":{"user_id":payload['user_id'],"timestamp":timestamp}}}
    followee_ret = collection.find_one_and_update(query, update,
            return_document=ReturnDocument.AFTER)

    return dumps({"status": "success", "user": user_ret, "followee":followee_ret})
