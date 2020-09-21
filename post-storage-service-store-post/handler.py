import os, sys, json, traceback
import pymongo
from bson.json_util import dumps

def handle(req):
    """Store a post in MongoDB
    Args:
        req (str): a JSON string with the following fields:
            int req_id (128-bit uuid4 integer)
            obj post
    """
    payload = json.loads(req)

    if ('req_id' not in payload or
        'post' not in payload):
        msg = 'Make sure the input has `req_id` and `post` fields'
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)

    post = payload['post']

    try:
        connect_str = str(os.getenv('MONGO_URI'))
        client = pymongo.mongo_client.MongoClient(connect_str)
        db = client.post
        collection = db.post
    except:
        ret = {"status":"PostStorageServiceStorePostError",
               "errors":[{"message": "MongoDB failed to connect",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                          ]}

        sys.exit(dumps(ret))

    try:
        ret = collection.insert_one(post)
    except:
        ret = {"status":"PostStorageServiceStorePostError",
               "errors":[{"message": "MongoDB insert_one() failed",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                        ]}
        sys.exit(dumps(ret))

    return dumps({"status": "success", "req_id": post['req_id']})
