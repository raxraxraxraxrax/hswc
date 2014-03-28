#!/usr/bin/env python
"""
Cribbed off of python-openid's Simple example for an OpenID consumer.

The HSWC signup page for 2014.
"""

from Cookie import SimpleCookie
import cgi
import urlparse
import cgitb
import sys, re
import hswcutil as hswc

#dbstuff
import sqlite3, sys
dbconn = sqlite3.connect('hswc.db')
cursor = dbconn.cursor()

def quoteattr(s):
    qs = cgi.escape(s, 1)
    return '"%s"' % (qs,)

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

try:
    import openid
except ImportError:
    sys.stderr.write("""
Failed to import the OpenID library. In order to use this example, you
must either install the library (see INSTALL in the root of the
distribution) or else add the library to python's import path (the
PYTHONPATH environment variable).

For more information, see the README in the root of the library
distribution.""")
    sys.exit(1)

from openid.store import memstore
from openid.store import filestore
from openid.consumer import consumer
from openid.oidutil import appendArgs
from openid.cryptutil import randomString
from openid.fetchers import setDefaultFetcher, Urllib2Fetcher
from openid.extensions import pape, sreg



class OpenIDHTTPServer(HTTPServer):
    """http server that contains a reference to an OpenID consumer and
knows its base URL. The base URL is hardcoded here because that's how
it's set up in Apache2.
"""
    def __init__(self, store, *args, **kwargs):
        HTTPServer.__init__(self, *args, **kwargs)
        self.sessions = {}
        self.store = store

        if self.server_port != 80:
#            self.base_url = ('http://%s:%s/' %
#                             (self.server_name, self.server_port))
             self.base_url = 'http://autumnfox.akrasiac.org/hswctest'
        else:
            self.base_url = 'http://%s/' % (self.server_name,)

