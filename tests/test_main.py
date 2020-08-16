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

def test_follow():
    '''every element in the `user_accounts` follow the next element in the list
    and the last element follows everyone
    '''
    for i in range(0, len(user_accounts)-1):
        user_id = user_accounts[i]['user_id']
        followee_id = user_accounts[i+1]['user_id']
        ret = follow(user_id, followee_id)
        assert ret.status_code == 200

    last = user_accounts[len(user_accounts)-1]
    for i in range(0, len(user_accounts)-1):
        ret = follow(last['user_id'], user_accounts[i]['user_id'])
        assert ret.status_code == 200

    for i in range(0, len(user_accounts)-1):
        follower = user_accounts[i]
        followee = user_accounts[i+1]

        # check everyone's followees list has the next element
        ret = get_followees(follower['user_id'])
        assert ret.status_code == 200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'
        followees_list = payload['followees']
        #print('user_id: ' + follower['user_id'] + ", followees: " +
        #        str(followees_list))
        assert check_user_id_in_list(followee['user_id'], followees_list) == True

        # check everyone's followers list has the previous element
        ret = get_followers(followee['user_id'])
        assert ret.status_code == 200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'
        followers_list = payload['followers']
        assert check_user_id_in_list(follower['user_id'], followers_list) == True

        # check everyone has the last element in its followers list
        #print('last user_id: {}'.format(last['user_id']))
        #print('user_id: ' + followee['user_id'] + ", followers: " +
        #        str(followers_list))
        if followee != last:
            assert check_user_id_in_list(last['user_id'], followers_list) == True

    # check the last user has everyone in its followees list
    last = user_accounts[len(user_accounts)-1]
    ret = get_followees(last['user_id'])
    assert ret.status_code == 200

    payload = json.loads(ret.text)
    assert payload['status'] == 'success'
    followees_list = payload['followees']

    for i in range(0, len(user_accounts)-1):
        assert check_user_id_in_list(user_accounts[i]['user_id'], followees_list) == True

def test_unfollow():
    for i in range(0, len(user_accounts)-1):
        follower_id = user_accounts[i]['user_id']
        followee_id = user_accounts[i+1]['user_id']
        ret = unfollow(follower_id, followee_id)
        assert ret.status_code == 200

        # check follower's followees list no long has followee_id
        ret = get_followees(follower_id)
        assert ret.status_code == 200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'
        followees_list = payload['followees']
        assert check_user_id_in_list(followee_id, followees_list) == False

        # check followee's followers list no long has follower_id
        ret = get_followers(followee_id)
        assert ret.status_code == 200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'
        followers_list = payload['followers']
        assert check_user_id_in_list(follower_id, followers_list) == False

def test_follow_with_username():
    '''every element in the `user_accounts` follow the next element in the list
    '''
    for i in range(0, len(user_accounts)-1):
        username = user_accounts[i]['username']
        followee_name = user_accounts[i+1]['username']
        ret = follow_with_username(username, followee_name)
        assert ret.status_code == 200

    for i in range(0, len(user_accounts)-1):
        follower = user_accounts[i]
        followee = user_accounts[i+1]

        # check everyone's followees list has the next element
        ret = get_followees(follower['user_id'])
        assert ret.status_code == 200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'
        followees_list = payload['followees']
        #print('user_id: ' + follower['user_id'] + ", followees: " +
        #        str(followees_list))
        assert check_user_id_in_list(followee['user_id'], followees_list) == True

        # check everyone's followers list has the previous element
        ret = get_followers(followee['user_id'])
        assert ret.status_code == 200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'
        followers_list = payload['followers']
        assert check_user_id_in_list(follower['user_id'], followers_list) == True



def test_unfollow_with_username():
    for i in range(0, len(user_accounts)-1):
        follower_name = user_accounts[i]['username']
        followee_name = user_accounts[i+1]['username']
        follower_id = user_accounts[i]['user_id']
        followee_id = user_accounts[i+1]['user_id']
        ret = unfollow_with_username(follower_name, followee_name)
        assert ret.status_code == 200

        # check follower's followees list no long has followee_id
        ret = get_followees(follower_id)
        assert ret.status_code == 200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'
        followees_list = payload['followees']
        assert check_user_id_in_list(followee_id, followees_list) == False

        # check followee's followers list no long has follower_id
        ret = get_followers(followee_id)
        assert ret.status_code == 200

        payload = json.loads(ret.text)
        assert payload['status'] == 'success'
        followers_list = payload['followers']
        assert check_user_id_in_list(follower_id, followers_list) == False



'''Helper functions
'''
def check_user_id_in_list(user_id, l):
    '''check if a user_id in the followers or followees list
    followers and followees lists have documents of the format {"user_id":
    "xxx", "timestamp":1247089}
    '''
    for e in l:
        if e['user_id'] == user_id:
            return True

    return False

def clean_error_msg(s):
    '''clean OpenFaaS functions' error message for JSON encoder
    When an OpenFaaS function exit on error (i.e., via `sys.exit(..)`), the
    returned message looks like this:
    s = 'exit status 1\n{"status": "UsernameAlreadyExistError", "message":
    "username troubledEagle2 already exist"}\n'
    The beginning `exit status 1\n` and the last \n throws off the json encoder.
    '''
    return s.split("\n")[1]

def unfollow_with_username(username, followee_name):
    '''user_id unfollow followee_id
    user_id should be removed from the the `followers` list of followee_id in the
    social graph. followee_id should be removed from the `followees` list of user_id
    '''
    req = json.dumps({"username":username, "followee_name":followee_name})
    r = requests.get(openfaas_url +
            "/function/social-graph-unfollow-with-username",
            data=req)
    return r

def follow_with_username(username, followee_name):
    '''user_id follow followee_id
    user_id should be added to the the `followers` list of followee_id in the
    social graph. followee_id should be added to the `followees` list of user_id
    '''
    req = json.dumps({"username":username, "followee_name":followee_name})
    r = requests.get(openfaas_url + "/function/social-graph-follow-with-username",
            data=req)
    return r


def unfollow(user_id, followee_id):
    '''user_id unfollow followee_id
    user_id should be removed from the the `followers` list of followee_id in the
    social graph. followee_id should be removed from the `followees` list of user_id
    '''
    req = json.dumps({"user_id":user_id, "followee_id":followee_id})
    r = requests.get(openfaas_url + "/function/social-graph-unfollow",
            data=req)
    return r

def follow(user_id, followee_id):
    '''user_id follow followee_id
    user_id should be added to the the `followers` list of followee_id in the
    social graph. followee_id should be added to the `followees` list of user_id
    '''
    req = json.dumps({"user_id":user_id, "followee_id":followee_id})
    r = requests.get(openfaas_url + "/function/social-graph-follow",
            data=req)
    return r

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
