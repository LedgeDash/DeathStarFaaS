import json
import uuid

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

    user_id = uuid.uuid4()

    print('user_id: {}'.format(user_id))

    import pymongo
    client = pymongo.mongo_client.MongoClient('mongodb://mongo.default.svc.cluster.local')
    db = client.test

    print(db.list_collection_names())
    print(db.houses.find_one())

    return req
