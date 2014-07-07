#!/usr/bin/python

# THIS TOOL, LIKE, GETS COMMENTS FROM A COMMUNITY OR WHATEVER.


import codecs, glob, os, pickle, pprint, logging, re, sys, time, urllib, urllib2
import xml.dom.minidom, xmlrpclib, socket
from xml.sax import saxutils
from optparse import OptionParser
import hswcsecret, hswcutil
import sqlite3
import dwump

dbconn = sqlite3.connect('hswc.db')
cursor = dbconn.cursor()

### maybe I should just import dwump and use this code from there?

#dwump.getsession(flat_url, username, password):
#    """This routine tries to log in the user and get an LJ session token.
#    This token, sent as a cookie, allows you to have credentials for a 
#    particular account while requesting comments from a different account;
#    in this case that would be a community, which can't log in as itself."""

#dwump.calcchallenge(challenge, password):
#    """Hashes the password. Taken directly from dwump."""

#dwump.flatresponse(response):
#    """Parses the response. No, I don't understand why name[-1] works
#    either. Taken directly from dwump."""

def get_round_from_jitemid(jitemid, cursor):
    """Take a jitemid, return a round."""

    round_jitemid_mapping = { (0, 'br negative one') }

    # if jitemid is a key in the dictionary:
        # return the value
  
    # otherwise just return "UNKNOWN ROUND"
 
    return round 

def get_dwname_from_posterid(posterid, cursor):
    """Take a posterid, get a dwname."""

    array = (posterid, )
    cursor.execute('SELECT * from dwids where dwid=?', array)
    result = cursor.fetchone()
    if not result:
        return "UNKNOWN POSTER"	
    
    dwname = result[1]

    return dwname

def add_to_db(id, jitemid, posterid, state, parentid, date, body, subject, cursor):
    """Add a comment into the db."""

    # DEFAULTS
    scoring = 0
    isprompt = 'no'
    isfill = 'no'
    needsreview = 'no'
        
    # turn jitemid into round
    # I think we're not doing this right away?
    # though maybe we should
    #round = get_round_from_jitemid(jitemid, cursor)

    # turn posterid into dwname
    dwname = get_dwname_from_posterid(posterid, cursor)
    
    # if there is no team it returns 0 which is fine 
    playerteam = hswcutil.get_current_team(dwname, cursor)

	
    if state == "D" or state =="S":
	# no one wants to score screened/deleted posts
	scoring = 0
	needsreview = 'no'
    else:
	state = ""

    # PROMPT: TEAM [YOUR SHIP]
    if re.search("^prompt: team", subject.lower()):
	team = (subject.lower()).split(" team ")[1]
	if playerteam == team:
	    isprompt = 'yes'
	    scoring = 1
	else:
	    isprompt = 'yes'
	    needsreview = 'yes'

    if re.search("^fill: team", subject.lower()):
	team = (subject.lower()).split(" team ")[1]
	if not parentid:
            needsreview = 'yes'
	else:
	    if playerteam == team:
		isfill = 'yes'
                # trust them on wordcount for now
		scoring = 1
	    else:
		isfill = 'yes'
		needsreview = 'yes'

    # right now we pass date through but in the future we might check for last-minute posts

    # enter it into the db yo
    array = (id, posterid, parentid, subject, body, date, dwname, playerteam, isprompt, isfill, needsreview, jitemid, scoring, state)
    print array
    cursor.execute('INSERT into comments (id, posterid, parentid, subject, body, date, dwname, team, isprompt, isfill, needsreview, jitemid, scoring, extra1) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', array)
    dbconn.commit()

    return

def set_comment_maxid(maxid, cursor):
    """Set the comment maxid for the current year."""

    # hardcoded right now
    year = 2014

    string = 'update commentmeta set maxid=%s where year=%s' % (maxid, year)
    cursor.execute(string)

    dbconn.commit()

    return

def get_comment_maxid(cursor): 
    """Get the comment maxid for the current year."""

    # hardcoded right now
    year = 2014

    cursor.execute("SELECT * FROM commentmeta where year=?", (year,))
    output = cursor.fetchone()

    return output[2]

def dwid_exists(dwid, cursor):
    """See if a dwid exists in the database or not. If yes, return 1,
       if not return 0."""
    array = (dwid,)
    cursor.execute('SELECT * from dwids where dwid=?', array)
    if cursor.fetchone():
        return 1
    else:
        return 0

