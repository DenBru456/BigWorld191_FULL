from mod_python import apache, Session, util

import xhtml
import Page
import BigWorldConstants

import logging
log = logging.getLogger( "fd_python.AuthPage" )

class AuthPage( Page.Page ):
	"""
	This is the superclass for all pages with validated authentication data. It
	stores authentication data in the session.
	"""

	def __init__( self, req, title='AuthPage', stylesheets=None ):
		"""
		Constructor. All the parameters are passed to the Page.Page
		constructor.

		"""
		Page.Page.__init__( self, req, title, stylesheets )
		self.session = Session.Session( req )

		if self.session.is_new():
			self.session.set_timeout( BigWorldConstants.MAX_INACTIVITY_TIMEOUT )
			self.session.save()
		else:
			self.session.load()

		log.debug( "Session created/last accessed: %s/%s",
			self.session.created(), self.session.last_accessed() )
		log.debug ( "session : %r", self.session.items() )

		# session page-specific variables
		self.session.setdefault( self._pageSessionKey(), {} )


	def _pageSessionKey( self ):
		"""
		The key in the session object for this page. The page-specific session
		data is stored using this key.
		"""
		return self.title + "_settings"


	def checkAuth( self ):
		"""
		Check the validity of the session to make sure that the request IP
		address is the same as the one IP we had when the session was first
		created.

		You can override this method to supply alternative authentication
		methods.
		"""
		#self.addMsg("Session ID: %s" % self.session.id())

		# check session

		# check IP address
		remoteHost = self.req.get_remote_host( apache.REMOTE_NOLOOKUP )
		if not self.session.has_key('ip') or remoteHost != self.session['ip']:
			# bad IP address or none taken
			self.session.invalidate()
			return False

		return True


	def render( self ):
		if 'logout' in self.fields and self.fields['logout'] != '':
			self.session.invalidate()
			util.redirect( self.req, BigWorldConstants.LOGIN_PAGE )

		if not self.checkAuth():
			self.addMsg( 'Your session is invalid or has expired, '
				'please log in again.' )
			util.redirect( self.req, BigWorldConstants.LOGIN_PAGE )
		result = Page.Page.render( self )
		return result


	def putSetting( self, key, value ):
		"""
		Save a page-specific session value.
		"""
		self.session[ self.title + '_settings' ][ key ] = value
		self.session.save()


	def getSetting( self, key, default=None ):
		"""
		Retrieve a page-specific session value.
		"""
		return self.session[ self._pageSessionKey() ].get( key, default )

# AuthPage.py
