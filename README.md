# DeathStar with FaaS

Rewriting the DeathStar Benchmark suite in a Function-as-a-Service (FaaS)
architecture.

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

This command will run the mongo shell directly.

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

More information on:
1. [DNS name for StatefulSet
   resources](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#stable-network-id)

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
1. `string first_name`
2. `string last_name`
3. `string username`
4. `string password`

**Output**: success or error code/message

**Callee services**: SocialGraphService:InsertUser()

**Storage used**: MongoDB

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

## SocialGraphService

### GetFollowers()

### GetFollowees()

### Follow()

### Unfollow()

### FollowWithUsername()

### UnfollowWithUsername()

### InsertUser()


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

When performing an action that involves multiple services, NGINX will create
multiple threads, each to call a necessary service. For example, to compose a
post, NGINX calls `UploadCreatorWithUserId()` in `user-service`, `UploadText()`
in `text-service`, `UploadMedia()` in `media-service` and `UploadUniqueID()` in
`unique-id-service`, each in a separate NGINX thread.

## Mappings

NGINX request URL: `/api/user/register`
LUA:
1. `api/user/register.lua`:`RegisterUser()`
2. `gen-lua/social_network_UserServer.lua`:`UserServiceClient:RegisterUser()`
Container Service: `user-service` 

