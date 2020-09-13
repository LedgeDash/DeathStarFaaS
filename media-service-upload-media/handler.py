import json, sys
from bson.json_util import dumps
from function import ds_util

def handle(req):
    """handle a request to the function
    Args:
        req (str): a JSON string with the following fields:
            int req_id (128-bit uuid4 integer)
            str media_type
            str media_id
    Return:
        on success, return {"status": "success", ...TBD}
        on error, return {"status": "MediaServiceUploadMediaError", "errors": [errors from
        each function call]}
    """
    payload = json.loads(req)

    if ('req_id' not in payload or
        'media_id' not in payload or
       'media_type' not in payload):
        msg = '''Make sure the input has `req_id`, `media_id` and `media_type` fields'''
        ret = json.dumps({"status":"MissingFieldError", "errors":[msg]})
        sys.exit(ret)

    function_url = "http://gateway.openfaas:8080/function/compose-post-service-upload-media"
    ret = ds_util.invoke(function_url, payload)

    if ret['http_status_code'] != 200:
        sys.exit(json.dumps({"status":"MediaServiceUploadMediaError",
                             "errors": [ret]}))

    return dumps({"status":"success", "media_id": payload['media_id']})


