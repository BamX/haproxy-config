#!/usr/bin/env python
import json

authGroup = "UsersForAuth"

jsonFile = "haproxy.json"
haproxyFile = "haproxy.cfg"

frontendTemplate = """frontend http_frontend
bind *:%s
mode http
option httpclose%s
"""

defaultFrontendLineTemplate = """
default_backend %s_web"""

frontendLineTemplate = """
acl is_%s hdr_end(host) -i %s
use_backend %s_web if is_%s"""

authUsersTemplate = """
userlist %s%s"""

authUserTemplate = """
user %s insecure-password %s"""

backendTemplate = """

backend %s_web
mode http%s%s
server %s_server %s:%s check%s"""

authTemplate = """
acl is_auth_ok http_auth(%s)
http-request auth realm %s if !is_auth_ok"""

cookieTemplate = """
cookie %s_server insert indirect nocache"""

#########

def formatDefaultFrontendLine(name):
    return defaultFrontendLineTemplate % name

def formatUseFrontendLine(name, host):
    return frontendLineTemplate % (name, host, name, name)

def formatFrontendLine(site):
    if ("default" in site) and site["default"]:
        return formatDefaultFrontendLine(site["name"])
    else:
        return formatUseFrontendLine(site["name"], site["host"])

def formatFrontend(listenPort, sites):
    return frontendTemplate % (listenPort, ''.join(map(formatFrontendLine, sites)))

#########

def formatAuthUser(login, password):
    return authUserTemplate % (login, password)

def formatAuthUsers(users):
    return authUsersTemplate % (authGroup, ''.join([formatAuthUser(user['login'], user['pass']) for user in users]))

#########

def formatCookies(name):
    return cookieTemplate % name

def formatAuth(realm):
    return authTemplate % (authGroup, realm)

def formatBackendLine(site):
    name = site["name"]
    remote = "localhost"
    if "remote" in site:
        remote = site["remote"]
    realm = "MyServer"
    if "realm" in site:
        realm = site["realm"]
    port = site["port"]
    cookies = (not "cookies" in site) or site["cookies"]
    auth = ("auth" in site) and site["auth"]
    return backendTemplate % (name, ("", formatAuth(realm))[auth], ("", formatCookies(name))[cookies], name, remote, port, ("", " cookie %s_server" % name)[cookies])

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

def formatAll(data):
    listenPort = parseSettings(data)
    frontend = formatFrontend(listenPort, data["sites"])
    authUsers = ""
    if "auth_users" in data:
        authUsers = formatAuthUsers(data["auth_users"])
    else:
        if len([site for site in data["sites"] if (("auth" in site) and site["auth"])]) > 0:
            print "Add user(s)"
            exit(1)
    backend = formatBackend(data["sites"])
    return ''.join([frontend, authUsers, backend]) + '\n'

with open(jsonFile) as dataFile:
    data = json.load(dataFile)
    with open(haproxyFile, 'w') as outputFile:
        outputFile.write(formatAll(data))
