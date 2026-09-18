#!/usr/bin/env python
"""
Stress testing web integration module.
"""
import cookielib
import urllib2
import urllib
import optparse

# Grabbed this from my Linux box
DEFAULT_USER_AGENT = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.5) Gecko/20070719 Iceweasel/2.0.0.5 (Debian-2.0.0.5-0etch1)'

def readURL( f ):
	chunk = f.read()
	out = chunk
	while not chunk:
		print chunk
		chunk = f.read()
		out += chunk
	return out



def doLogin( opener, addr, username, password, character ):
	headers = {'User-Agent': DEFAULT_USER_AGENT }
	
	# initial request (get cookie)
	req = urllib2.Request( addr + "/Login.php?logout=1", headers=headers )
	f = opener.open( req )
	print f.geturl()
	print f.info()
	
	# login
	req = urllib2.Request( addr + "/Login.php", 
		data = urllib.urlencode( 
			dict( username = username, password = password ) ) )
	print "logging in with %s/%s" % (username, password)
	f = opener.open( req )
	print f.geturl()
	if not f.geturl().endswith( 'Characters.php' ):
		print f.read()
		raise ValueError, "login failed with %s/%s" % (username, password)
		
	try:
		# characters page
		req = urllib2.Request( 
			addr + "/Characters.php?character=%s" % character )

		print "choosing character: %s" % character
		f = opener.open( req )
		print f.geturl()
		if not f.geturl().endswith( "News.php" ):
			raise ValueError, \
				"login failed with character selection: %s" % character
	except:
		print "logging out due to exception"
		req = urllib2.Request( addr + "/Login.php?logout=1" )
		opener.open( req )
		raise
	
def doCharacter( opener, addr ):
	print "looking at character"

	req = urllib2.Request( addr + "/Character.php" )
	f = opener.open( req )
	print f.read()

def doAuctionSearch( opener, addr ):
	headers = {'User-Agent': DEFAULT_USER_AGENT }

	data = {
		'search_type_name': '',
		'search_min_bid': '',
		'search_max_bid': '',
		'search_submit': 'Search'
	}
		
	print "searching auctions"
	req = urllib2.Request( addr + "/SearchAuctions.php?%s" % 
		urllib.urlencode( data ) )
	f = opener.open( req )
	print f.read()
	
def doMyAuctions( opener, addr ):
	headers = {'User-Agent': DEFAULT_USER_AGENT }

	print "my auctions"
	req = urllib2.Request( addr + "/PlayerAuctions.php" )
	f = opener.open( req )
	print f.read()

def doInventoryTest( opener, addr ):

	headers = {'User-Agent': DEFAULT_USER_AGENT }

	try:
		# inventory page
		print "getting inventory"
		req = urllib2.Request( addr + "/Inventory.php" )
		f = opener.open( req )
		print f.read()
	except:
		print "logging out due to exception"
		req = urllib2.Request( addr + "/Login.php?logout=1" )
		opener.open( req )
		raise
		
def main( options, addr ):
	cookieJar = cookielib.CookieJar()
	opener = urllib2.build_opener( urllib2.HTTPCookieProcessor( cookieJar ), 
		urllib2.HTTPRedirectHandler() )
	
	numIterations = int( options.numIterations )

	doLogin( opener, addr, options.username, options.password, 
		options.character )

	if numIterations == -1:
		while True:
			runLoggedInTests( opener, addr )
	else:
		for i in xrange( numIterations ):
			runLoggedInTests( opener, addr )
	
	print "logging out"
	req = urllib2.Request( addr + "/Login.php?logout=1" )
	opener.open( req )


def runLoggedInTests( opener, addr ):
	doCharacter( opener, addr )
	doInventoryTest( opener, addr )
	doAuctionSearch( opener, addr )
	doMyAuctions( opener, addr )
	

if __name__ == "__main__":
	import sys
	import os

	clParser = optparse.OptionParser(
		usage = "%s <addr>" % os.path.basename( sys.argv[0] )
	)

	clParser.add_option( "-n", 
		dest="numIterations",
		action="store",
		default=1,
		help="number of iterations (default %default, specify -1 for infinite)" 	)
	
	clParser.add_option( "-u",
		dest="username",
		action="store",
		default="dominicw",
		help="username (default \"%default\")" )

	clParser.add_option( "-p",
		dest = "password",
		action="store",
		default="aa",
		help="password (default \"%default\")" )

	clParser.add_option( "-c",
		dest = "character",
		action="store",
		default="Dom0",
		help="character name (default \"%default\")" )

	options, args = clParser.parse_args()
	if len( args ) < 1:
		clParser.print_usage()
		sys.exit( 1 )
	addr = args[0]

	main( options, addr )



