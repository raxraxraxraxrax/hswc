#!/usr/bin/python

import sqlite3, sys
dbconn = sqlite3.connect('hswc.db')

## Assumptions about the database are currently:

# sqlite> .schema
# CREATE TABLE players(dwname TEXT, email TEXT, tumblr TEXT, team TEXT, friendleader TEXT, flwilling TEXT, notes TEXT, extrafield TEXT);
# CREATE TABLE teams(name TEXT, active TEXT, friendleader TEXT, member1 TEXT, member2 TEXT, member3 TEXT, member4 TEXT, member5 TEXT, member6 TEXT, member7 TEXT, member8 TEXT, member9 TEXT, member10 TEXT, member11 TEXT, member12 TEXT, member13 TEXT, totalscore INT, round1 INT, round2 INT, collab INT, bonus0 INT, bonus1 INT, bonus2 INT, bonus3 INT, bonus4 INT, bonus5 INT, bonus6 INT, bonus7 INT, extrafield TEXT);

## this is minorly belunkus but it's a starting point at least
## in particular the players table doesn't need 'flwilling'
## and having it be dwname and name in different tables is _kind_ of
## stupid although also a reminder of which table you're working with

## extrafield is there in case I forgot something and need to insert it 
## in the middle of the event, which is probably the sort of thing you 
## only do when you are writing hackity nonsense for shipping competitions, 
## but that's what I'm doing so here we are

cursor = dbconn.cursor()

def team_exists(teamname):
    """See if a team exists in the database or not. If yes, return 1,
      if not return 0."""
    array = (teamname,) # for sanitizing
    cursor.execute('SELECT * from teams where name=?', array)
    if cursor.fetchone():
        print 'exists'
        return 1 
    else:
        print 'does not exist'
        return 0 

def player_exists(player):
    """See if a player exists in the database or not. If yes, return 1,
       if not return 0."""
    array = (player,)
    cursor.execute('SELECT * from players where dwname=?', array)
    if cursor.fetchone():
        return 1
    else:
        return 0
    
def add_team(teamname):
    """Add a team to the database without information in it."""
    array = (teamname,)
    cursor.execute('INSERT into teams (name) values (?)', array)
    dbconn.commit()

def get_list_of_teams():
    """Get a list of all teams."""
    teamlist = []
    for team in cursor.execute('SELECT * from teams'):
        teamlist.append(team[0]) # man isn't it cool that order matters
    return teamlist

def make_friendleader(player, teamname):
    """Make player friendleader of teamname."""
    array = (player, teamname)
    cursor.execute('UPDATE teams set friendleader=? where name=?', array) 
    cursor.execute('UPDATE players set friendleader=? where dwname=?', ('yes', player))
    dbconn.commit()
    return

def add_player_to_players(player,email,tumblr):
    """Put the player in the player database at all.
       Team preference is not handled here."""
    array=(player, email, tumblr)
    cursor.execute('INSERT into players (dwname, email, tumblr) values (?,?,?)', array)
    dbconn.commit()
    return
    
def add_player_to_team(player, teamname, flwilling, email, tumblr):
    """Adds a player to a team. If the team is full, errors out.
       If the player is already on the team, continue without changes.
       If the player is willing and there is no friendleader, FLify them.
       If the team has at least 5 members, make it active."""

    if not player_exists(player):
        add_player_to_players(player, email, tumblr)

    if team_exists(teamname):  
        array = (teamname,)
        cursor.execute('SELECT * from teams where name=?', array)
        teamdatalist = cursor.fetchone()
        alreadyonteam = 0 
        teamindex = 0
        friendleader = teamdatalist[2]

        # it's gnarly finite state machine time, kids!
        # that's how you know i'm a shitty programmer <3

        for x in [3,4,5,6,7,8,9,10,11,12,13,14,15]: # 0 is name, 1 is active, 2 is FL
            if teamdatalist[x]:
                if teamdatalist[x] == player:
                    # you're already on that team you dingus
                    alreadyonteam = 1
                else:
                    # someone else has this slot
                    continue
            else:
                # this is your slot now
                teamindex = x
                break

        # maybe "is team full" should be its own function?

        if not alreadyonteam:
            if teamindex:
                # because if it's zero, the team is full         
                strteamindex = 'member' + str(teamindex - 2)

                # python the fact that I have to do the below makes me sad
                string = 'UPDATE teams set %s=? where name=?' % strteamindex
                cursor.execute(string, (player, teamname))
                if not friendleader:
                    if flwilling:
                        make_friendleader(player, teamname) 
                dbconn.commit()
                print "success"
                return
            else:
                print "handle error because team is full" 
                return
        else:
            print "I guess pass since you are already on the team?"
            if not friendleader:
                if flwilling:
                    make_friendleader(player, teamname)
    else:
        print "handle error because team doesn't exist"
    return


if __name__ == "__main__":
    teamnames = ('rax<3<computers', 'modship<3players', 'h8rs<>h8rs')
    playernames = ('alice', 'bob', 'carol', 'dave', 'elsa', 'fiddlesticks')

    # add teams if they don't exist
    for team in teamnames:
        if team_exists(team):
            print "hooray"
        else:
            add_team(team)

    # print a list of all teams
    teamlist = get_list_of_teams()
    print teamlist 
   
    add_player_to_team('rax','rax<3<computers',0,'rax@akrasiac.org','')
    for player in playernames:
        add_player_to_team(player, 'rax<3<computers',0,'test@example.com','')
 
