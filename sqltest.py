#!/usr/bin/python

import sqlite3, sys
dbconn = sqlite3.connect('hswc.db')

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
    dbconn.commit()
    return

    
def add_player_to_team(player, teamname, flwilling):
    """Adds a player to a team. If the team is full, errors out.
       If the player is already on the team, continue without changes.
       If the player is willing and there is no friendleader, FLify them.
       If the team has at least 5 members, make it active."""
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
   
    add_player_to_team('rax','rax<3<computers',0)
