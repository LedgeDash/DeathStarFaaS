import json, os, sys
from bson.json_util import dumps

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    payload = json.loads(req)

    if ('url_docs' not in payload or
       'req_id' not in payload):
        msg = '''Make sure the input has `url_docs`, `req_id`'''
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)


    return dumps({"status":"success"})
