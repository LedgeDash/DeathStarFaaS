import concurrent.futures
import json, os, sys
import uuid
from bson.json_util import dumps
import requests
from function import ds_util

def upload_user_id(req_id, user_id, username):
    '''
    return a JSON dict
    '''
    req = {"req_id":req_id,
           "user_id": user_id,
           "username":username}
    function_url = "http://gateway.openfaas:8080/function/user-service-upload-creator-with-user-id"

    return ds_util.invoke(function_url, req)

def upload_unique_id(req_id, post_type):
    '''
    return a JSON dict
    '''
    req = {"req_id": req_id,
           "post_type": post_type}
    function_url = "http://gateway.openfaas:8080/function/unique-id-service-upload-unique-id"

    return ds_util.invoke(function_url, req)

def upload_media(req_id, media_type, media_id):
    '''
    return a JSON dict
    '''
    req = {"req_id":req_id,
           "media_type": media_type,
           "media_id":media_id}
    function_url = "http://gateway.openfaas:8080/function/media-service-upload-media"

    return ds_util.invoke(function_url, req)

def upload_text(req_id, text):
    '''
    return a JSON dict
    '''
    req = {"req_id":req_id,
           "text":text}
    function_url = "http://gateway.openfaas:8080/function/text-service-upload-text"

    return ds_util.invoke(function_url, req)

def handle(req):
    """handle a request to the function
    Args:
        req (str): a JSON string with the following fields:
            string user_id
            string username
            number post_type
            string text
            string media_id
            string media_type
    Return:
        on success, return {"status": "success", ...TBD}
        on error, return {"status": "ComposePostError", "errors": [errors from
        each function call]}
    """
    payload = json.loads(req)

    if ('username' not in payload or
       'user_id' not in payload or
       'post_type' not in payload or
       'text' not in payload or
       'media_id' not in payload or
       'media_type' not in payload):
        msg = '''Make sure the input has `username`, `user_id`, `post_type`, 
        `text`, `media_id` and `media_type` fields'''
        ret = json.dumps({"status":"MissingFieldError", "errors":[msg]})
        sys.exit(ret)

    req_id= uuid.uuid4().int

    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures.append(executor.submit(upload_user_id, req_id,
            payload['user_id'], payload['username']))
        futures.append(executor.submit(upload_unique_id, req_id,
            payload['post_type']))
        futures.append(executor.submit(upload_media, req_id,
            payload['media_type'], payload['media_id']))
        futures.append(executor.submit(upload_text, req_id,
            payload['text']))

        results = [f.result() for f in concurrent.futures.as_completed(futures)]

        ret = {"status": "ComposePostError", "errors":[]}

        for r in results:
            if r["http_status_code"] != 200:
                ret["errors"].append(r)

        if len(ret["errors"]) == 0:
            ret={"status":"success"}

        return dumps(ret)
