Define `OPENFAAS_URL` as an env variable. For example:
```
export OPENFAAS_URL="http://40.119.49.149:8080"
```
This is also required if you want to use the OpenFaaS client side CLI tool (`faas-cli`)

Install required packages:
```
pip3 install -r requirements.txt
```

Run the tests through pytest. You can simply run `pytest -v` on the commandline

More information on pytest: https://docs.pytest.org/en/latest/index.html
