import concurrent.futures
import sys, os, json
from bson.json_util import dumps
import pymongo
import traceback
import redis
import time
from function import ds_util

def upload_post_helper(req_id, post):
    '''Call post-storage-service-store-post to write the post into DB
    '''
    req = {"req_id":req_id,
           "post":post}
    function_url = "http://gateway.openfaas:8080/function/post-storage-service-store-post"

    return ds_util.invoke(function_url, req)

def upload_user_timeline_helper(req_id, post_id, creator_id, post_tsp):
    '''Call user-timeline-service-write-user-timeline to ...
    '''
    req = {"req_id":req_id,
           "post_id":post_id,
           "creator_id": creator_id,
           "timestamp": post_tsp}
    function_url = "http://gateway.openfaas:8080/function/user-timeline-service-write-user-timeline"

    return ds_util.invoke(function_url, req)

def upload_home_timeline_helper(req_id, post_id, creator_id, post_tsp,
        user_mentions_ids):
    '''Send basic message through RabbitMQ
    '''
    return {"http_status_code": 200}

def handle(req):
    """Create a post based on the hash stored at req_id in Redis

    Args:
        req (str): a JSON string with the following fields:
            int req_id (128-bit uuid4 integer)
    """
    payload = json.loads(req)

    if ('req_id' not in payload):
        msg = '''Make sure the input has `req_id`'''
        ret = json.dumps({"status":"MissingFieldError", "message":msg})
        sys.exit(ret)

    req_id = payload['req_id']
    req_id_str = str(req_id)

    # Connect to Redis
    redis_server= os.getenv('REDIS_SERVER')
    redis_port = os.getenv('REDIS_PORT')
    try:
        r = redis.Redis(host = redis_server, port = redis_port)
    except:
        ret = {"status":"ComposePostServiceComposeAndUploadError",
               "errors":[{"message": "Failed to connect to Redis",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                        ]}
        sys.exit(dumps(ret))

    # Read all fields of a post from Redis
    try:
        text = r.hget(req_id_str, "text").decode("utf-8")
        creator = r.hget(req_id_str, "creator").decode("utf-8")
        media = r.hget(req_id_str, "media").decode("utf-8")
        post_id = r.hget(req_id_str, "post_id").decode("utf-8")
        urls = r.hget(req_id_str, "urls").decode("utf-8")
        user_mentions = r.hget(req_id_str, "user_mentions").decode("utf-8")
        post_type = r.hget(req_id_str, "post_type").decode("utf-8")
    except:
        ret = {"status":"ComposePostServiceComposeAndUploadError",
               "errors":[{"message": "Failed to read hash from Redis",
                          "exception": str(sys.exc_info()[1]),
                          "traceback": traceback.format_exc()}
                        ]}
        sys.exit(dumps(ret))

    # Create a BSON document for the post and store it in MongoDB
    post = {}
    post["req_id"] = req_id_str
    post["post_id"] = str(post_id)
    post["creator"] = json.loads(creator)
    post["text"] = text
    post["timestamp"] = int(time.time())
    post["media"] = json.loads(media)
    post["urls"] = json.loads(urls)
    post["user_mentions"] = json.loads(user_mentions)
    user_mentions_ids = [u["user_id"] for u in post["user_mentions"]]

    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures.append(executor.submit(upload_post_helper, req_id, post))
        futures.append(executor.submit(upload_user_timeline_helper, req_id,
            post['post_id'], post['creator']['user_id'], post['timestamp']))
        futures.append(executor.submit(upload_home_timeline_helper, req_id,
            post['post_id'], post['creator']['user_id'], post['timestamp'],
            user_mentions_ids))

        results = [f.result() for f in concurrent.futures.as_completed(futures)]

        ret = {"status": "ComposePostServiceComposeAndUploadError",
               "req_id": req_id, "errors":[]}

        for r in results:
            if r["http_status_code"] != 200:
                ret["errors"].append(r)

        if len(ret["errors"]) == 0:
            ret={"status":"success", "req_id": req_id, "post": post}
            return dumps(ret)
        else:
            sys.exit(dumps(ret))

