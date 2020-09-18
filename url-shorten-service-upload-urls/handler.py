import concurrent.futures
from function import ds_util
import os, sys, json
import pymongo
from bson.json_util import dumps
import random
import string

HOSTNAME="http://short-u.rl/"

def get_random_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

def store_urls_mongo(url_docs):
    '''store url documents in mongodb.
    On error, this function mimicks the behavior of the invoke function where it
    returns a dict with a key "http_status_code" equal to 500.
    '''
    connect_str = os.getenv('MONGO_URI')
    try:
        client = pymongo.mongo_client.MongoClient(connect_str)
    except:
        return {"http_status_code": 500, "error": "MongoDB failed to connect to " + connect_str}

    db = client.url_shorten
    collection = db.url_shorten

    requests = [pymongo.InsertOne(doc) for doc in url_docs]

    ret = collection.bulk_write(requests)

    if ret.inserted_count != len(url_docs):
        return {"http_status_code": 500, "error": "Some inserts failed: "
                +str(len(url_docs)) + " attempts, "
                +str(ret.inserted_count) + " successes"}

    return {"http_status_code":200, "status":"success"}


def compose_post_service_upload_urls(req_id, url_docs):
    '''
    return a JSON dict
    '''
    req = {"req_id": req_id,
           "url_docs": url_docs}
    function_url = "http://gateway.openfaas:8080/function/compose-post-service-upload-urls"

    return ds_util.invoke(function_url, req)

def handle(req):
    """Given a list of urls, shorten them, store shortened url in DB and call
    compose-post-service-upload-urls.

    Always call compose-post-service-upload-urls even if the text contains no
    urls (i.e., the "urls" field in the input JSON string is []).
    Args:
        int req_id (128-bit uuid4 integer)
        urls (list of str): a list of urls to shorten
    Return:
        On success, return {"status":"success", "urls": [url_docs]
        On error, whether it's write to MongoDB or
        compose-post-service-upload-urls, return {"status": 
        "UrlShortenServiceUploadUrlsError", "errors": [], "urls": [url_docs]}
    """

    payload = json.loads(req)

    if ('req_id' not in payload or
       'urls' not in payload):
        msg = '''Make sure the input has `req_id` and `urls` fields'''
        ret = json.dumps({"status":"MissingFieldError", "errors":[msg]})
        sys.exit(ret)

    req_id = payload['req_id']
    urls = payload['urls']
    new_url_docs = []
    
    for u in urls:
        new_url_docs.append({"expanded_url": u,
                             "shortened_url": HOSTNAME+get_random_string(10)})

    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures.append(executor.submit(compose_post_service_upload_urls, req_id,
            new_url_docs))
        
        if len(urls) > 0:
            futures.append(executor.submit(store_urls_mongo, new_url_docs))

        results = [f.result() for f in concurrent.futures.as_completed(futures)]

        ret = {"status": "UrlShortenServiceUploadUrlsError", "errors":[]}

        for r in results:
            if r["http_status_code"] != 200:
                ret["errors"].append(r)

        if len(ret["errors"]) == 0:
            ret={"status":"success"}
            ret["urls"] = new_url_docs
            return dumps(ret)
        else:
            ret["urls"] = new_url_docs
            sys.exit(dumps(ret))

