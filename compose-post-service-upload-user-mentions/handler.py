import json, os, sys
from bson.json_util import dumps

def handle(req):
    """handle a request to the function
     Args:
        req (str): a JSON string with the following fields:
        int req_id (128-bit uuid4 integer)
        list(dict) user_mentions each user_mention is a dict of the form
        {"username": username, "user_id": user_id}
    Return:

    """
    payload = json.loads(req)

    if ('user_mentions' not in payload or
       'req_id' not in payload):
        msg = '''Make sure the input has `user_mentions` and `req_id`'''
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)


    return dumps({"status":"success"})
