import json, os, sys, traceback
from bson.json_util import dumps
import pymongo

def handle(req):
    """Given a list of post_ids return a list of post documents from MongoDB

    Args:
        req (str): request body
            list(str): post_ids
    """
    payload = json.loads(req)

    if ('post_ids' not in payload):
        msg = '''Make sure the input has `post_ids`'''
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)

    try:
        connect_str = str(os.getenv('MONGO_URI'))
        client = pymongo.mongo_client.MongoClient(connect_str)
        db = client.post
        collection = db.post
    except:
        ret = {"status":"PostStorageServiceReadPostsError",
               "errors":[{"message": "MongoDB failed to connect",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                          ]}

        sys.exit(dumps(ret))

    # suppress the _id field added by MongoDB
    post_ids = payload['post_ids']
    query = {"post_id": {"$in": post_ids}}

    try:
        ret = collection.find(query, {"_id":False})
    except:
        ret = {"status":"PostStorageServiceReadPostsError",
               "errors":[{"message": "Failed to get posts from Mongo",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                          ]}

        sys.exit(dumps(ret))

    return dumps({"status": "success", "posts": ret})
