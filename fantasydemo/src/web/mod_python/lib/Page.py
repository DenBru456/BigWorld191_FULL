from mod_python import apache, util

import datetime
import xhtml
import logging

log = logging.getLogger( "fd_python.Page" )

class Page( object ):

	def __init__( self, req, title='Page', stylesheets=[] ):
		self.req = req
		self.fields = util.FieldStorage( req, True )
		self.title = title
		self.stylesheets = stylesheets
		self.returnCode = apache.OK
		self.msgs = []


	def renderBody( self ):
		pass


	def renderHead( self ):
		self.echo( xhtml.tag( 'title', self.title ) + "\n" )
		if self.stylesheets:
			for stylesheet in self.stylesheets:
				self.echo(
					xhtml.singleTag( 'link',
						className=None,
						attributes={
							'rel':'stylesheet',
							'href':stylesheet }	) +
					"\n" )


	def render( self ):
		initResult = self.initialise()

		if initResult != None and initResult == False:
			return self.returnCode

		self.echo( "<html>\n" )
		self.echo ( "<head>\n" )
		self.renderHead()
		self.echo ( "</head>\n" )
		self.renderBody()
		self.echo( "</html>\n" )

		return self.returnCode


	def initialise( self ):
		pass

	def echo( self, *args ):
		self.req.write( *args )

	def addMsg( self, msg ):
		now = datetime.datetime.now()
		self.msgs.append( '%s.%06d %s: %s' % (now.strftime('%H:%M:%S'),
				now.microsecond,
				self.__class__.__name__, msg) )
		log.debug( msg )

# Page.py
