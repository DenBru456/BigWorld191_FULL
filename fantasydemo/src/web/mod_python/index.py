from lib import Page
from mod_python import util


class index( Page.Page ):
	def __init__( self, req ):
		Page.Page.__init__( self, req )

	def initialise( self ):
		util.redirect( self.req, 'Login' )

# index.py
