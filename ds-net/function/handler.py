import os, json
from urllib.parse import parse_qs
import requests
from function import ds_util

error_html = open("function/pages/error.html", "r")
error_html_f = error_html.read()

login_html = open("function/pages/index.html", "r")
login_html_f = login_html.read()

signup_html = open("function/pages/signup.html", "r")
signup_html_f = signup_html.read()

main_html = open("function/pages/main.html", "r")
main_html_f = main_html.read()

profile_html = open("function/pages/profile.html", "r")
profile_html_f = profile_html.read()

contact_html = open("function/pages/contact.html", "r")
contact_html_f = contact_html.read()

def index(req):
    return login_html_f

def signup(req):
    return signup_html_f

def login(req):
    values = parse_qs(req)
    if ("username" not in values or
        "password" not in values):
        return login_html_f

    req = {
            "username": values['username'][0],
            "password": values['password'][0]
            }

    function_url = "http://gateway.openfaas:8080/function/user-service-login"

    ret = ds_util.invoke(function_url, req)

    if ret['http_status_code'] != 200:
        return login_html_f
    
    return main(req)

def register(req):
    values = parse_qs(req)
    req = {
            "username": values['username'][0],
            "first_name": values['first_name'][0],
            "last_name": values['last_name'][0],
            "password": values['password'][0]
            }

    function_url = "http://gateway.openfaas:8080/function/register-user"

    ret = ds_util.invoke(function_url, req)

    if ret['http_status_code'] != 200:
        return error_html_f

    return login_html_f

def main(req):
    return main_html_f

def profile(req):
    return profile_html_f

def contact(req):
    return contact_html_f

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    path = os.getenv("Http_Path")

    return path_map[path](req)


path_map = {"/": index,
            "/login": login,
            "/signup": signup,
            "/register": register,
            "/main": main,
            "/profile": profile,
            "/contact": contact}
