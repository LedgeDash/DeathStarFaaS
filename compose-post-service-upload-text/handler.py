import json, os, sys
from bson.json_util import dumps

def handle(req):
    """handle a request to the function
     Args:
        req (str): a JSON string with the following fields:
        int req_id (128-bit uuid4 integer)
        string user_id
        string username
    Return:

    """
    payload = json.loads(req)

    if ('text' not in payload or
       'req_id' not in payload):
        msg = '''Make sure the input has `text` and `req_id`'''
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)


    return dumps({"status":"success"})
