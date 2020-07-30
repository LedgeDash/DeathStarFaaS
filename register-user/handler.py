import json

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    print(req)
    payload = json.loads(req)

    if ('username' not in payload or
       'first_name' not in payload or
       'last_name' not in payload or
       'password' not in payload):
           return "Missing input"

    print(payload['username'])
    print(payload['first_name'])
    print(payload['last_name'])
    print(payload['password'])

    return req
