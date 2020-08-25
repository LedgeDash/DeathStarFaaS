RegisterUserWithId
additional input: `int64_t user_id`

In RegisterUser, a `int64_t user_id` is generated based on the `_machine_id` of
the machine on which the microservice runs, a counter number and the current
time stamp of the registration request
(`int64_t timestamp = duration_cast<milliseconds>(system_clock::now()...)`).
This seems to be a manual implementation of UUID Version 1 (`uuid.uuid1() function
in Python's uuid package).

## Uniqueness problem
The social network application wants global uniqueness for all user IDs. There are
multiple processes for registering user accounts. How to guarantee uniqueness?

A centralized sequencer could work.

UUID could also work, but it relies on getting the current timestamp. There is
a chance that 2 threads on the same machine gets the timestamp at the same time.
In the DeathStar implementation, they take a lock before `system_clock::now()`.
But how to do this in Cloudflare Workers where each `RegisterUser` function runs
in its own Isolate and there is global coordinator for creating function instances
so that they can all share a lock? Cloudflare could provide their own uuid
implementation where node ID is changed from the machine's MAC address to an
Isolate's ID. Then how many more packages do they need to re-implement?

This is not a problem in AWS Lambda, because functions run in VMs. As long as
each VM gets a unique node name, UUIDs won't have duplicates.

Or use UUID4 and rely on randomness.

# OpenFaaS
`sys.exit('error msg')` will return result with `Server returned unexpected
status code: 500 - exit status 1`, whereas `return('message')` will return
status code 200.


I can just return a dict and OpenFaaS runtime will convert that into a string:
```
return {"status": "success", "user_id": found['user_id']}
sys.exit({"status": "SomeError", "message": error_message})
```
**actually, I can't do this. Because this won't return a json string. fields will be
enclosed in single quotes... which causes `json.loads()` to fail.**
On the client side then, I can convert the string into a dictionary via `json.loads()`

# MongoDB

Access directly on the AKS cluster: `kubectl exec -it mongo-0 -- sh`. This
gives you a shell into the pod named `mongo-0`which is the primary node of
MongoDB.

To access the database for user account:

```bash
use users # switch to db `users`
db.getCollectionInfos()
db.users.find({}) # perform a query on the `users` collection and find everything
```

To clear all documents in a collection:
```bash
db.social_graph.remove({})
```

```
res = users.insert_one(new_user_doc)
print(new_user_doc)
```
`users.insert_one()` actually returns the new MongoDB document in
`new_user_doc`. In practice, this means that after `insert_one()`,
`new_user_doc` now also has a field `_id:ObjectId(..)`.

To use `from bson.json_util import dumps, loads`, we need to install `pymongo`.
In the case of OpenFaaS functions, this means adding `pymongo` into the
`requirements.txt` file.

# Data format

Fields don't include the MongoDB default `_id` field unless we manually create it.

Python and BSON data structure mapping: 

### MongoDB for users:

db: users

collection: users

fields:
1. `username`: string
2. `first_name`: string
3. `last_name`: string
4. `password`: hex string of hash
5. `user_id`: hex string of UUID4
6. `salt`: random string generated by secrets

See `register-user/handler.py` for details

### MongoDB for social graph

db: social_graph

collection: social_graph

fields:
1. `user_id`
2. `followers`: list (BSON array)
3. `followees`: list

# Mappings

Microservice types: `https://github.com/delimitrou/DeathStarBench/blob/master/socialNetwork/gen-cpp/social_network_types.h`

NGINX request URL: `/api/user/register`
LUA:
1. `api/user/register.lua`:`RegisterUser()`
2. `gen-lua/social_network_UserServer.lua`:`UserServiceClient:RegisterUser()`
Container Service: `user-service` 

NGINX request URL: `/api/post/compose`
LUA:
`api/post/compose.lua`:`ComposePost()`

user_id

username

req_id

`post`:
1. post.media_ids
2. post.media_types
3. post.post_type
4. post.text

creates 4 threads each calls:
1. `api/post/compose.lua`:`_UploadMedia(req_id, post)`
    1. `social_network_MediaService.lua`:`UploadMedia(req_id, post.media_types, post.media_ids)`
        1. `src/MediaService/MediaHandler.h`:`UploadMedia(req_id, vector<string> media_types, vector<int64_t>media_ids)`:
            compose_post_client->UploadMedia(req_id, media)
            1. `src/ComposePostService/ComposePostHandler.h`:UploadMedia(req_id, vector<Media>)
2. `api/post/compose.lua`:`_UploadUserId(req_id, user_id, username)`
    1. social_network_UserService:UploadCreatorWithUserId(req_id, user_id, username)
        1. `src/UserService/UserHandler.h`:`UploadCreatorWithUserId(req_id, user_id, username)
            compose_post_client->UploadCreator(req_id, creator)
            1. `src/ComposePostService/ComposePostHandler.h`:UploadCreator(req_id, vector<Media>)
3. `api/post/compose.lua`:`_UploadText(req_id, post)`
    1. social_network_TextService:UploadText(req_id, post.text)
        1. `src/TextService/TextHandler.h`:`UploadText(req_id, string text)`
            regex match on the text to get `vector<string> user_mentions` and `vector<string> urls`
            url_client->UploadUrls(return_urls, req_id, urls)
            user_mention_client->UploadUserMentions(req_id, user_mentions)
            compose_post_client->UploadText(req_id, updated_text)
            1. `src/UrlShortenService/UrlShortenHandler.h`:`UploadUrls(req_id, vector<string> urls)`:
                1. write to Mongo db: `url-shorten`, collection: `url-shorten` in bulk
                2. compose_post_client->UploadUrls(req_id, vector<Url> target_urls)
                    1. `src/ComposePostService/ComposePostHandler.h`:`UploadUrls(req_id, urls)`
            2. `src/UserMentionService/UserMentionHandler.h`:`UploadUserMentions(req_id, vector<string> usernames)`
                1. construct a vector<UserMention> user_mentions by querying memcached and mongodb
                2. compose_post_client->UploadUserMentions(req_id, user_mentions)
                    1. `src/ComposePostService/ComposePostHandler.h`:UploadUserMentions(req_id, vector<UserMention>)
4. `api/post/compose.lua`:`_UploadUniqueId(req_id, post)`
    1. social_network_UniqueIdService: UploadUniqueId(req_id, tonumber(post.type))
        1. `src/UniqueIdService/UniqueIdHandler.h`:`UploadUniqueId(req_id, PostType::type post_type)`
            compose_post_client->UploadUniqueId(req_id, post_id, post_type)
            1. `src/ComposePostService/ComposePostHandler.h`:`UploadUniqueId(req_id, post_id, post_type)
