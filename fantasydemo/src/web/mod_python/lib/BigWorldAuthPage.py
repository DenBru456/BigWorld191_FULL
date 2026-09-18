from lib import AuthPage
from lib import BigWorldAuth
from lib import BigWorldConstants
from lib import xhtml

import logging
log = logging.getLogger( "fd_python.BigWorldAuthPage" )

class BigWorldAuthPage( AuthPage.AuthPage ):
	"""
	This is the superclass for all BigWorld authenticated pages.
	"""

	def __init__( self, req, title,
			stylesheets=['styles/style.css'] ):
		"""
		Constructor. All the parameters are passed to the AuthPage.AuthPage
		constructor.
		"""

		AuthPage.AuthPage.__init__( self, req, title, stylesheets )
		self.menuItems = []

		self.addMenuItem( 'Logout', self.req.uri + '?logout=1' )


	def checkAuth( self ):
		"""
		Overridden from AuthPage.AuthPage.checkAuth.

		We check to see if there is a player and username in the current
		session.
		"""
		log.debug( "checkAuth started" )
		if not AuthPage.AuthPage.checkAuth( self ):
			log.debug( "checkAuth failed due to AuthPage.checkAuth" )
			return False

		res = 'username' in self.session and 'player' in self.session

		if res:
			log.debug( "BigWorldAuthPage.checkAuth() succeeded" )
		else:
			log.error( "BigWorldAuthPage.checkAuth() failed due to "
					"no username or databaseID set in session" )

		return res


	def addMenuItem( self, label, href ):
		"""
		Add a menu item to this page. This is rendered using renderMenuBar().

		@param label		the label of the menu item link
		@param href			the URL of the menu item
		"""
		self.menuItems.insert( 0, (label, href) )


	def renderMenuBar( self ):
		"""
		Render the menu.
		"""
		contents = ''
		first = True
		for label, href in self.menuItems:
			if not first:
				contents += '&nbsp;:&nbsp;'
			contents = contents + xhtml.link( href, label )
			first = False

		self.echo( xhtml.tag( 'div', contents, className='menubar' ) )

# BigWorldAuthPage.py
