#!/usr/bin/env python
import json

defaultRealm = "Welcome"

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
userlist {auth_group}_group{user_lines}"""

authUserTemplate = """
user {login} insecure-password {password}"""

backendTemplate = """

backend {name}_web
mode http{auth}{cookies}
server {name}_server {remote}:{port} check{check_cookies}"""

authTemplate = """
acl is_auth_ok http_auth({auth_group}_group)
http-request auth realm {realm} if !is_auth_ok"""

cookieTemplate = """
cookie {name}_server insert indirect nocache"""

cookieCheckTemplate = " cookie {name}_server"

#########


def formatDefaultFrontendLine(site):
    return defaultFrontendLineTemplate.format(name=site['name'])


def formatUseFrontendLine(site):
    return frontendLineTemplate.format(name=site['name'],
                                       host=site['host'])


def formatFrontendLine(site):
    if site.get("default", False):
        return formatDefaultFrontendLine(site)
    else:
        return formatUseFrontendLine(site)


def formatFrontend(listenPort, sites):
    frontendLines = ''.join(map(formatFrontendLine, sites))
    return frontendTemplate.format(port=listenPort,
                                   frontend_lines=frontendLines)

#########


def formatAuthUser(user):
    return authUserTemplate.format(login=user['login'],
                                   password=user['pass'])


def formatAuthGroup(group):
    userLines = ''.join(map(formatAuthUser, group['users']))
    return authUsersTemplate.format(auth_group=group['name'],
                                    user_lines=userLines)


def formatAuthGroups(groups):
    if not groups or len(groups) == 0:
        return ""
    return '\n'.join(map(formatAuthGroup, groups))

#########


def formatCookies(site):
    if site.get("cookies", False) == False:
        return ""
    return cookieTemplate.format(name=site['name'])


def formatCheckCookies(site):
    if site.get("cookies", False) == False:
        return ""
    return cookieCheckTemplate.format(name=site['name'])


def formatAuth(site):
    if site.get("auth_group", False) == False:
        return ""
    return authTemplate.format(auth_group=site['auth_group'],
                               realm=site.get('realm', defaultRealm))


def formatBackendLine(site):
    name = site["name"]
    remote = site.get("remote", "localhost")
    realm = site.get("realm", "MyServer")
    port = site["port"]
    return backendTemplate.format(name=name,
                                  remote=remote,
                                  port=port,
                                  auth=formatAuth(site),
                                  cookies=formatCookies(site),
                                  check_cookies=formatCheckCookies(site))


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
    if not "auth_groups" in data:
        for site in data["sites"]:
            if site.get("auth_group", False):
                print "Add auth user(s)"
                exit(1)


def formatAll(data):
    validate(data)
    listenPort = parseSettings(data)
    frontend = formatFrontend(listenPort, data["sites"])
    auth = formatAuthGroups(data["auth_groups"])
    backend = formatBackend(data["sites"])
    return ''.join([frontend, auth, backend]) + '\n'

with open(jsonFile) as dataFile:
    data = json.load(dataFile)
    with open(haproxyFile, 'w') as outputFile:
        outputFile.write(formatAll(data))
