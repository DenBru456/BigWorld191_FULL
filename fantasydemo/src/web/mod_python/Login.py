from mod_python import util
from mod_python import apache

from lib.AuthPage import AuthPage
from lib import xhtml
from lib import BigWorldConstants
from lib import BigWorldAuth


import logging
log = logging.getLogger( "fd_python.Login" )

class Login( AuthPage ):
	"""
	The login page. This page authenticates username and passwords using the
	BigWorldAuth module, which wraps around the web integration BigWorld shared
	library.
	"""

	def __init__( self, req ) :

		AuthPage.__init__( self, req,
			title='FantasyDemo Login',
			stylesheets=['styles/style.css',
				'styles/style.css'] )

		if self.session.is_new():
			remote_host = self.req.get_remote_host( apache.REMOTE_NOLOOKUP )
			self.session['ip'] = remote_host
			self.session.save()
			log.debug( "session set remote_host = %s", remote_host )

		self.username = ''
		self.password = ''
		self.errorMsgs = []
		self.auth = BigWorldAuth.BigWorldAuth()

	def initialise( self ):
		if 'player' in self.session:
			# we're authenticated
			util.redirect( self.req, BigWorldConstants.WELCOME_PAGE )

		if not 'submit' in self.fields:
			return

		if 'username' in self.fields:
			self.username = self.fields['username']

		password = ''
		if 'password' in self.fields:
			password = self.fields['password']

		log.debug( "about to authenticate" )
		result, errmsgs = self.auth.authenticate( self.session,
			self.username, password )
		log.debug( "finished authenticating: result is %s", result )

		if result:
			log.debug( "Login.initialise - auth result is True - "
				"redirecting to Characters" )
			log.debug( "session : %s",  self.session.items() )
			util.redirect( self.req, BigWorldConstants.CHARACTERS_PAGE )
		else:
			self.errorMsgs += [errmsgs]


	def renderBody( self ):
		self.echo( xhtml.tag( 'h1', 'Login' ) )
		log.info( "renderBody" )
		if self.errorMsgs:
			self.echo( xhtml.list( self.errorMsgs, className='error' ) )

		self.echo( xhtml.form(
			action="Login",
			method="post",
			contents=xhtml.tag( 'div',
					'Username' + xhtml.BR +
					xhtml.formInputText( 'username', self.username ) +
						xhtml.BR +
					'Password' + xhtml.BR +
					xhtml.formInputPassword( 'password' ) + xhtml.BR +
					xhtml.formInputSubmit( 'login', name="submit" ),
				'loginbox' ) ) )

		if self.msgs:
			self.echo( xhtml.list( self.msgs, className='status' ) )

# Login.py
