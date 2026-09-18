import BigWorldConstants

from mod_python import apache, Session

import sys
import os

import logging
log = logging.getLogger( "fd_python.BigWorldAuth" )

##
# BigWorld library initialisation
#

# Set environment variables before importing BigWorld.
# This is necessary to set the right Bigworld server user.
os.environ['UID'] = str( BigWorldConstants.UID )
os.environ['HOME'] = str( BigWorldConstants.HOME )

import BigWorld


class BigWorldAuth( object ):

	def authenticate( self, session, username, password ):
		log.debug( "authenticate started" )
		errs = []
		if username == '':
			errs.append( 'Username is empty' )

		if username != '':
			log.info( 'Setting session variables' )
			session['username'] = username
			try:
				BigWorld.logOn( username, password,
					allow_already_logged_on=True )
				player = BigWorld.lookUpEntityByName( 'Account', username )
				if type( player ) == bool:
					if player:
						return (False,
							"Could not create Account for %s" % username)
					else:
						return (False,
							"Could not find Account for %s" % username)
			except Exception, e:
				errs.append( str( e ) )
				return ( False, errs )

			player.keepAliveSeconds = BigWorldConstants.MAX_INACTIVITY_TIMEOUT
			session['player'] = player
			session.save()

			log.debug( "saved username=%s, player=%s into session",
				session['username'], session['player'] )

		if errs:
			return (False, errs)

		return (True, None)

# BigWorldAuth.py
