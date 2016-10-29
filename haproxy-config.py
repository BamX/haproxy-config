#!/usr/bin/env python
import json

authGroup = "UsersForAuth"

jsonFile = "haproxy.json"
haproxyFile = "haproxy.cfg"

frontendTemplate = """frontend http_frontend
bind *:{port}
mode http
option httpclose{frontend_lines}
"""

defaultFrontendLineTemplate = """
default_backend {name}_web"""

frontendLineTemplate = """
acl is_{name} hdr_end(host) -i {host}
use_backend {name}_web if is_{name}"""

authUsersTemplate = """
userlist {auth_group}{user_lines}"""

authUserTemplate = """
user {login} insecure-password {password}"""

backendTemplate = """

backend {name}_web
mode http{auth}{cookies}
server {name}_server {remote}:{port} check{check_cookies}"""

authTemplate = """
acl is_auth_ok http_auth({auth_group})
http-request auth realm {realm} if !is_auth_ok"""

cookieTemplate = """
cookie {name}_server insert indirect nocache"""

cookieCheckTemplate = " cookie {name}_server"

#########


def formatDefaultFrontendLine(name):
    return defaultFrontendLineTemplate.format(name=name)


def formatUseFrontendLine(name, host):
    return frontendLineTemplate.format(name=name, host=host)


def formatFrontendLine(site):
    if ("default" in site) and site["default"]:
        return formatDefaultFrontendLine(site["name"])
    else:
        return formatUseFrontendLine(site["name"], site["host"])


def formatFrontend(listenPort, sites):
    frontendLines = ''.join(map(formatFrontendLine, sites))
    return frontendTemplate.format(port=listenPort,
                                   frontend_lines=frontendLines)

#########


def formatAuthUser(login, password):
    return authUserTemplate.format(login=login, password=password)


def formatAuthUsers(users):
    userLines = ''.join([formatAuthUser(u['login'], u['pass']) for u in users])
    return authUsersTemplate.format(auth_group=authGroup, user_lines=userLines)

#########


def formatCookies(has_cookies, name):
    if has_cookies == False:
        return ""
    return cookieTemplate.format(name=name)


def formatCheckCookies(has_cookies, name):
    if has_cookies == False:
        return ""
    return cookieCheckTemplate.format(name=name)


def formatAuth(has_auth, realm):
    if has_auth == False:
        return ""
    return authTemplate.format(auth_group=authGroup, realm=realm)


def formatBackendLine(site):
    name = site["name"]
    remote = site.get("remote", "localhost")
    realm = site.get("realm", "MyServer")
    port = site["port"]

    hasAuth = site.get("auth", False)
    auth = formatAuth(hasAuth, realm)

    hasCookies = site.get("cookies", False)
    cookies = formatCookies(hasCookies, name)
    checkCookies = formatCheckCookies(hasCookies, name)

    return backendTemplate.format(name=name,
                                  remote=remote,
                                  port=port,
                                  auth=auth,
                                  cookies=cookies,
                                  check_cookies=checkCookies)


def formatBackend(sites):
    return ''.join(map(formatBackendLine, sites))

#########


def parseSettings(data):
    listenPort = 80
    if "settings" in data:
        settings = data["settings"]
        if "listen_port" in settings:
            listenPort = settings["listen_port"]
    return listenPort


def validate(data):
    if not "auth_users" in data:
        auth_count = len([s for s in data["sites"] if s.get("auth", False)])
        if auth_count > 0:
            print "Add auth user(s)"
            exit(1)


def formatAll(data):
    validate(data)
    listenPort = parseSettings(data)
    frontend = formatFrontend(listenPort, data["sites"])
    authUsers = ""
    if "auth_users" in data:
        authUsers = formatAuthUsers(data["auth_users"])
    backend = formatBackend(data["sites"])
    return ''.join([frontend, authUsers, backend]) + '\n'

with open(jsonFile) as dataFile:
    data = json.load(dataFile)
    with open(haproxyFile, 'w') as outputFile:
        outputFile.write(formatAll(data))
