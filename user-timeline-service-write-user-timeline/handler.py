import os, sys, json, traceback
import pymongo
from pymongo import ReturnDocument
from bson.json_util import dumps
import redis

def handle(req):
    """Update the creator's user timeline after it creates a new post
    Args:
        req (str): request body
            req_id
            str post_id
            str creator_id
            datetime timestamp
    """
    payload = json.loads(req)

    if ('req_id' not in payload or
        'post_id' not in payload or
        'creator_id' not in payload or
        'timestamp' not in payload):
        msg = '''Make sure the input has `req_id`, `creator_id`, `timestamp` and
        `post_id` fields'''
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)

    # Write post_id and timestamp to MongoDB
    try:
        connect_str = str(os.getenv('MONGO_URI'))
        client = pymongo.mongo_client.MongoClient(connect_str)
        db = client.user_timeline
        collection = db.user_timeline
    except:
        ret = {"status":"UserTimelineServiceWriteUserTimelineError",
               "errors":[{"message": "MongoDB failed to connect",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                          ]}

        sys.exit(dumps(ret))

    user_id = payload['creator_id']
    post_id = payload['post_id']
    timestamp = payload['timestamp']
    query = {"user_id":user_id}
    update = {
                "$push": {
                    "posts": {
                        "$each":[{"post_id": post_id, "timestamp": timestamp}],
                        "$position": 0
                    }
                }
             }
    try:
        ret = collection.find_one_and_update(query, update,
                return_document=ReturnDocument.AFTER, upsert=True)
    except:
        ret = {"status":"UserTimelineServiceWriteUserTimelineError",
               "errors":[{"message": "MongoDB find_one_and_update() failed",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                        ]}
        sys.exit(dumps(ret))

    # Write post_id and timestamp to Redis sorted set
    redis_server= os.getenv('REDIS_SERVER')
    redis_port = os.getenv('REDIS_PORT')
    try:
        r = redis.Redis(host = redis_server, port = redis_port)
    except:
        ret = {"status":"UserTimelineServiceWriteUserTimelineError",
               "errors":[{"message": "Failed to connect to Redis",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                        ]}
        sys.exit(dumps(ret))

    try:
        ret = r.zadd(str(user_id), {str(post_id): timestamp}, nx=True)
    except:
        ret = {"status":"UserTimelineServiceWriteUserTimelineError",
               "errors":[{"message": "Failed to update Redis",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                        ]}
        sys.exit(dumps(ret))

    return dumps({"status": "success", "req_id": payload['req_id'], "user_id":
        user_id, "post_id": post_id})
