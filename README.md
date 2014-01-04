hswc
====

Homestuck Shipping World Cup server code

if you aren't on the HSWC mod team and are reading this, um, you're probably too early there is nothing here yet sorry

TODO: everything

brief description of goals:

there are three major tasks
the first one is letting people sign up and assign themselves to teams
which mostly needs openid integration, ability to write to a database, and ability to make an html page with a
huge spreadsheet/table based on that database, ideally with a bunch of links/buttons on it
this doesn't seem that hard although it may be somewhat grindy
the second task is making a page that lets people vote for their favorite fanwork; based on their openID they
get a different list, and they can only vote once, and all the votes have to be tabulated and then the results also get
spit out as a big html table woooo
the third task involves crawling a bunch of dreamwidth pages to see who has posted what where, and generate
scoring based on some as yet unspecified algorithm and that data
there may be a useful API for this or it may just be taking apart HTML, which is misery but not actually that
 _hard_
(at least in my experience)

this will all be hosted on a Debian box through apache2

it looks like there's an OpenID apache module I've worked with before so I'm going to start with that
my limited experience is with python and mako for html templating so unless someone prefers something else we might
as well use that?

woo
