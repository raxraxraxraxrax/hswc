#!/usr/bin/python

import sqlite3, sys, re
#dbconn = sqlite3.connect('hswc.db')

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

#cursor = dbconn.cursor()

def team_exists(teamname, cursor):
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

def player_exists(player, cursor):
    """See if a player exists in the database or not. If yes, return 1,
       if not return 0."""
    array = (player,)
    cursor.execute('SELECT * from players where dwname=?', array)
    if cursor.fetchone():
        return 1
    else:
        return 0
    
def add_team(teamname, cursor):
    """Add a team to the database without information in it."""
    array = (teamname,)
    cursor.execute('INSERT into teams (name) values (?)', array)
    dbconn.commit()

def get_list_of_teams(cursor):
    """Get a list of all teams."""
    teamlist = []
    for team in cursor.execute('SELECT * from teams'):
        teamlist.append(team[0]) # man isn't it cool that order matters
    teamlist.sort()
    return teamlist

def get_teamcount(cursor):
    """Get a count of teams."""
    teamlist = get_list_of_teams(cursor)
    return len(teamlist)

def get_playercount(cursor):
    """Get a count of players."""
    playerlist = []
    for player in cursor.execute('SELECT * from players'):
	playerlist.append(player[0])
    return len(playerlist)

def make_friendleader(player, teamname, cursor):
    """Make player friendleader of teamname."""
    array = (player, teamname)
    cursor.execute('UPDATE teams set friendleader=? where name=?', array) 
    cursor.execute('UPDATE players set friendleader=? where dwname=?', ('yes', player))
    dbconn.commit()
    return

def add_player_to_players(player, email, notes, cursor):
    """Put the player in the player database at all.
       Team preference is not handled here."""
    array=(player, email, tumblr)
    cursor.execute('INSERT into players (dwname, email, notes) values (?,?,?)', array)
    dbconn.commit()
    return

def get_team_display_line(team, cursor):
    """Make the display line that goes into the teams table.
    Format is csstype, count, teamname, fl, stringofallplayers."""
    array=(team,)
    cursor.execute('SELECT * from teams where name=?', array)
    teamdatalist = cursor.fetchone()
    teamname = re.sub('<', '&lt;', teamdatalist[0])
    teamname = re.sub('>', '&gt;', teamname)
    if teamdatalist[2]:
	friendleader = teamdatalist[2]
    else: 
	friendleader = "None! You should sign up :D"
    count = 1 # teams shouldn't exist empty
    stringofallplayers = teamdatalist[3]
    for x in [4,5,6,7,8,9,10,11,12,13,14,15]:
        if teamdatalist[x]:
	    count = count + 1
            stringofallplayers = stringofallplayers + ', ' + teamdatalist[x]
    csstype = 'roster_teamslots'
    if count < 5:
	csstype = 'roster_teamslots_small'
    if count > 12:
	csstype = 'roster_teamslots_full'
    return (csstype, count, teamname, friendleader, stringofallplayers)


def add_player_to_team(player, teamname, flwilling, email, notes, cursor):
    """Adds a player to a team. If the team is full, errors out.
       If the player is already on the team, continue without changes.
       If the player is willing and there is no friendleader, FLify them.
       If the team has at least 5 members, make it active."""

    if not player_exists(player, cursor):
        add_player_to_players(player, email, notes, cursor)

    if not team_exists(teamname, cursor):
        add_team(teamname, cursor)

    if team_exists(teamname, cursor):  
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
                        make_friendleader(player, teamname, cursor) 
                dbconn.commit()
                print "success"
                return
            else:
                return "handle error because team is full" 
        else:
            if not friendleader:
                if flwilling:
                    make_friendleader(player, teamname)
		    return
    else:
        return "handle error because team doesn't exist after creating it"
    return "this error should never happen" 

def handle_incoming_player(datarow):
    """Get a full row of data from the hypothetical webform and do
       the needful."""

    # split the row into all of the relevant data

    # make sure they typed in the check correctly
    if checkstring != "whatever the checkstring is":
        print "checkstring is wrong"
        return 1

    # if the player does not exist, add them to the table
    if not player_exists(name):
        add_player_to_players(player,email,tumblr)
    
    # add them
    status = add_player_to_team(however,this, works)

    return status

def scrub_team(team):
    """Return a valid team name based on the user input.
       If there is no valid team name, return nothing."""

    string = team.lower()

    if string == '':
        return 0 
    elif re.search('<3<', string):
        namelist = string.split('<3<')
        shipsymbol = '<3<'
    elif re.search('<3', string):
        namelist = string.split('<3')
        shipsymbol = '<3'
    elif re.search('<>', string):
        namelist = string.split('<>')
        shipsymbol = '<>'
    elif re.search('c3<', string):
        namelist = string.split('c3<')
        shipsymbol = 'c3<'
    elif re.search('abstrata', string):
        return 'abstrata'
    elif re.search('noir', string):
        # jack noir won't show up, because there would be a ship symbol
        # unless you ship just... jack noir
        # no ship, just jack noir
        # in which case THE CODE CAN'T EVEN HANDLE YOU RIGHT NOW
        return 'noir'
    else:
	# then you have some kinda theme team or something whatever
        return string

    newlist = []
    newstring = ''

    for name in namelist:
        name = name.strip()
        newlist.append(name)

    newlist.sort()

    for x in range(0,(len(newlist) -1)):
        newstring = newstring + newlist[x] + shipsymbol

    newstring = newstring + newlist[(len(newlist) - 1)]

    return newstring

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
 