class OpenIDRequestHandler(BaseHTTPRequestHandler):
    """Request handler that knows how to verify an OpenID identity."""
    SESSION_COOKIE_NAME = 'hswcpage'

    session = None

    def getConsumer(self, stateless=False):
        if stateless:
            store = None
        else:
            store = self.server.store
        return consumer.Consumer(self.getSession(), store)

    def getSession(self):
        """Return the existing session or a new session"""
        if self.session is not None:
            return self.session

        # Get value of cookie header that was sent
        cookie_str = self.headers.get('Cookie')
        if cookie_str:
            cookie_obj = SimpleCookie(cookie_str)
            sid_morsel = cookie_obj.get(self.SESSION_COOKIE_NAME, None)
            if sid_morsel is not None:
                sid = sid_morsel.value
            else:
                sid = None
        else:
            sid = None

        # If a session id was not set, create a new one
        if sid is None:
            sid = randomString(16, '0123456789abcdef')
            session = None
        else:
            session = self.server.sessions.get(sid)

        # If no session exists for this session ID, create one
        if session is None:
            session = self.server.sessions[sid] = {}

        session['id'] = sid
        self.session = session
        return session

    def setSessionCookie(self):
        sid = self.getSession()['id']
        session_cookie = '%s=%s;' % (self.SESSION_COOKIE_NAME, sid)
        self.send_header('Set-Cookie', session_cookie)

    def do_GET(self):
        """Dispatching logic. There are multiple paths defined:

/ - Display an empty form asking for a signup
/verify - Handle form submission, initiating OpenID verification
/process - Handle a redirect from an OpenID server
/teams - display the teams as currently extant

Any other path gets a 404 response. This function also parses
the query parameters.

If an exception occurs in this function, a traceback is
written to the requesting browser.
"""
        try:
            self.parsed_uri = urlparse.urlparse(self.path)
            self.query = {}
            for k, v in cgi.parse_qsl(self.parsed_uri[4]):
                self.query[k] = v.decode('utf-8')

            path = self.parsed_uri[2]
            if path == '':
                path = '/' + self.parsed_uri[1] 
            if path == '/':
                self.render()
            elif path == '/verify':
                self.doVerify()
            elif path == '/process':
                self.doProcess()
	    elif path == '/teams':
		self.doTeams()
            else:
                self.notFound()

        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.setSessionCookie()
            self.end_headers()
            self.wfile.write(cgitb.html(sys.exc_info(), context=10))

    def doTeams(self):
	"""Show the page with all of the teams on it. Right now, empty."""


    def doVerify(self):
        """Process the form submission, initating OpenID verification.
"""

        # First, collect all the data.
        openid_url = self.query.get('username')
	email = self.query.get('email')
	team = self.query.get('team')
	if self.query.get('FL') == 'yes':
            flwilling = 1
	else:
	    # if they didn't check anything we assume they do not want to
	    # be a friendleader. that seems best here.
            flwilling = 0
	contentnotes = self.query.get('content-tags')

	# You have to get the rules check right.
	if self.query.get('rules-check') != 'I certify that I have read and will abide by the Rules and Regulations of the 2014 HSWC.':
	   self.render('Please enter the correct rules check text.', css_class='error',
		       form_contents=(openid_url,email,team,contentnotes))
	   return

        # There has to be a team name.
	if not team:
            self.render('Please enter a team name.', css_class='error',
			form_contents=(openid_url,email,team,contentnotes))
	team = hswc.scrub_team(team)
	if not team:
	    self.render('Please enter a valid team name.', css_class='error',
			form_contents=(openid_url,email,team,contentnotes))
	    return

	# There also has to be an email address!
	if not email:
            self.render('Please enter an email address.', css_class='error',
			form_contents=(openid_url,email,team,contentnotes))
	    return
	if not re.match(r'[^@]+@[^@]+\.[^@]+',email):
            self.render('Please enter a valid email address.', css_class='error',
			form_contents=(openid_url,email,team,contentnotes))
	    return

	# There has to be a username.
        if not openid_url:
            self.render('Enter a DreamWidth username.',
                        css_class='error', form_contents=(openid_url,email,team,contentnotes))
            return 

        # Now add the DW part of the string --- we don't want other OpenID
	# providers because they are cubeless and shall surely be put to
	# death.
        openid_url = openid_url + '.dreamwidth.org'

        # we're not using these parts of the example but I did not strip them
	# out on the theory that we might end up needing them for some reason
        #immediate = 'immediate' in self.query
        #use_sreg = 'use_sreg' in self.query
        #use_pape = 'use_pape' in self.query
        #use_stateless = 'use_stateless' in self.query
	immediate = 0
	use_sreg = 0
	use_pape = 0
	use_stateless = 0

        oidconsumer = self.getConsumer(stateless = use_stateless)
        try:
            request = oidconsumer.begin(openid_url)
        except consumer.DiscoveryFailure, exc:
            fetch_error_string = 'Error in discovery: %s' % (
                cgi.escape(str(exc[0])))
            self.render(fetch_error_string,
                        css_class='error',
                        form_contents=openid_url)
        else:
            if request is None:
                msg = 'No OpenID services found for <code>%s</code>' % (
                    cgi.escape(openid_url),)
                self.render(msg, css_class='error', form_contents=openid_url)
            else:
                # Then, ask the library to begin the authorization.
                # Here we find out the identity server that will verify the
                # user's identity, and get a token that allows us to
                # communicate securely with the identity server.
                if use_sreg:
                    self.requestRegistrationData(request)

                if use_pape:
                    self.requestPAPEDetails(request)

                trust_root = self.server.base_url
                print 'trust_root is ' + trust_root
                return_to = self.buildURL('process')
                print 'return_to is ' + return_to
                if request.shouldSendRedirect():
                    redirect_url = request.redirectURL(
                        trust_root, return_to, immediate=immediate)
                    self.send_response(302)
                    self.send_header('Location', redirect_url)
                    self.writeUserHeader()
                    self.end_headers()
                else:
                    form_html = request.htmlMarkup(
                        trust_root, return_to,
                        form_tag_attrs={'id':'openid_message'},
                        immediate=immediate)

                    self.wfile.write(form_html)

    def requestRegistrationData(self, request):
        sreg_request = sreg.SRegRequest(
            required=['nickname'], optional=['fullname', 'email'])
        request.addExtension(sreg_request)

    def requestPAPEDetails(self, request):
        pape_request = pape.Request([pape.AUTH_PHISHING_RESISTANT])
        request.addExtension(pape_request)

    def doProcess(self):
        """Handle the redirect from the OpenID server.
"""
        oidconsumer = self.getConsumer()

        # Ask the library to check the response that the server sent
        # us. Status is a code indicating the response type. info is
        # either None or a string containing more information about
        # the return type.
