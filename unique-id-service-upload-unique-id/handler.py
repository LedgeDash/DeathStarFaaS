import json, sys
from bson.json_util import dumps
from function import ds_util
import uuid

def handle(req):
    """handle a request to the function
    Args:
        req (str): a JSON string with the following fields:
            int req_id (128-bit uuid4 integer)
            int post_type
    Return:
        on success, return {"status": "success", ...TBD}
        on error, return {"status": "UploadUniqueIdError", "errors": [errors from
        each function call]}
    """
    payload = json.loads(req)

    if ('req_id' not in payload or
       'post_type' not in payload):
        msg = '''Make sure the input has `req_id` and `post_type` fields'''
        ret = json.dumps({"status":"MissingFieldError", "errors":[msg]})
        sys.exit(ret)

    post_id= uuid.uuid4().int

    function_url = "http://gateway.openfaas:8080/function/compose-post-service-upload-unique-id"
    ret = ds_util.invoke(function_url, payload)

    if ret['http_status_code'] != 200:
        sys.exit(json.dumps({"status":"UniqueIdServiceUploadUniqueIdError",
                             "errors": [ret]}))

    return dumps({"status":"success", "post_id": post_id})