def populate_dwids(meta, cursor):
    """Take some dwids and populate the players table."""

    # agh code
    for x in meta.getElementsByTagName('usermap'):
        dwid = int(x.getAttribute('id'))
        dwname = x.getAttribute('user')
	if hswcutil.player_exists(dwname, cursor):
            # then add the dwid to the player's line in the player table
            cursor.execute('UPDATE players set dwid=? where dwname=?', (dwid, dwname))
        # else they are probably from last year or dropped or something

        if dwid_exists(dwid, cursor):
            cursor.execute('UPDATE dwids set dwid=? where dwname=?', (dwid, dwname))
        else:
            cursor.execute('insert into dwids (dwid, dwname) values (?,?)',  (dwid, dwname))
        
        # I think we commit once per loop for locking reasons?
        dbconn.commit()  
             

    # actually I think that's it?

    return

def break_apart_object(outputobject):
    """Break apart an object and prepare it for entry into the database."""

    maxid = 0

    for x in outputobject.getElementsByTagName('comment'):
        id = int(x.getAttribute('id'))
	jitemid = int(x.getAttribute('jitemid'))
	posterid = int(x.getAttribute('posterid'))
	state = (x.getAttribute('state'))
	if x.getAttribute('parentid'):
	    parentid = int(x.getAttribute('parentid'))
	else:
            parentid = ''
        date = dwump.gettext(x.getElementsByTagName("date"))
	body = unicode(dwump.gettext(x.getElementsByTagName("body")))#.encode('utf-8')
	subject = unicode(dwump.gettext(x.getElementsByTagName("subject")))#.encode('utf-8')
	maxid = id
        add_to_db(id, jitemid, posterid, state, parentid, date, body, subject , cursor)
 
    return maxid

def get_comments(startnumber, session):
    """Gets 1000 comments starting from startnumber as a blob thing.
       Will need to be parsed."""
    urlstring = "http://www.dreamwidth.org/export_comments.bml?get=comment_body&startid=%s&authas=hs_worldcup" % startnumber
    r = urllib2.urlopen(urllib2.Request(urlstring,
                        headers = {'Cookie': "ljsession=%s" % session}))
    meta = xml.dom.minidom.parse(r)
    r.close()
    return meta

def get_current_start_point(cursor):
    """Get the current point to start getting comments from."""

    # should unhardcode at some point
    year = 2014

    array = (year, )
    cursor.execute('SELECT * from commentmeta where year=?', array)
    output = cursor.fetchone()

    return output[1]

def set_current_start_point(commentcount, cursor):
    """Set the most recent comment downloaded."""

    year = 2014

    cursor.execute('UPDATE commentmeta set current=? where year=?', (commentcount, year))
    
    return

def slurp_recurser(startpoint, maxid, session):
    """yeah"""

    commentblob = get_comments(startpoint, session)
    downloaded_maxid = break_apart_object(commentblob)

    if downloaded_maxid >= maxid:
        print "Hit maximum comments."
        set_current_start_point(downloaded_maxid, cursor)
        return

    slurp_recurser(startpoint+1000, maxid, session) 
 

def comment_slurper(session):
    """Slurps up comments from the last point to the current last post 
       as of the last metadata run."""

    current_start_point = get_current_start_point(cursor)
    maxid = get_comment_maxid(cursor)

    slurp_recurser(current_start_point, maxid, session)

    return
    
    # MAGIC MARKER

def execute_startup_metadata(startid, session):
    """Gets meta information. Meta can change, grab it all every run."""
    r = urllib2.urlopen(urllib2.Request("http://www.dreamwidth.org/export_comments.bml?get=comment_meta&startid=%s&authas=hs_worldcup" % startid, headers = {'Cookie': "ljsession=%s" % session}))
    meta = xml.dom.minidom.parse(r)
    r.close()

    maxmetaid_text = dwump.gettext(meta.getElementsByTagName("maxid"))

    maxmetaid = int(maxmetaid_text)
    set_comment_maxid(maxmetaid, cursor)
    populate_dwids(meta, cursor)
    if startid < maxmetaid:
        execute_startup_metadata((startid+10000), session)
    return
        

def test(session):
    r = urllib2.urlopen(urllib2.Request("http://www.dreamwidth.org/export_comments.bml?get=comment_body&startid=12400&authas=hs_worldcup",
	                headers = {'Cookie': "ljsession=%s" % session}))
    meta = xml.dom.minidom.parse(r)
    r.close()
    return meta


if __name__ == '__main__':
    username = 'worldcup_mods'
    commname = 'hs_worldcup'
    password = hswcsecret.send_password() # hahahah oops
                                          # I guess a config file would be maximally correct

    session = dwump.getsession('http://dreamwidth.org/interface/flat', username, password)

    comment_slurper(session)
    #datamadness = test(session)
    #execute_startup_metadata(10000, session)
    # the above command takes a while and should not necessarily be run every time
    #for c in datamadness.getElementsByTagName('comment'):
    #    id = int(c.getAttribute('id'))
#	string = dwump.gettext(c.getElementsByTagName("body"))
#	print unicode(string).encode('utf-8')
