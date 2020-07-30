# DeathStar with FaaS

Rewriting the DeathStar Benchmark suite in a Function-as-a-Service (FaaS)
architecture.

# Supported Actions

1. Register user accounts
2. Upload user information
3. Login with user credentials (username+password)
4. Follow a user
5. Unfollow a user
6. Read a user's timeline
7. Create a post with text and optionally media (images or video)
8. Search for a user
9. Search for a post
10. Read a post

# Services and Functions

## UserService

### RegisterUser()

**Input**:

**Output**:

**Callee(s)**:

**Service(s) used**:

**Descriptions**:

### RegisterUserWithId()

### Login()

### GetUserId()

### UploadCreatorWithUserId()

### UploadCreaterWithUsername()

## ComposePostService

### UploadText()

### UploadMedia()

### UploadUniqueId()

### UploadCreator()

### UploadUrls()

### UploadUserMentions()


# Mapping DeathStar Actions to Service Functions

## Overview

The original DeathStar has the following architecture.

The front end is an NGINX webserver. Clients perform actions by requesting
specific URLs (e.g., `/api/user/register`). Those requests cause NGINX to run
corresponding LUA scripts. The mappings between URLs and LUA scripts are
configured in `socialNetwork/nginx-web-server/conf/nginx.conf`. LUA scripts are
located under `nginx-web-server/lua-scripts`.

The LUA scripts calls backend microservices through Thrift RPC. Thrift RPC
interface definition is in `social_network.thrift`. The `.thrift` file specifies
service names and function signatures (name, parameter names and types, return
value types and possible exceptions). Based on this `.thrift`
file, the thrift compiler generates the RPC stub functions for both LUA and C++.
Note that the generated code is only for sending and receiving RPC calls and
results. LUA client side code is responsible for preprocessing input data,
connecting to microservices and performing RPC.

The backend microservices run as containers. Their configurations for a
`docker-compose` deployment is in `docker-compose.yml`. Their Thrift service
names and port numbers are specified in `config/service-config.json`. (Though on
the LUA client side, port numbers for establishing connections seem to be
hard-coded.)

As a concrete example, to register an account, clients first request the URL
`/api/user/register`, passing in `first_name`, `last_name`, `username` and
`password`. This will trigger the NGINX server to run the `RegisterUser()`
function in `/api/user/register.lua`.  `RegisterUser()` checks that input data
are valid (non-empty), connects to the `UserServiceClient` by creating a
`GenericObjectPool` with the right service name and port number, then calls the
`RegisterUser()` function in `UserServiceClient`.
`UserServiceClient:RegisterUser()` is Thrift generated code (see:
`gen-lua/social_network_UserService.lua`). All it does is sending the RPC call
and receiving the RPC results. Once the RPC call finishes,
`/api/user/register.lua` returns different HTTP status codes to clients and
possibly redirects to different pages based on the RPC results.

The backend microservices don't seem to call each other directly. When performing an
action that involves multiple services, NGINX will create multiple threads, each
to call a necessary service. For example, to compose a post, NGINX calls
`UploadCreatorWithUserId()` in `user-service`, `UploadText()` in `text-service`,
`UploadMedia()` in `media-service` and `UploadUniqueID()` in
`unique-id-service`, each in a separate NGINX thread.
(TODO: need to further verify this is the case for all actions.)

## Mappings

NGINX request URL: `/api/user/register`
LUA:
1. `api/user/register.lua`:`RegisterUser()`
2. `gen-lua/social_network_UserServer.lua`:`UserServiceClient:RegisterUser()`
Container Service: `user-service` 

