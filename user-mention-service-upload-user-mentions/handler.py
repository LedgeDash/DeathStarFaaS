import json, sys
from bson.json_util import dumps
from function import ds_util

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    payload = json.loads(req)

    if ('usernames' not in payload or
       'req_id' not in payload):
        msg = '''Make sure the input has `usernames` and `req_id`'''
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)


    return dumps({"status":"success"})
