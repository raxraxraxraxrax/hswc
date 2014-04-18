hswc
====

Homestuck Shipping World Cup server code

The HSWC is a for-fun-not-blood competition where a bunch of fans join teams for various Homestuck "ships" (that is, aggregations of webcomic characters considered in romantic relationships) and produce fanworks (art, fiction, movies, &c.) based on those ships and then vote on which are best. If you're here for code and not for fandom, yes, this is some hardcore nerd shit, and also it is awesome.

CURRENTLY IMPLEMENTED:

hswc-webserver.py and hswcutil.py handle signups for teams via a python webserver that can be proxied to through apache or, I guess, run directly on port 80 if you roll like that. The database that backs this is sqlite3 and the spec is in the comments of hswcutil.py. Currently missing from this code is:

 * how to handle signups closing
 * truly clean dreamwidth openid authentication handling

There are two more tasks we'd like this codebase to handle. The first is voting, where players go to vote on main round entries for the competition and their votes are authenticated and automatically tabulated. The second is trawling through dreamwidth comments on bonus rounds, where people write or draw quick things for small numbers of points (and fun!), which requires either wrangling the dreamwidth API or getting some serious HTML parser action going. These two may or may not be completed this year.

If you're interested in using this code for some other fandom event poke rax, they will totally help you figure out if it's worth using this code

If you want to use this for something unrelated there... is probably better code you can start from? But hey have at and I'm happy to explain all of the bad choices I made :)
