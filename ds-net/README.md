Custom Dockerfile options

`ds-net` serves static webpages. Therefore we need to config the OpenFaaS
Watchdog to always return HTTP responses with the `Content-Type` header set to
`text/html`. We do this by setting the `content_type` environment variable in
the `Dockerfile`:

```
ENV content_type="text/html"
```
