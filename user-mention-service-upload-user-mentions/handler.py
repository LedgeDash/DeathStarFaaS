import json, sys, os
from bson.json_util import dumps
from function import ds_util
import pymongo

def compose_post_service_upload_user_mentions(req_id, user_mentions):
    req = {"req_id": req_id,
           "user_mentions": user_mentions}
    function_url = "http://gateway.openfaas:8080/function/compose-post-service-upload-user-mentions"

    return ds_util.invoke(function_url, req)

def handle(req):
    """Look up the user_ids of all usernames in the user mentions and upload
    them to compose-post-service-upload-user-mentions.

    If some of the user mentions (words that start with @) do not exist in the
    user database, ignore them and just treat them as regular strings.

    Args:
        req (str): a JSON string with the following fields:
            int req_id
            [str] usernames
    """
    payload = json.loads(req)

    if ('usernames' not in payload or
       'req_id' not in payload):
        msg = '''Make sure the input has `usernames` and `req_id`'''
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)

    usernames = payload['usernames']
    req_id = payload['req_id']
    connect_str = os.getenv('MONGO_URI')
    try:
        client = pymongo.mongo_client.MongoClient(connect_str)
    except:
        error = {"status": "UserMentionServiceUploadUserMentionsError",
                "errors": ["MongoDB failed to connect"]}
        sys.exit(dumps(error))

    db = client.users
    query = {"username": {"$in": usernames}}
    cursor = db.users.find(query)

    user_mentions = [{"username": d['username'], "user_id":d['user_id']} for d
            in cursor]

    # call compose-post-service-upload-user-mentions
    ret = compose_post_service_upload_user_mentions(req_id, user_mentions)

    if ret['http_status_code'] != 200:
        error = {"status": "UserMentionServiceUploadUserMentionsError",
                "errors": [ret],
                "user_mentions": user_mentions}
        sys.exit(dumps(error))

    return dumps({"status":"success", "user_mentions": user_mentions})
