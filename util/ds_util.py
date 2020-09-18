import json
import requests

def invoke(url, req):
    '''invoke a OpenFaaS function at `url` with input parameter `req`
    Invoke a OpenFaaS function with `url` through HTTP requests.
    If the callee function succeeds, it will return a JSON string. invoke()
    then simply deserialize the JSON string into a python dict and return the
    dict.
    If the callee function fails through sys.exit(), it will return a JSON
    string as error message. invoke() then simply deserializes the JSON string
    into a python dict and return the
    If the callee function crashes not through sys.exit(), it normally returns a
    Python traceback. invoke() then returns a dict with the following contents:

    {"status": "UnknowError",
     "url": url,
     "http_status_code": http_status_code,
     "message": traceback messages}

    Args:
        url a str specifying the function's http/https route
        req a python dict to be send as JSON string
    Return: 
        a dict
    '''
    req_str = json.dumps(req)
    r = requests.get(url, data = req_str)

    if r.status_code == 200:
        ret = json.loads(r.text)
        ret['http_status_code'] = r.status_code
        return ret

    # callee failed through sys.exit
    if r.status_code == 500:
        try:
            error_msg = json.loads(clean_error_msg(r.text))
            error_msg['http_status_code'] = r.status_code
            error_msg['url'] = url
            return error_msg
        except:
            pass

    # if the error code is not 500 or the callee didn't return JSON string
    # for the 500 error (happens for example when code crashes and Python
    # returns traceback messages)
    return {"status": "UnknowError",
            "url": url,
            "http_status_code": r.status_code,
            "message": r.text}


def clean_error_msg(s):
    '''clean OpenFaaS functions' error message for JSON encoder
    When an OpenFaaS function exit on error (i.e., via `sys.exit(..)`), the
    returned message looks like this:
    s = 'exit status 1\n{"status": "UsernameAlreadyExistError", "message":
    "username troubledEagle2 already exist"}\n'
    The beginning `exit status 1\n` and the last \n throws off the json encoder.
    '''
    return s.split('\n')[1]


