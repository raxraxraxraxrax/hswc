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

teamsdict = {'blue':['abstrata','alpha!dave<3alpha!rose','dave<3karkat','denizens', 'dualscar<3signless','equius<>nepeta','eridan<3<rose','eridan<3karkat','gamzee<>karkat','jade<3roxy','kanaya<3rose','palepitch'], 'ceph':['psiioniic<3redglare', 'damarac3<horussc3<rufioh','cronus<3karkat','gamzee<3jane','feferi<3jade','jane<3roxy','terezi<3vriska','rose<>terezi', 'cronus<3kankri', 'cronus<3<kurloz','jade<3rose','eridan<3<sollux'], 'teaghan':['ancestors', 'dave<3jade<3john<3rose', 'dave<3jane', 'dave<3john', 'dave<3sollux', 'dirk<3jake<3jane<3roxy', 'equius<3gamzee', 'equius<3sollux', 'jake<3roxy', 'kanaya<3vriska', 'dirk<3jake<3jane<3roxy'], 'ketsu':['feferi<3nepeta', 'jake<>john', 'caliborn<3dirk', 'dirk<3john', 'dave<3terezi', 'robots', 'john<3karkat', 'dirk<3jake', 'eridan<3sollux'], 'maggie':['jake<3jane', 'feferi<3terezi', 'john<3roxy', 'gamzeec3<rosec3<terezi', 'jade<3karkat', 'john<3vriska', 'rose<3roxy', 'dave<3nepeta', 'eridan<3feferi<3sollux', 'dave<>karkat', 'gamzee<3tavros', 'john<3rose'], 'jay':['latula<3mituna', 'kismesissitude', 'dirk<3jane', 'calliope<3roxy', 'john<3<tavros', 'karkat<3sollux', 'guardians', 'bro<3john', 'karkat<3terezi', 'aradia<3sollux', 'hella jeff<3sweet bro'], 'soni':['calliope<3jade', 'tricksters', 'dave<3<karkat', 'jake<3karkat', 'dualscar<3psiioniic', 'eridan<>feferi', 'bro<3dave', 'alpha!dave<3dirk', 'eridan<3roxy', 'dave<3jade', 'kanaya<>karkat']}

# man this should be coded better at some point
round = 86 
roundname = 'br5'

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


    # for br4+ needs to detect if comment is screened and if so not print it
    if comment[11] == "screened":
	return

    scoringfile.write("Poster: " + poster + "   Team: " + team + '\n')
    scoringfile.write("Subject: " + subject.encode('utf-8') + '\n')
    encodedtext = text.encode('utf-8')
    scoringfile.write(encodedtext)
    scoringfile.write("\n --- \n")

    return
  
def generate_all_scores_for_round():
    """generate all the scores for a round
       basically, this is what the script did before, except coded in a 
       semi-reasonable way!"""
    for mod in teamsdict.keys():
	scoringfilename = mod + roundname + '.txt'
        scoringfile = open(scoringfilename, 'w')
        for team in teamsdict[mod]:
	    array = (round, team)
	    blob = cursor.execute('SELECT * from comments where jitemid=? and team=?', array)

	    for x in cursor.fetchall():
		pretty_print_comment(x, scoringfile)

        scoringfile.close()

if __name__ == '__main__':
    print "generating all scores for round " + roundname
    generate_all_scores_for_round()
    print "done, hopefully"
