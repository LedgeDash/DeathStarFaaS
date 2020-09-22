import json, os, sys
from bson.json_util import dumps
from function import ds_util

def format_posts(data):
    posts = data["posts"]
    posts.sort(key = lambda i: i['timestamp'], reverse=True)
    return posts

def handle(req):
    """Client API to read the timeline of a user

    Calls user-timeline-service-read-user-timeline to acquire a user's timeline,
    formats the data in the right fashion and return it back to the client
    (e.g., a browser).

    Args:
        req (str): request body
    """
    payload = json.loads(req)

    if ('user_id' not in payload or
       'start' not in payload or
       'stop' not in payload):
        msg = '''Make sure the input has `user_id`, `start`, `stop`'''
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)

    function_url = "http://gateway.openfaas:8080/function/user-timeline-service-read-user-timeline"

    ret = ds_util.invoke(function_url, payload)

    if ret["http_status_code"] != 200:
        return dumps({"status": "UserTimelineReadFrontendError",
            "errors":[ret]
            })

    return dumps({"status": "success", "posts":format_posts(ret)})
