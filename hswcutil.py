#!/usr/bin/python

import sqlite3, sys, re
#dbconn = sqlite3.connect('hswc.db')

## Assumptions about the database are currently:

# sqlite> .schema
# CREATE TABLE pending(dwname TEXT, email TEXT, team TEXT, friendleader TEXT, notes TEXT, extrafield TEXT);
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

def make_pending_entry(dwname, email, team, friendleader, notes, cursor):
    """Make a pending entry to be processed if the DW auth goes through."""
    array = (dwname, email, team, friendleader, notes)
    cursor.execute('INSERT into pending (dwname, email, team, friendleader, notes) values (?,?,?,?,?)', array)
    return

def retrieve_pending_entry(dwname, cursor):
    """Get a pending entry out for a username."""
    array = (dwname,)
    cursor.execute('SELECT * from pending where dwname=?', array)
    pending_entry = cursor.fetchone()
    return pending_entry

def remove_pending_entry(dwname, cursor):
    """Remove a pending entry for a username."""
    array = (dwname,)
    cursor.execute('DELETE from pending where dwname=?', array)
    #dbconn.commit()
    return

def team_exists(teamname, cursor):
    """See if a team exists in the database or not. If yes, return 1,
      if not return 0."""
    array = (teamname,) # for sanitizing
    if teamname == 'noir':
	return 1
    cursor.execute('SELECT * from teams where name=?', array)
    if cursor.fetchone():
        return 1 
    else:
        return 0 

def team_has_friendleader(teamname, cursor):
    """If a team has a friendleader, return 0, otherwise return 1"""
    array = (teamname,)
    if not team_exists(teamname, cursor):
	# there's not a friendleader if there's no team!
	return 0
    cursor.execute('SELECT * from teams where name=?', array)
    teamlist = cursor.fetchone()
    if teamlist[2]:
	return 1
    else:
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

def get_current_team(player, cursor):
    """Get the team the player is currently on, if there is one."""
    array = (player,)
    cursor.execute('SELECT * from players where dwname=?', array)
    currentteam = cursor.fetchone()
    if currentteam:
	return currentteam[3]
    else:
	cursor.execute('SELECT * from noir where dwname=?', array)
	noirstatus = cursor.fetchone()
	if noirstatus:
	    return 'noir'
	return 0
    
def add_team(teamname, cursor):
    """Add a team to the database without information in it."""
    array = (teamname,)
    cursor.execute('INSERT into teams (name) values (?)', array)
    #dbconn.commit()
    return

def remove_team(teamname, cursor):
    """Delete a team."""
    array = (teamname,)
    if teamname == 'noir':
	# don't delete noir
	return
    cursor.execute('DELETE from teams where name=?', array)
    #dbconn.commit()
    return

def remove_player(player, cursor):
    """Delete a player."""
    array = (player,)
    cursor.execute('DELETE from players where dwname=?', array)
    #dbconn.commit()
    return

def get_list_of_teams(cursor):
    """Get a list of all teams."""
    teamlist = []
    for team in cursor.execute('SELECT * from teams'):
        teamlist.append(team[0]) # man isn't it cool that order matters
    teamlist.append('noir')
    # soni doesn't like it alphabetical
    # teamlist.sort()
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

def get_friendleader(team, cursor):
    """Get the friendleader of a team, if one exists."""
    array = (team, )
    if not team_exists(team, cursor):
	return 0
    if team == 'noir':
	return 'worldcup-mods'
    cursor.execute('SELECT * from teams where name=?', array)
    teamrow = cursor.fetchone()
    return teamrow[2]

def make_friendleader(player, teamname, cursor):
    """Make player friendleader of teamname."""
    array = (player, teamname)
    cursor.execute('UPDATE teams set friendleader=? where name=?', array) 
    #cursor.execute('UPDATE players set friendleader=? where dwname=?', ('yes', player))
    #dbconn.commit()
    return

def remove_player_from_noir(player, cursor):
    """Remove a player from noir."""
    array = (player,)
    cursor.execute('DELETE from noir where dwname=?', array)
    #dbconn.commit()
    return

def add_player_to_noir(player, cursor):
    """Add a player to noir."""
    array = (player,)
    cursor.execute('INSERT into noir (dwname) values (?)', array)
    return

def remove_player_from_team(player, teamname, cursor):
    """Remove a player from a team, presumably because they joined another."""
    array = (teamname,)
    if teamname == 'noir':
	remove_player_from_noir(player, cursor)
	return
    cursor.execute('SELECT * from teams where name=?', array)
    teamdatalist = cursor.fetchone()
    if teamdatalist[2] == player:
	friendleader = ''
    else:
	friendleader = teamdatalist[2]
    newteamlist = []
    for x in xrange(3,16):
        if teamdatalist[x] != player:
	    if teamdatalist[x]:
                newteamlist.append(teamdatalist[x])
    if newteamlist == []:
	remove_team(teamname, cursor)
	return
    if len(newteamlist) < 13:
	for i in xrange(13 - len(newteamlist)):
            newteamlist.append('')
    arglist = [friendleader] + newteamlist + [teamname]
    array = tuple(arglist)
    cursor.execute('UPDATE teams set friendleader=?, member1=?, member2=?, member3=?, member4=?, member5=?, member6=?, member7=?, member8=?, member9=?, member10=?, member11=?, member12=?, member13=? where name=?', array)
    #dbconn.commit()
    return

