# DeathStarFaaS

The DeathStar Benchmark suite in a Function-as-a-Service (FaaS) architecture.

# How to Deploy

The current version of DeathStarFaaS is implemented on top of OpenFaaS
and Kubernetes. You need a Kubernetes cluster, install on it OpenFaaS and other
services (e.g., MongoDB) and then install DeathStarFaaS to the OpenFaaS
deployment.

## Install OpenFaaS

The current implementation is tested on
[AKS](https://docs.microsoft.com/en-us/azure/aks/). Follow [AKS' guide on
installing OpenFaaS](https://docs.microsoft.com/en-us/azure/aks/openfaas)

To learn more about using OpenFaaS, check out their
[workshop](https://github.com/openfaas/workshop).

## Deploy MongoDB

### Kubernetes Setup

DeathStarFaaS uses MongoDB for persistent storage. One option is to deploy a
MongoDB instance on the same Kubernetes cluster as your OpenFaaS deployment. We
provide the necessary config files to deploy MongoDB on AKS. See
`aks/mongodb-k8s.yaml` and `aks/azure-storageclass.yaml`.

Simply use `kubectl apply` or `kubectl create` to deploy it. This will create
three things:
1. A StorageClass resource that dynamically creates a AZure File off of which we
   can later create PersistentVolumeClaims for MongoDB Pods.
2. A StatefulSet named "mongo" with 3 replicas. This will create 3 Pods with
   names `mongo-0`, `mongo-1` and `mongo-2`. You don't have to use 3 replicas or
   any replication at all.
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
works on your platform. Most likely, you'll need to change at least the
StorageClass resource because it's cloud-provider-specific.

### Initialize MongoDB

After all MongoDB pods get into the `Running` status, we can initialize the
MongoDB deployment.

Get a shell into one of the mongo pods (we use `mongo-0` here) by `kubectl
exec`:

```bash
kubectl exec -it mongo-0 -- mongo
```

This command will run the mongo shell directly in the primary MongoDB pod
(`mongo-0`).

Once you're inside the mongo shell, initialize the deployment and add all 3 pods
to the Replica Set (here we're talking about the MongoDB Replica Set not the K8S
ReplicaSet):


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

You can get a Mongo shell into the pod running the master MongoDB replica. In
our case, it is pod `mongo-0`:

```
kubectl exec -it mongo-0 -- mongo
```

## Redis

Similarly we provide a K8s resource config file for deploying a Redis instance on K8s.
See `aks/redis-k8s.yaml`.

### Quick Testing of Redis

Similarly you can get a shell into the pod running the Redis instance:

```
kubectl exec -it <redis-pod-name> -- redis-cli
```


## Deploy DeathStarFaaS

`stack.yml` contains OpenFaaS specifications for all functions in DeathStarFaaS.
After [logging in to your OpenFaaS deployment through the CLI
client](https://docs.microsoft.com/en-us/azure/aks/openfaas#deploy-openfaas)
(`faas-cli`) and navigating to the same directory as the `stack.yml` file, you
can simply deploy the entire DeathStarFaaS application by `faas-cli up`.
`faas-cli up` is a shortcut for building, uploading and deploying all functions
defined in a `stack.yml` file in the current directory.

See this [OpenFaaS workshop](https://github.com/openfaas/workshop/blob/master/lab3.md)
for more details on deploying applications.

### Specifying MongoDB and Redis URI

Functions that interact with the MongoDB or Redis services obtain the service
URIs through environment varialbes. We use `MONGO_URI` for MongoDB and
`REDIS_SERVER` and `REDIS_PORT` for Redis.  For example,
`user-timeline-service-write-user-timeline` interacts with both MongoDB and
Redis. Therefore its section in `stack.yml` contains the following environment
variable definition:

```yaml
environment:
    MONGO_URI: "mongodb://mongo-0.mongo.default"
    REDIS_SERVER: "ds-redis.default"
    REDIS_PORT: 6379
```

Modify the URIs based on your configuration.

### Timeouts

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

# Testing

You can run DeathStarFaaS tests with the pytest framework. Just change directory
to `/tests` and run `pytest -v`.

For more details, see `/test/README.md`.

# Design

## Original DeathStar

[Architecture graph](docs/DeathStarOriginal.pdf)

The original DeathStar has the following architecture:

The frontend are two NGINX webservers serving client-facing APIs via HTTP endpoints.
The main NGINX server serves the following routes:

1. `/api/user/register`
2. `/api/user/follow`
3. `/api/user/unfollow`
4. `/api/user/login`
5. `/api/post/compose`
6. `/api/user-timeline/read`
7. `/api/user/get_follower`
8. `/api/user/get_followee`

There's an additional `media-frontend` NGINX server that serve the following
routes:

1. `/upload-media`
2. `/get-media`

Clients (e.g., web browsers) interact with the application by issuing HTTP
requests to those endpoints.

For each request to an endpoint, the NGINX servers execute a LUA script which in
turn sends RPCs to docker containers running at the backend. Containers may send
RPCs to other containers if the request processing involves multiple
microservices.

All RPCs are Apache Thrift RPCs.

Each microservice has a pool of running containers and each container can serve
all APIs of the microservice.

## DeathStarFaaS

[Architecture graph](docs/DeathStarFaaS.pdf)

There are no webservers in DeathStarFaaS. Instead, each HTTP endpoint is
replaced by an OpenFaaS function. For example, the original `/api/post/compose`
endpoint is now the `compose-post-front` function which is accessible at
`http://<openfaas-url>/function/compose-post-front`. You invoke the function by
sending HTTP requests with JSON payload.

There are no microservices either in DeathStarFaaS. Instead, each microservice
is replaced by a set of functions each of which implements an API of the
original microservice. For example, there are now 2 functions
`read-user-timeline` and `write-user-timeline` that replace the original
`UserTimelineService`.

Functions call each other via HTTP requests.

## Function Interface

Inputs and outputs to DeathStarFaas functions are JSON strings.

Each function expects JSON inputs with particular fields. See comments in
`handler.py` of each function for details.

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

### HTTP Status Code

DeathStarFaaS functions return HTTP 200 on success and 500 on error. 200 code
is sent by simply calling `return` in python whereas 500 is sent by
exiting via `sys.exit()`.

### Error Messages

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

## Data Format

### User

**MongoDB:**

DB: `users`

Collection: `users`

Format:
```
{
    "username": "username_str",
    "user_id": "uuid4_hex_str",
    "first_name": "first_name_str",
    "last_name": "last_name_str",
    "salt": "random_32_character_str",
    "password": "hash_of_user_password_and_salt"
}
```

### Social Graph Node

**MongoDB:**

DB: `social_graph`

Collectoin: `social_graph`

Format:
```
{
    "user_id": "user_id",
    "followers: ["user_ids"],
    "followees: ["user_ids"]
}
```

### Url

**MongoDB:**

DB: `url_shorten`

Collection: `url_shorten`

Format:
```
{
    "expanded_url": "url_string",
    "shortened_url": "url_string"
}
```

### Post

**MongoDB:**

DB: `post`

Collection: `post`

Format:
```
{
    "req_id": "uuid_str",
    "post_id": "uuid_str",
    "creator":
        {
            "user_id": "user_id",
            "username" "username"
        },
    "text": "string",
    "timestamp": integer,
    "media": 
        {
            "media_id": "string",
            "media_type": "string"
        },
    "urls: [url_documents],
    "user_mentions": [{"username": "username", "user_id": "user_id"}]
}
```

**Redis:**

Type: hash

Expire: 60 seconds

Format: same as in MongoDB

### User timeline

**Redis:**

Type: Sorted set

Element: `post_ids`

Scores: timestamps of posts

Key: `user_id` of the creator

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

