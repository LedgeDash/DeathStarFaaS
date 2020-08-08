# How to invoke
With `cRUL`
```bash
curl -X POST http://40.119.49.149:8080/function/register-user --data
"@.tests/users.json"
```

With `faas-cli` (after login to OpenFaaS cluster)
```bash
cat tests/users.json |faas invoke register-user
```


