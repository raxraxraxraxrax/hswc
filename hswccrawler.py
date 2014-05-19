#!/usr/bin/python

# THIS TOOL, LIKE, GETS COMMENTS FROM A COMMUNITY OR WHATEVER.
# THIS IS ADAPTED FROM:
# dwump.py -- Dreamwidth archiver
#     foxfirefey <skittisheclipse@gmail.com>
# Version 1.0
#
# This program is adapted from Greg Hewgill's ljdump.
#
# Simplest example:
#
#  python dwump.py -u USERNAME -p
#
# Help:
#
#  python dwump.py -h
#
# LICENSE
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the author be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
#
# Copyright (c) 2005-2006 Greg Hewgill


import codecs, glob, os, pickle, pprint, logging, re, sys, time, urllib, urllib2
import xml.dom.minidom, xmlrpclib, socket
from xml.sax import saxutils
from optparse import OptionParser
import hswcsecret

def getsession(flat_url, username, password):
    """This routine tries to log in the user and get an LJ session token.
    This token, sent as a cookie, allows you to have credentials for a 
    particular account while requesting comments from a different account;
    in this case that would be a community, which can't log in as itself.
    This code taken directly from dwump."""
    r = urllib2.urlopen(flat_url, "mode=getchallenge")
    response = flatresponse(r)
    r.close()
    r = urllib2.urlopen(flat_url,
        "mode=sessiongenerate&user=%s&auth_method=challenge&auth_challenge=%s&auth_response=%s" %
        (username, response['challenge'], calcchallenge(response['challenge'], password)))
    response = flatresponse(r)
    r.close()
    return response['ljsession']

def calcchallenge(challenge, password):
    """Hashes the password. Taken directly from dwump."""
    try:
        import hashlib
        return hashlib.md5(challenge+hashlib.md5(password).hexdigest()).hexdigest()
    except ImportError:
        import md5
        return md5.new(challenge+md5.new(password).hexdigest()).hexdigest()

def flatresponse(response):
    """Parses the response. No, I don't understand why name[-1] works
    either. Taken directly from dwump."""
    r = {}
    while True:
        name = response.readline()
        if len(name) == 0:
            break
        if name[-1] == '\n':
            name = name[:len(name)-1]
        value = response.readline()
        if value[-1] == '\n':
            value = value[:len(value)-1]
        r[name] = value
    return r

def test(session):
    r = urllib2.urlopen(urllib2.Request("http://www.dreamwidth.org/export_comments.bml?get=comment_body&startid=12400&authas=hs_worldcup",
	                headers = {'Cookie': "ljsession=%s" % session}))
    meta = xml.dom.minidom.parse(r)
    r.close()
    return meta


if __name__ == '__main__':
    username = 'worldcup_mods'
    commname = 'hs_worldcup'
    password = hswcsecret.send_password()

    session = getsession('http://dreamwidth.org/interface/flat', username, password)
    datamadness = test(session)
    for c in datamadness.getElementsByTagName('comment'):
	print c.getAttribute('posterid')