#        url = 'http://'+self.headers.get('Host')+self.path
	# rax: hardcoding this for maximum bullshit
        # this makes me not just a bad programmer but a bad person
        url = 'http://autumnfox.akrasiac.org/hswctest/'+ self.path.strip('/')
        info = oidconsumer.complete(self.query, url)

        sreg_resp = None
        pape_resp = None
        css_class = 'error'
        display_identifier = info.getDisplayIdentifier()
        print 'display_identifier is ' + display_identifier

        if info.status == consumer.FAILURE and display_identifier:
            # In the case of failure, if info is non-None, it is the
            # URL that we were verifying. We include it in the error
            # message to help the user figure out what happened.
            fmt = "Verification of %s failed: %s"
            message = fmt % (cgi.escape(display_identifier),
                             info.message)
        elif info.status == consumer.SUCCESS:
            # Success means that the transaction completed without
            # error. If info is None, it means that the user cancelled
            # the verification.
            css_class = 'alert'

            # This is a successful verification attempt. Since this
            # is now a real application, we do stuff with the form data.
	    # Or at least will.
            fmt = "You have successfully signed up with %s as your identity."
            message = fmt % (cgi.escape(display_identifier),)
	    # ACTUALLY DO SHIT
            #sreg_resp = sreg.SRegResponse.fromSuccessResponse(info)
            #pape_resp = pape.Response.fromSuccessResponse(info)

	    # MAGIC MARKER 

        elif info.status == consumer.CANCEL:
            # cancelled
            message = 'Verification cancelled'
        elif info.status == consumer.SETUP_NEEDED:
            if info.setup_url:
                message = '<a href=%s>Setup needed</a>' % (
                    quoteattr(info.setup_url),)
            else:
                # This means auth didn't succeed, but you're welcome to try
                # non-immediate mode.
                message = 'Setup needed'
        else:
            # Either we don't understand the code or there is no
            # openid_url included with the error. Give a generic
            # failure message. The library should supply debug
            # information in a log.
            message = 'Verification failed.'

        self.render(message, css_class, display_identifier,
                    sreg_data=sreg_resp, pape_data=pape_resp)

    def buildURL(self, action, **query):
        """Build a URL relative to the server base_url, with the given
query parameters added."""
	# ugly hacks that work work
        base = self.server.base_url + '/' + action
        return appendArgs(base, query)

    def notFound(self):
        """Render a page with a 404 return code and a message."""
        fmt = 'The path <q>%s</q> was not understood by this server.'
        msg = fmt % (self.path,)
        openid_url = self.query.get('openid_identifier')
        self.render(msg, 'error', openid_url, status=404)

    def render(self, message=None, css_class='alert', form_contents=None,
               status=200, title="Homestuck Shipping World Cup",
               sreg_data=None, pape_data=None):
        """Render a page."""
        self.send_response(status)
        self.pageHeader(title)
        if message:
	    print message
            self.wfile.write("<div class='%s'>" % (css_class,))
            self.wfile.write(message)
            self.wfile.write("</div>")
        self.pageFooter(form_contents)

    def pageHeader(self, title):
        """Render the page header"""
        self.setSessionCookie()
	print (title, title, quoteattr(self.buildURL('verify')))
        self.wfile.write('''\
Content-type: text/html; charset=UTF-8

<html>
<head><title>HSWC SIGNUPS</title></head>
<style type="text/css" media="all">
<!-- to protect older browsers apparently? -->
html, body {	
	font-family: Verdana,Arial,"Liberation Sans",sans-serif;
	color: #000;
	font-size: 11pt;
	background-color: #e5e4e5;
}

a:link {
	color: #3c3c89;
	font-weight:bold;
	text-decoration: none;
}

a:hover {
	color: #4e5273;
	font-weight:bold;
	text-decoration: underline;
}

h1 {
	font-size: 18pt;
	text-transform: uppercase;
	color: #3c3c89;
	text-align: center;
}

.navigation {
	margin-left: auto;
	margin-right: auto;	
	text-align: center;
	border-top: 1px #4e5273 solid;
	width:50%;
	padding: 22px 0px 10px 0px;
}

#verify-form { 
	border: 2px #4e5273 solid;
	margin: 0px 10px 20px 10px;
	padding: 7px;
	background-color: #fff;
	font-weight: bold;
	text-align: center;
	display:none;
	}

.alert {
	border: 1px solid #e7dc2b;
	background-color: #fff888;
	font-weight: bold;
}

.error {
	border: 1px solid #ff0000;
	background-color: #ffaaaa;
	font-weight: bold;
}

form {
	width: 70%;
	background-color: #fff;
	padding: 20px;
	margin-left: auto;
	margin-right: auto;
	margin-top:1%;
	border-radius:10px;
	box-shadow:5px 5px #babad5;
}

.edit { 
	border: 2px #4e5273 solid;
	margin: 7px;
	padding: 7px;
	background-color: #f1f1f1;
	}

input, textarea {
	border: 1px solid black;
	background-color: #fff;
	margin: 3px 0px 0px 0px;
}

.field {
	font-weight:bold
	}

.descrip {
	font-size:10pt;
	color:#202020;
}


table {
	width: 80%;
	background-color: #fff;
	padding: 20px;
	margin-left: auto;
	margin-right: auto;
	margin-top:1%;
	border-radius:10px;
	box-shadow:5px 5px #babad5;
}
.tableheader {
	background-color: #e3e3e3;
}

tr:hover {
	background-color: #babad5;
}
</style>

<body>

	<h1>
	HSWC 2014 Sign Up Form
	</h1>

<p class="navigation">Team Roster | <a href="http://hs_worldcup.dreamwidth.org">Dreamwidth</a> | <a href="http://autumnfox.akrasiac.org/hswcrules">Rules Wiki</a> | <a href="http://hswc-announce.tumblr.com">Tumblr</a></p>
''')

    def pageFooter(self, form_contents):
        """Render the page footer"""
        if not form_contents:
            form_contents = ''
        self.wfile.write('''\
<br/>
<form method="GET" accept-charset="UTF-8" action=%s>
<p class="edit">
	<strong>To edit your sign up for any reason</strong> (typos, wrong 
e-mail, switching teams, new content tags, etc.), just sign up 
again. You won't lose your current team spot (unless you're 
switching teams).
</p>

<p>
	<span class="field">Dreamwidth Username:</span><br />
	<span class="descrip">You need a <a href="https://www.dreamwidth.org/create">DW account</a>. Make sure it's <a href="http://hs-worldcup.dreamwidth.org/2803.html#join">verified</a>!</span><br />
	<input name="username" type="text" />
</p>

<p>
	<span class="field">E-mail Address:</span><br />
	<input name="email" type="text" />
</p>

<p>
	<span class="field">Joining HSWC Team:</span><br />
	<span class="descrip">Format your team name <a href="http://hswc-announce.tumblr.com/post/49934185410/how-to-write-ship-names">like this</a>!</span><br />
	<input name="team" type="text" />
</p>

<p>
	<span class="field">Would you like to volunteer to be the team's <a href="http://autumnfox.akrasiac.org/hswcrules/Teams#Friendleaders">Friendleader?</a>:</span><br />
	<input name="FL" value="yes" type="radio" />Yes &nbsp; <input name="FL" value="no" type="radio" />No
</p>

<p>
	<span class="field">Any noteworthy content tags that you would like to add and are not already listed on the <a href="http://autumnfox.akrasiac.org/hswcrules/Tags%%20List">content tags list?</a>:</span> <br />
	<span class="descrip">The major content tags are used to warn for 
content that may be potentially upsetting and is not a place for 
sarcastic comments or jokes. Misusing the tag request form may result in
 your removal from the HSWC.</span><br />
	<textarea name="content-tags" rows="5" cols="70">&nbsp;</textarea>
</p>

<p>
	<span class="field"><a href="http://autumnfox.akrasiac.org/hswcrules/Participant%%20Agreement">Participant Agreement</a>'s rules check phrase:</span><br />
	<input name="rules-check" type="text" />
</p>

<input type="submit" value="Sign up!">

</form>
 
</body></html>
''' % (quoteattr(self.buildURL('verify')),))

