#!/usr/bin/env python
"""
Stress testing web integration module.
"""
import cookielib
import urllib2
import urllib
import optparse

DEFAULT_USER_AGENT = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.5) Gecko/20070719 Iceweasel/2.0.0.5 (Debian-2.0.0.5-0etch1)'

def readURL( f ):
	chunk = f.read()
	out = chunk
	while not chunk:
		print chunk
		chunk = f.read()
		out += chunk
	return out

def doInventoryTest( addr, username, password, character ):

	cookieJar = cookielib.CookieJar()

	opener = urllib2.build_opener( urllib2.HTTPCookieProcessor( cookieJar ), 
		urllib2.HTTPRedirectHandler() )
	
	headers = {'User-Agent': DEFAULT_USER_AGENT }

	# initial request (get cookie)
	req = urllib2.Request( addr + "/Login", headers=headers )
	f = opener.open( req )
	print f.geturl()
	print f.info()
	for cookie in cookieJar:
		print cookie.name, cookie.value, cookie.path
	# login
	req = urllib2.Request( addr + "/Login", 
		data = urllib.urlencode( 
			dict( submit="login", username = username, password = password ) ) 
		)
	print "logging in with %s/%s" % (username, password)
	f = opener.open( req )
	print f.geturl()
	if not f.geturl().endswith( 'Characters' ):
		print f.read()
		raise ValueError, "login failed with %s/%s" % (username, password)
		
	try:
		# characters page
		req = urllib2.Request( 
			addr + "/Characters?%s" % urllib.urlencode(
				dict( choose=character ) ) )

		print "choosing character: %s" % character
		f = opener.open( req )
		print f.geturl()
		if not f.geturl().endswith( "Welcome" ):
			raise ValueError, \
				"login failed with character selection: %s" % character

		# inventory page
		print "getting inventory"
		req = urllib2.Request( addr + "/Inventory" )
		f = opener.open( req )
		print f.read()
		
	except:
		print "logging out due to exception"
		req = urllib2.Request( addr + "/Welcome.py?logout=1" )
		opener.open( req )
		raise

	print "logging out"
	req = urllib2.Request( addr + "/Welcome.py?logout=1" )
	f = opener.open( req )
	if not f.geturl().endswith( "Login" ):
		print "logout failed!"

def main( options, addr ):
	numIterations = int( options.numIterations )
	if numIterations == -1:
		while True:
			doInventoryTest( addr, options.username, 
				options.password, options.character )
	else:
		for i in xrange( numIterations ):
			doInventoryTest( addr, options.username, 
				options.password, options.character )

if __name__ == "__main__":
	import sys
	import os

	commandLineParser = optparse.OptionParser(
		usage = "%s <addr>" % os.path.basename( sys.argv[0] )
	)

	commandLineParser.add_option( "-n", 
		dest="numIterations",
		action="store",
		default=1,
		help="number of iterations (default %default, specify -1 for infinite)" 	)

	commandLineParser.add_option( "-u", dest="username", default="dominicw",
		help="username (default %default)" )
	commandLineParser.add_option( "-p", dest="password", default="aa",
		help="password (default %password)" )
	commandLineParser.add_option( "-c", dest="character", default="Dom0",
		help="character (default %default)" )
	
	options, args = commandLineParser.parse_args()
	if len( args ) < 1:
		commandLineParser.print_help()
		sys.exit( 1 )
	addr = args[0]

	main( options, addr )



