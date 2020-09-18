import json, os, sys
from bson.json_util import dumps
import redis
from function import ds_util

def compose_and_upload(req_id):
    req = {"req_id": req_id}
    function_url = "http://gateway.openfaas:8080/function/compose-post-service-compose-and-upload"

    return ds_util.invoke(function_url, req)

def handle(req):
    """Upload user_id and username of the the post creator to Redis and
    optionally invoke compose-post-service-compose-and-upload if all 6 compose
    post functions already completed.
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

    req_id = payload['req_id']
    creator_str = json.dumps({"user_id":payload['user_id'],
    "username":payload['username']})
    req_id_str = str(payload['req_id'])

    redis_server= os.getenv('REDIS_SERVER')
    redis_port = os.getenv('REDIS_PORT')
    try:
        r = redis.Redis(host = redis_server, port = redis_port)

        hset_reply = r.hset(req_id_str, "creator", creator_str)
        hlen_reply = r.hincrby(req_id_str, "num_components", 1)
        r.expire(req_id_str, os.getenv('REDIS_EXPIRE_TIMEOUT'))
    except:
        ret = {"status":"ComposePostServiceUploadCreatorError",
               "errors":[{"message": "Redis failure",
                          "exception": sys.exc_info()[1],
                          "traceback": sys.exc_info()[2]}
                        ]}
        sys.exit(dumps(ret))

    if hlen_reply == os.getenv('NUM_COMPONENTS'):
        ret = compose_and_upload(req_id)
        if ret['http_status_code']!= 200:
            sys.exit(dumps({"status":"ComposePostServiceUploadCreatorError", "req_id": req_id_str,
                              "errors": [ret]}))
        else:
            return dumps({"status":"success", "req_id": req_id_str,
                          "compose_and_upload": ret})

    return dumps({"status":"success", "req_id": req_id_str})
