#!/usr/bin/env python2.5

PATH = '/home/dominicw/bw-19d/bigworld/bin/web/Hybrid'

import optparse

def main( options ):

	import sys
	sys.path.append( PATH )
	import pyBigWorld
	pyBigWorld.setDefaultKeepAliveSeconds( 300 )
	pyBigWorld.logOn( options.username, options.password )

	for i in xrange( int( options.numIterations ) ):
		account = pyBigWorld.lookUpEntityByName( "Account", options.username )
		if type( account ) == bool:
			print "Logon failed"

		res = account.webGetCharacterList()

		print res
		print res['characters'][0]['name']

		character, characterType = options.character, "Avatar"
		
		if character is None or characterType is None:
			character = res['characters'][0]['name']
			characterType = res['characters'][0]['type']
		print "Choosing character '%s' (%s)" % (character, characterType)
		res = account.webChooseCharacter( character, characterType )
		avatar = res['character']

		if avatar is None:
			raise ValueError, res['errMsg']

		print avatar.webGetGoldAndInventory()

if __name__ == "__main__":
	
	parser = optparse.OptionParser()

	parser.add_option( "-n", dest="numIterations", default="1" )
	parser.add_option( "-u", dest="username", default="dominicw" )
	parser.add_option( "-p", dest="password", default="aa" )
	parser.add_option( "-c", dest="character", default=None )
	options, args = parser.parse_args()

	main( options )
