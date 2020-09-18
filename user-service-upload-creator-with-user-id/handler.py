import json, os, sys
import requests
from bson.json_util import dumps
from function import ds_util

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

    if ('username' not in payload or
       'user_id' not in payload or
       'req_id' not in payload):
        msg = '''Make sure the input has `username`, `user_id`, `req_id`'''
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)

    function_url = "http://gateway.openfaas:8080/function/compose-post-service-upload-creator"
    ret = ds_util.invoke(function_url, payload)

    if ret['http_status_code'] != 200:
        sys.exit(dumps({"status":"UploadCreatorError",
                             "errors": [ret]}))

    return dumps({"status":"success",
                  "creator": {"username":payload['username'], "user_id": payload['user_id']}
                 })

