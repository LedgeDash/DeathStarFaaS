# How to invoke
With `cRUL`
```bash
curl -X POST http://40.119.49.149:8080/function/register-user --data
"@./users.json"
```

With `faas-cli` (after login to OpenFaaS cluster)
```bash
cat users.json |faas invoke register-user
```


