Upload media (videos and images) to AZure blob storage.

Interacting with AZure blob storage requires `azure-storage-blob` python
package, which in turns requires the following packages and binaries when built
in Alpine Linux:
1. gcc
2. musl-dev
3. python-dev
4. libffi-dev
5. openssl-dev

This function is a `dockerfile` type function, not a `python3` type function so
that we can install the above custom packages and binaries. You can see the
language type in the OpenFaaS `stack.yaml` file.

# Connection with AZure blob storage
Blob storage connection string and container name are passed into the function
as environment variables. You can specify them in the `stack.yaml` file:
```yaml
  media-front-upload-media:
    lang: dockerfile
    handler: ./media-front-upload-media
    image: ledgedash/media-front-upload-media:latest
    environment:
        BLOB_STORAGE_CONNECTION_STRING: "DefaultEndpointsProtocol=https;AccountName=davidhliu2020sfaas;AccountKey=dNrgfTFfCcINupXC0tnLaDxmkVeFnQhq0cFn8UO+WwOlzYiyLuZSY6bwSmAt4TkehFCkFBuNLgDvTAEBVERPKQ==;EndpointSuffix=core.windows.net"
        CONTAINER_NAME: "deathstar-media"
```
To make DeathStarFaaS work with your AZure blob storage backend, use your own
connection string and container name.
