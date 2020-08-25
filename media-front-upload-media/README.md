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

