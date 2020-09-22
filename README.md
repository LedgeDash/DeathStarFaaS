# DeathStarFaaS

The DeathStar Benchmark suite in a Function-as-a-Service (FaaS) architecture.

# How to Deploy

The current version of DeathStarFaaS is implemented on top of OpenFaaS
and Kubernetes. You need a Kubernetes cluster, install on it OpenFaaS and other
services (e.g., MongoDB) and then install DeathStarFaaS to the OpenFaaS
deployment.

## Getting started with OpenFaaS
The current implementation is tested on
[AKS](https://docs.microsoft.com/en-us/azure/aks/). Follow AKS' guide for
installing OpenFaaS: https://docs.microsoft.com/en-us/azure/aks/openfaas

To learn more about using OpenFaaS, checkout their
[workshop](https://github.com/openfaas/workshop).

## Installing DeathStarFaaS

All functions of DeathStarFaaS are specified in the `stack.yml` file. Therefore,
after logging in to your OpenFaaS deployment through the CLI client
(`faas-cli`) and navigating to the same directory as the `stack.yml` file, you
can simply deploy the entire DeathStarFaaS application by

```bash
faas-cli up
```

See [OpenFaaS workshop](https://github.com/openfaas/workshop/blob/master/lab3.md)
for more details on deploying applications.

## Deploy MongoDB

### Kubernetes Setup
DeathStarFaaS uses MongoDB for persistent storage. One option is to deploy a
MongoDB instance on the same Kubernetes cluster as your OpenFaaS deployment. We
provide the necessary config files to deploy MongoDB on AKS.

Simply use `kubectl apply` or `kubectl create` to deploy it. This will create
three things:
1. A StorageClass resource that dynamically creates a AZure File so that we can
   later create PersistentVolumeClaims off of it and use them for our MongoDB Pods.
2. A StatefulSet named "mongo" with 3 replicas. This will create 3 Pods with
   names `mongo-0`, `mongo-1` and `mongo-2`.
3. A Headless Service (type: `ClusterIP`) exposing the MongoDB pods to other
   pods inside the cluster.

We use the cheapest redundancy option for the AZure File in the StorageClass
resource.

The StatefulSet configuration includes a persistent volume claim off
of the StorageClass resource (so you don't need to separately create a
PersistentVolumeClaim resource for the MongoDB pods to use).

For more information:
1. [Dynamically create persistent volumes with AZure
   File](https://docs.microsoft.com/en-us/azure/aks/azure-files-dynamic-pv)
2. [Storage redundancy options for AZure
   File](https://docs.microsoft.com/en-us/azure/storage/common/storage-redundancy)
3. [StorageClass resources for AZure
   File](https://kubernetes.io/docs/concepts/storage/storage-classes/#azure-file)
4. [K8S
   StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)

If you're using a different cloud provider, adapt the config files so that it
works on your platform. 

### Initialize MongoDB

After all MongoDB pods get into the RUNNING status, we can initialize the
MongoDB deployment.

Get a shell into one of the mongo pods (we use `mongo-0` here) by `kubectl
exec`:

```bash
kubectl exec -it mongo-0 -- mongo
```

This command will run the mongo shell directly in the primary MongoDB pod
(`mongo-0`).

Once you're inside the mongo shell, initialize the deployment and add all 3 pods
to the Replica Set (here we're talking about the MongoDB Replica Set not K8S
ReplicaSet)


```bash
rs.initiate()
var cfg = rs.conf()
cfg.members[0].host="mongo-0.mongo:27017"
rs.reconfig(cfg)
rs.add("mongo-1.mongo:27017")
rs.add("mongo-2.mongo:27017")
```

Check the status to make sure all 3 pods are added and functioning properly by
`rs.status()`.

More information on
1. [Get a shell into a running
   container (`kubectl exec`)](https://kubernetes.io/docs/tasks/debug-application-cluster/get-shell-running-container/)
2. MongoDB [Replica Set](https://docs.mongodb.com/manual/tutorial/deploy-replica-set/)

### Namespace and DNS Names

You can deploy MongoDB in any K8S namespace, but accessing the MongoDB within
the same namespace differs from across namespaces.

Within the same namespace, you can connect to the MongoDB simply through
`mongodb://mongo` via the service or `mongodb://mongo-0.mongo` via the pod. You
could also connect to `mongodb://mongo-0.mongo,mongo-1.mongo,mongo-2.mongo`.

Across namespace, the domain managed by the Headless Service takes the form:
`$(service name).$(namespace).svc.cluster.local`, where "cluster.local" is the
cluster domain.

In our case, all OpenFaaS functions live under the `openfaas-fn` namespace and
need to access the MongoDB via `mongodb://mongo.default.svc.cluster.local`. They
can address the pods via for example `mongodb://mongo-0.mongo.default`.

In the case of multiple MongoDB replicas, `Not master` error might occur if
accessing via the Headless Service's DNS name. An easy fix is to use the
master's address, which in the case is `mongodb://mongo-0.mongo.default`.

More information on:
1. [DNS name for StatefulSet
   resources](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#stable-network-id)

### Quick Testing of MongoDB

```
kubectl exec -it mongo-0 -- mongo
```

## Redis

## Specifying MongoDB and Redis URI

Functions that interact with the MongoDB or Redis services obtain the service
URIs through environment varialbes. We use `MONGO_URI` for MongoDB and `REDIS_SERVER` and `REDIS_PORT` for Redis.
For example, `user-timeline-service-write-user-timeline` interacts with both
MongoDB and Redis. Therefore its section in `stack.yml` contains the following
environment variable definition:

```yaml
environment:
    MONGO_URI: "mongodb://mongo-0.mongo.default"
    REDIS_SERVER: "ds-redis.default"
    REDIS_PORT: 6379
```
## Timeouts

~Though according to documentation, the default function timeouts are 20s,
experiments showed that timeouts are around 5s. For example, in the case of
`compose-post-frontend`, whenever the e2e runtime exceeds 5s, the OpenFaaS
gateway returns `502` without any error messages from the functions.~

OpenFaaS has a default timeout of 5s for functions. This timeout is independent
of the gateway timeout (default 20s and was increased to 60 in my test
deployment). However, if a function timeouts, the error we receive is `502` from
the gateway with no error messages from the function.

> If we check the gateway deployment, we can see the environment variables
> for timeouts:
> 
> ```
> kubectl describe deployment/gateway -n openfaas
> Environment:                   
> read_timeout:             65s
> write_timeout:            65s
> upstream_timeout:         60s
> ```

Therefore, we manually increase the timeouts to 20s on each function. If you
face similar issues on your system, consider adjusting the timeouts manually.

More on OpenFaaS timeouts:
1. [Timeout chapter in OpenFaaS
   workshop](https://github.com/openfaas/workshop/blob/master/lab8.md)
2. [Troubleshooting chapter in the official
   documentation](https://docs.openfaas.com/deployment/troubleshooting/#timeouts)

## Other configurable options


# Testing

You can run DeathStarFaaS tests with the pytest framework. Just change directory
to `/tests` and run `pytest -v`.

For more details, see `/test/README.md`.

# Interface

DeathStarFaas functions return JSON strings.

On success, functions return `{"status": "success", "other_fields": ...}`.

On failures, functions return `{"status": "SomeError", "errors":
[error_message_objects]}`.

For example, if a username already exists when registering, `register-user`
function returns `{"status":"UsernameAlreadyExistError", "errors": [{"message":
"username ... already exists"}]}`. If a function calls other functions and
those callee functions could each fail independently, the caller returns errors
from each callee in the `"errors"` array. For example, the
`compose-post-frontend` function calls 4 other functions. If any of the 4
functions fail, their error message is stored in the `"errors"` array and
returned by `compose-post-frontend`.

See individual function's README for more details.

## HTTP Status Code

DeathStarFaaS functions return HTTP 200 on success and 500 on error. 200 code
is sent by simply calling `return` in python whereas 500 is sent by
exiting via `sys.exit()`.

## Error Messages

Note that on `sys.exit()`, the OpenFaaS runtime will prefix a string `exit
status 1\n`. For example, the actually payload of the HTTP response might look
like:
```
s = 'exit status 1\n{"status": "UsernameAlreadyExistError", "message": "username troubledEagle2 already exist"}\n'
```
So to get the actual error responses from DeathStarFaaS functions, you need to
"clean" the response text a bit. See `test/test_main.py:clean_error_msg()` for
an example.

Furthermore, if the Python code crashes and dumps traceback messages, those
messages are returned as strings. If a client calls the function directly, the
client will receive the traceback messages in the payload of HTTP responses. If
a function calls the faulting function, the caller function will return the
callee's traceback message in the `"errors"` array when the caller exits.

# Data Format

## MongoDB

## Redis

# List of frontend APIs

1. /user/unfollow
2. /user/follow
3. /user/register
4. /post/compose
5. /user-timeline/read
6. /home-timeline/read


# List of DeathStar services and functions

### UserService

- [x] RegisterUser()
- [x] RegisterUserWithId()
- [ ] Login()
- [x] GetUserId()
- [x] UploadCreatorWithUserId()
- [x] ~UploadCreaterWithUsername()~

### SocialGraphService

- [x] GetFollowers()
- [x] GetFollowees()
- [x] Follow()
- [x] Unfollow()
- [x] FollowWithUsername()
- [x] UnfollowWithUsername()
- [x] InsertUser()


### ComposePostService

- [x] UploadText()
- [x] UploadMedia()
- [x] UploadUniqueId()
- [x] UploadCreator()
- [x] UploadUrls()
- [x] UploadUserMentions()

### UniqueIdService

- [x] UploadUniqueId()

### TextService

- [x] UploadText()

### PostStorageService

- [x] StorePost
- [x] ~ReadPost~
- [x] ReadPosts

### HomeTimelineService

- [x] ~ReadHomeTimeline~

### UserTimelineService

- [x] ReadUserTimeline
- [x] WriteUserTimeline

### UserMentionSerive

- [x] UploadUserMentions

### UrlShortenService

- [x] UploadUrls
- [ ] GetExtendedUrls

### MediaService

- [x] UploadMedia


**Notes:**

1. `UserTimelineService:ReadUserTimeline()` and
`HomeTimelineService:ReadHomeTimeline()` have identical functionalities. The
original DeathStar only actually uses `HomeTimelineService:ReadHomeTimeline()`
even to read timeline of users other than the currently-logged-in user.
Therefore, we only implement `UserTimelineService:ReadUserTimeline()`.
   1. In the future, if we want to add permissions to posts (e.g., only viewable
      by followers), we can augment `ReadUserTimeline()`'s interface to include
      the `user_id` of the caller.
2. In PostStorageService, `ReadPosts()` subsumes `ReadPost(). Therefore, we only
   implement `ReadPosts()`. The original DeathStar only actually uses
   `ReadPosts()`.

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

When performing an action that involves multiple services, NGINX will create
multiple threads, each to call a necessary service. For example, to compose a
post, NGINX calls `UploadCreatorWithUserId()` in `user-service`, `UploadText()`
in `text-service`, `UploadMedia()` in `media-service` and `UploadUniqueID()` in
`unique-id-service`, each in a separate NGINX thread.


