from lib import BigWorldAuthPage
from lib import xhtml

class Welcome( BigWorldAuthPage.BigWorldAuthPage ):
	"""
	Simple welcome page, which just has a menu for the user. Currently, we only
	have the Inventory page.

	You could at this point, query the server for things like news items,
	server status, etc.
	"""
	def __init__( self, req ):
		BigWorldAuthPage.BigWorldAuthPage.__init__( self, req,
			title='Welcome',
			stylesheets=['styles/style.css'] )


	def renderBody( self ):

		linkListContents = []
		linkListContents.append( xhtml.link( 'Inventory', 'Inventory' ) )

		self.echo( xhtml.heading( self.title ) )
		self.echo( xhtml.list( linkListContents ) )
		self.renderMenuBar()

		if self.msgs:
			self.echo( xhtml.list( self.msgs, className='status' ) )

# Welcome.py
