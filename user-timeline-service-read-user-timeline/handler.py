import json, os, sys, traceback
from bson.json_util import dumps
from function import ds_util
import pymongo
import redis

def handle(req):
    """Given a user_id and a range, return all posts of that use within that
    range.

    Acquire the post_ids from Redis and call post-storage-service-read-posts to
    obtain posts based on the list of post_ids. A range is represented by the
    `start` and `stop` input parameters. They are the starting the ending
    indexes of post_ids in the sorted set in Redis.

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

    start = int(payload['start'])
    stop = int(payload['stop'])
    user_id = str(payload['user_id'])

    # Read user_id's post_ids from Redis
    redis_server= os.getenv('REDIS_SERVER')
    redis_port = os.getenv('REDIS_PORT')
    try:
        r = redis.Redis(host = redis_server, port = redis_port)
    except:
        ret = {"status":"UserTimelineServiceReadUserTimelineError",
               "errors":[{"message": "Failed to connect to Redis",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                        ]}
        sys.exit(dumps(ret))

    try:
        ret = r.zrevrange(user_id, start, stop - 1)
    except:
        ret = {"status":"UserTimelineServiceReadUserTimelineError",
               "errors":[{"message": "Failed to read post_ids from Redis",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                        ]}
        sys.exit(dumps(ret))

    post_ids = [u.decode("utf-8") for u in ret]

    # call post-storage-service-read-posts to get post documents
    function_url = "http://gateway.openfaas:8080/function/post-storage-service-read-posts"
    ret = ds_util.invoke(function_url, {"post_ids": post_ids})

    if ret["http_status_code"] != 200:
        sys.exit(dumps({"status": "UserTimelineServiceReadUserTimelineError",
            "errors":[ret]
            }))

    return dumps({"status": "success", "post_ids": post_ids, "posts": ret["posts"]})
