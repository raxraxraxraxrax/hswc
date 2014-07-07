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

round = 75 #br2

def pretty_print_comment(comment, scoringfile):
    """pretty print a comment it's pretty fuckin' self-explanatory fef
       apparently eridan wrote this comment???"""
    poster = comment[7]
    team = comment[8]
    subject = comment[3]
    text = comment[4]

    # no interest in non-prompt non-fills
    if not (re.search("^prompt", subject.lower()) or re.search("^fill", subject.lower())):
        return

    # for br4+ needs to detect if comment is screened
    if comment[13]:
	return

    scoringfile.write("Poster: " + poster + "   Team: " + team + '\n')
    scoringfile.write("Subject: " + subject + '\n')
    encodedtext = text.encode('utf-8')
    scoringfile.write(encodedtext)
    scoringfile.write("\n --- \n")

    return
    

if __name__ == '__main__':
    scoringfile = open('alphadaveroseallbr2.txt', 'w')
    for team in ('alpha!dave<3alpha!rose', 'asdfjkl'):
#    for team in ('abstrata','alpha!dave<3alpha!rose','dave<3karkat','denizens', 'dualscar<3signless','equius<>nepeta','eridan<3<rose','eridan<3karkat','gamzee<>karkat','jade<3roxy','kanaya<3rose','palepitch'):
#    for team in ('psiioniic<3redglare', 'damarac3<horussc3<rufioh','cronus<3karkat','gamzee<3jane','feferi<3jade','jane<3roxy','terezi<3vriska','rose<>terezi', 'cronus<3kankri', 'cronus<3<kurloz','jade<3rose','eridan<3<sollux'):
	array = (round, team)
        blob = cursor.execute('SELECT * from comments where jitemid=? and team=?', array)	

        for x in cursor.fetchall():
	    pretty_print_comment(x, scoringfile)

    scoringfile.close()
