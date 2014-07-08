hswc
====

Homestuck Shipping World Cup server code

The HSWC is a for-fun-not-blood competition where a bunch of fans join teams for various Homestuck "ships" (that is, aggregations of webcomic characters considered in romantic relationships) and produce fanworks (art, fiction, movies, &c.) based on those ships and then vote on which are best. If you're here for code and not for fandom, yes, this is some hardcore nerd shit, and also it is awesome.

CURRENTLY IMPLEMENTED:

hswc-webserver.py handles signups for teams via a python webserver that can be proxied to through apache or, I guess, run directly on port 80 if you roll like that. The database that backs this is sqlite3 and the spec is in the comments of hswcutil.py. Currently missing from this code is:

 * truly clean dreamwidth openid authentication handling

Most of the utility functions for talking to the database are in hswcutil.py. Pretty much everything in the project imports hswcutil. hswcutil is friend, and can't be run standalone at this point (although if you wanted to you would just have to uncomment a bunch of dbconn.commit() type lines).

Half of the event is based on people posting many thousands of Dreamwidth comments that we then have to crawl and parse to see who has scored how many points for what. In the past, the mod team has manually read every comment and decided what was scoreworthy. hswccrawler.py populates a comment database with some tentative scoring suggestions that will hopefully save a lot of time. The current way to hackishly get output from that db is hswc-score-tool.py which is a belunkus script that needs to be replaced.

TO DO:

The other half involves voting on main round entries, currently on DW. There's no automation for this right now. Next year we'd like to collect votes automatically on a hosted webapp that minimizes the need for mod intervention at all. We are not there yet.

We'd also like some kind of mod web interface for looking up email, moving members between teams, getting scoring information out of the comments db, that kind of thing. Right now the solution to those things is "poke rax" which ... doesn't scale. My ideal is to have the system run without my intervention, but that's a little bit of a pipe dream probably. 

If you're interested in using this code for some other fandom event poke rax, they will totally help you figure out if it's worth using this code.

If you want to use this for something unrelated there... is probably better code you can start from? But hey have at and I'm happy to explain all of the bad choices I made :)
