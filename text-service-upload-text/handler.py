import concurrent.futures
import json, sys
from bson.json_util import dumps
from function import ds_util
import re

user_mention_pattern = re.compile(r"@[a-zA-Z0-9]+")
url_pattern=re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")

def shorten_and_upload_urls(req_id, urls):
    '''
    Args:
        urls: a list of str of urls. urls can be the empty list

    return a JSON dict
    '''
    req = {"req_id": req_id,
           "urls": urls}
    function_url = "http://gateway.openfaas:8080/function/url-shorten-service-upload-urls"

    return ds_util.invoke(function_url, req)

def upload_user_mentions(req_id, usernames):
    '''
    user_mentions: a list of usernames ste each with an @ sign prefix
    '''
    req = {"req_id": req_id,
           "usernames": usernames}
    function_url = "http://gateway.openfaas:8080/function/user-mention-service-upload-user-mentions"

    return ds_util.invoke(function_url, req)

def upload_text(req_id, text):
    req = {"req_id": req_id,
           "text": text}
    function_url ="http://gateway.openfaas:8080/function/compose-post-service-upload-text"

    return ds_util.invoke(function_url, req)

def handle(req):
    """Process the text in a post
    Extract the user mentions and urls that might appear in the text of a post.
    Forwards user mentions (a list of username strings) to
    user-mention-service-upload-user-mentions and the urls (a list of url
    strings) to url-shorten-service-upload-urls. After
    url-shorten-service-upload-urls returns shortened urls, replace full urls in
    the original text with shortened urls and send the new text to
    compose-post-service-upload-text for uploading.
    Args:
        req (str): a JSON string with the following fields:
            int req_id (128-bit uuid4 integer)
            str text
    Return:
        on success, return {"status": "success", ...TBD}
        on error, return {"status": "TextServiceUploadTextError", "errors": [errors from
        each function call]}
    """
    payload = json.loads(req)

    if ('req_id' not in payload or
       'text' not in payload):
        msg = '''Make sure the input has `req_id` and `text` fields'''
        ret = json.dumps({"status":"MissingFieldError", "errors":[msg]})
        sys.exit(ret)

    req_id = payload['req_id']
    text = payload['text']
    user_mentions = user_mention_pattern.findall(text)
    user_mentions = [u[1:] for u in user_mentions if u[0] == "@"]

    urls = url_pattern.findall(text)
    url_match_obj_list= list(url_pattern.finditer(text))

    url_shorten_ret = shorten_and_upload_urls(payload['req_id'], urls)
    # if url-shorten-service-upload-urls failed, fail this function now and
    # return the error from url-shorten-service-upload-urls
    if url_shorten_ret['http_status_code'] != 200:
        sys.exit(dumps({"status":"TextServiceUploadTextError", "errors":
            [url_shorten_ret]}))

    url_doc_list = url_shorten_ret['urls']

    # update text by replacing original full urls with shortened urls
    for url_doc, url_match_obj in zip(reversed(url_doc_list),
            reversed(url_match_obj_list)):
        prefix =  text[0:url_match_obj.start()]
        suffix= text[url_match_obj.end():]
        text = prefix+url_doc['shortened_url']+suffix

    # Call user-mention-service-upload-user-mentions and
    # compose-post-service-upload-text
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures.append(executor.submit(upload_user_mentions, req_id,
            user_mentions))
        futures.append(executor.submit(upload_text, req_id,
            text))

        results = [f.result() for f in concurrent.futures.as_completed(futures)]

        ret = {"status": "TextServiceUploadTextError", "errors":[]}

        for r in results:
            if r["http_status_code"] != 200:
                ret["errors"].append(r)

        if len(ret["errors"]) == 0:
            return dumps({"status":"success", "mentions":user_mentions,
                "urls":url_shorten_ret, "text": text})
        else:
            sys.exit(dumps(ret))