def main(host, port, data_path, weak_ssl=False):
    # Instantiate OpenID consumer store and OpenID consumer. If you
    # were connecting to a database, you would create the database
    # connection and instantiate an appropriate store here.
    if data_path:
        store = filestore.FileOpenIDStore(data_path)
    else:
        store = memstore.MemoryStore()

    if weak_ssl:
        setDefaultFetcher(Urllib2Fetcher())

    addr = (host, port)
    server = OpenIDHTTPServer(store, addr, OpenIDRequestHandler)

    print 'Server running at:'
    print server.base_url
    server.serve_forever()

if __name__ == '__main__':
    host = 'localhost'
    port = 8001
    weak_ssl = False

    try:
        import optparse
    except ImportError:
        pass # Use defaults (for Python 2.2)
    else:
        parser = optparse.OptionParser('Usage:\n %prog [options]')
        parser.add_option(
            '-d', '--data-path', dest='data_path',
            help='Data directory for storing OpenID consumer state. '
            'Setting this option implies using a "FileStore."')
        parser.add_option(
            '-p', '--port', dest='port', type='int', default=port,
            help='Port on which to listen for HTTP requests. '
            'Defaults to port %default.')
        parser.add_option(
            '-s', '--host', dest='host', default=host,
            help='Host on which to listen for HTTP requests. '
            'Also used for generating URLs. Defaults to %default.')
        parser.add_option(
            '-w', '--weakssl', dest='weakssl', default=False,
            action='store_true', help='Skip ssl cert verification')

        options, args = parser.parse_args()
        if args:
            parser.error('Expected no arguments. Got %r' % args)

        host = options.host
        port = options.port
        data_path = options.data_path
        weak_ssl = options.weakssl

    main(host, port, data_path, weak_ssl)
