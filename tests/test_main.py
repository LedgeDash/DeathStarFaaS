import json
import os
import sys
import string
import random
import names
import requests
from random_username.generate import generate_username

openfaas_url = os.environ['OPENFAAS_URL']
print('OpenFaaS URL: {}'.format(openfaas_url))
num_users = 10
usernames = generate_username(num_users)
password_set = string.ascii_letters + string.punctuation+ string.digits
user_accounts = [{"username": usernames[i],
                  "first_name": names.get_first_name(),
                  "last_name": names.get_last_name(),
                  "password": "".join(random.choice(password_set) for x in range(0,16))}
                  for i in range(0,num_users)]

''' Test cases
'''
def test_register_users():
    '''test registering user accounts
    '''
    for info in user_accounts:
        ret = register_user(info)
        assert ret.status_code == 200
        payload = json.loads(ret.text)
        assert payload['status'] == 'success'

def test_register_duplicate():
    '''test the register-user function prevents creating accounts with the same
    username
    '''
    ret = register_user(user_accounts[0])
    ret = register_user(user_accounts[0])
    assert ret.status_code == 500
    payload = json.loads(clean_error_msg(ret.text))
    assert payload['status'] == 'UsernameAlreadyExistError'

def test_get_id():
    '''test user_id is added to a user account after registration and that the
    get-user-id can return the correct user_id
    '''
    for account in user_accounts:
        ret = get_user_id(account['username'])
        assert ret.status_code ==200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'
        assert len(payload['user_id'])==32

        # NOTE: This function changes the states of `user_account`. Subsequent
        # test functions will have access to a `user_id` field for each dict in
        # `user_accounts` list. This can simplify tests that involve user_id's
        # (which there are many).
        account['user_id'] = payload['user_id']

def test_nonexistent_user_id():
    '''test is given a nonexistent username, get-user-id correctly return error
    '''
    ret = get_user_id("foo")
    assert ret.status_code == 500
    payload = json.loads(clean_error_msg(ret.text))
    assert payload['status'] == 'UsernameNotFoundError'


def test_get_social_graph_node():
    '''test if a user account(user_id) is added to the social graph after
    registration
    '''
    for account in user_accounts:
        ret = get_followers(account['user_id'])
        assert ret.status_code ==200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'

def test_initial_empty_follower_list():
    '''test that when a node in social graph is first created, its follower list
    is empty
    '''
    for account in user_accounts:
        ret = get_followers(account['user_id'])
        assert ret.status_code ==200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'
        assert payload['followers'] == []

def test_initial_empty_followee_list():
    '''test that when a node in social graph is first created, its followee list
    is empty
    '''
    for account in user_accounts:
        ret = get_followees(account['user_id'])
        assert ret.status_code ==200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'
        assert payload['followees'] == []

'''Helper functions
'''
def clean_error_msg(s):
    '''clean OpenFaaS functions' error message for JSON encoder
    When an OpenFaaS function exit on error (i.e., via `sys.exit(..)`), the
    returned message looks like this:
    s = 'exit status 1\n{"status": "UsernameAlreadyExistError", "message":
    "username troubledEagle2 already exist"}\n'
    The beginning `exit status 1\n` and the last \n throws off the json encoder.
    '''
    return s.split("\n")[1]

def get_followers(user_id):
    '''given a user_id, get its followers
    '''
    req = json.dumps({"user_id":user_id})
    r = requests.get(openfaas_url + "/function/social-graph-get-followers",
            data=req)
    return r

def get_followees(user_id):
    '''given a user_id, get its followees
    '''
    req = json.dumps({"user_id":user_id})
    r = requests.get(openfaas_url + "/function/social-graph-get-followees",
            data=req)
    return r

def get_user_id(username):
    '''given a username, get its id if exists
    '''
    req = json.dumps({"username":username})
    r = requests.get(openfaas_url + "/function/get-user-id",
            data=req)
    return r

def register_user(info):
    '''register a single user account

    @param info a dict with user information
    '''
    r = requests.get(openfaas_url + "/function/register-user",
            data=json.dumps(info))
    return r


def main():
    r = requests.get(openfaas_url + "/function/figlet",
            data="DD")
    print(r)
    print(r.status_code)
    print(r.text)


if __name__ == '__main__':
    main()