def update_player(player, email, notes, teamname, cursor):
    """Update the player's information in the db after a new form submission."""
    array=(email, notes, teamname, player)
    cursor.execute('UPDATE players set email=?, notes=?, team=? where dwname=?', array)
    #dbconn.commit()
    return

def add_player_to_players(player, email, notes, cursor):
    """Put the player in the player database at all.
       Team preference is not handled here."""
    array=(player, email, notes)
    cursor.execute('INSERT into players (dwname, email, notes) values (?,?,?)', array)
    #dbconn.commit()
    return

def get_team_members_count(team, cursor):
    """How many players on the team?"""
    array=(team,)
    if not team_exists(team, cursor):
	return 0
    if team == 'noir':
	return get_noir_members_count(cursor)
    cursor.execute('SELECT * from teams where name=?',array)
    teamdatalist = cursor.fetchone()
    count = 0
    for x in xrange(3,16):
	if teamdatalist[x]:
	    count = count + 1
    return count

def get_noir_members_count(cursor):
    """How many players on team noir?"""
    cursor.execute('SELECT * from noir')
    noirlist = cursor.fetchall()
    return len(noirlist)

def get_noir_members_list(cursor):
    """Which players are on team noir?"""
    cursor.execute('SELECT * from noir')
    noirlist = cursor.fetchall()
    if not noirlist:
	return ['nobody']
    noirplayers = []
    for x in noirlist:
	noirplayers.append(x[0])
    noirplayers.sort()
    return noirplayers

def player_is_on_team(player, team, cursor):
    """Is the player on the team?"""
    array=(team,)
    if team == 'noir':
        noir_members = get_noir_members_list(cursor)
	for x in noir_members:
	    if player == x:
		return 1
	return 0
    if not team_exists(team, cursor):
	return 0
    cursor.execute('SELECT * from teams where name=?',array)
    teamdatalist = cursor.fetchone()
    for x in xrange(3,16):
	if player == teamdatalist[x]:
	    return 1
    return 0

def get_team_display_line(team, cursor):
    """Make the display line that goes into the teams table.
    Format is csstype, count, teamname, fl, stringofallplayers."""
    array=(team,)
    teamname = re.sub('<', '&lt;', team)
    teamname = re.sub('>', '&gt;', teamname)
    if teamname == 'noir':
	stringofallplayers = 'Please see the noir page at <a href="http://autumnfox.akrasiac.org/hswc/noir">this link</a>.'
	csstype= 'roster_teamslots'
	count = get_noir_members_count(cursor)
	friendleader = 'worldcup-mods'
	return (csstype, count, teamname, friendleader, stringofallplayers)
    cursor.execute('SELECT * from teams where name=?', array)
    teamdatalist = cursor.fetchone()
    teamname = re.sub('<', '&lt;', teamdatalist[0])
    teamname = re.sub('>', '&gt;', teamname)
    if teamdatalist[2]:
	friendleader = teamdatalist[2]
    else: 
	friendleader = "None! You should sign up :3"
    count = 1 # teams shouldn't exist empty
    stringofallplayers = teamdatalist[3]
    for x in xrange(4,16): # yes 4 that's on purpose
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

    if teamname == 'noir':
	add_player_to_noir(player, cursor)
	cursor.execute('UPDATE players set team=? where dwname=?', ('noir', player))
	return

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

        for x in xrange(3,16): # 0 is name, 1 is active, 2 is FL
            if teamdatalist[x]:
                if teamdatalist[x] == player:
                    # you're already on that team you dingus
                    alreadyonteam = 1
		    break
                else:
                    # someone else has this slot
                    continue
            else:
                # this is your slot now
                teamindex = x
                break

        # in theory being already on the team should have been caught earlier
	# but this will double-catch it just in case because not doing so is bad
	# also it is already written
        if not alreadyonteam:
            if teamindex:
                # because if it's zero, the team is full         
                strteamindex = 'member' + str(teamindex - 2)

                # python the fact that I have to do the below makes me sad
                string = 'UPDATE teams set %s=? where name=?' % strteamindex
                cursor.execute(string, (player, teamname))
		cursor.execute('UPDATE players set team=? where dwname=?', (teamname, player))
                if not friendleader:
                    if flwilling:
                        make_friendleader(player, teamname, cursor) 
                #dbconn.commit()
                return
            else:
		if teamname == 'abstrata':
		    # abstrata is full, go to next abstrata
		    status = add_player_to_team(player, 'abstrata2', flwilling, email, notes, cursor)
		    return status
	        elif teamname == 'abstrata2':
		    status = add_player_to_team(player, 'abstrata3', flwilling, email, notes, cursor)
		    return status
	        elif teamname == 'abstrata3':
		    status = add_player_to_team(player, 'abstrata4', flwilling, email, notes, cursor)
		    return status
	        elif teamname == 'abstrata4':
	            status = add_player_to_team(player, 'abstrata5', flwilling, email, notes, cursor)
		    return status
	        elif teamname == 'abstrata5':
		    return "Rax didn't make enough abstrata teams, tell them they were wrong"
                return "Sorry, that team filled up due to a race condition."
        else:
            if not friendleader:
                if flwilling:
                    make_friendleader(player, teamname)
		    return
	        else:
	            return
	    else:
	        if not flwilling:
                    make_friendleader('', teamname)
		return
    else:
        return "Team doesn't exist after creating it, contact rax."
    return "This error should never happen! Contact rax." 

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
    elif re.search('o8<', string):
	namelist = string.split('o8<')
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
 
