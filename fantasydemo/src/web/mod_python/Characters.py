from lib import BigWorldAuthPage
from lib import BigWorldConstants
from lib import xhtml

import urllib

from mod_python import util


class Characters( BigWorldAuthPage.BigWorldAuthPage ):
	"""
	Page for users to choose a character from the account that they have logged
	in as.
	"""
	def __init__( self, req ):
		BigWorldAuthPage.BigWorldAuthPage.__init__( self, req,
			title = 'Characters',
			stylesheets = ['styles/style.css'] )
		self.characterList = None
		self.errorMsgs = []


	def initialise( self ):
		account = self.session['player']

		res = account.webGetCharacterList()
		self.characterList = res['characters']

		if 'choose' in self.fields:
			res = account.webChooseCharacter( self.fields['choose'], "Avatar" )
			if not res['character']:
				self.errorMsgs.append( res['errMsg'] )
			else:
				player = res['character']
				player.keepAliveSeconds = \
					BigWorldConstants.MAX_INACTIVITY_TIMEOUT
				self.session['player'] = player
				self.session.save()
				util.redirect( self.req, BigWorldConstants.WELCOME_PAGE )
		elif 'new_character_name' in self.fields:
			newCharName = self.fields['new_character_name']
			res = account.webCreateCharacter( newCharName )
			if res['success']:
				self.msgs.append( "Character created: %s" % newCharName )
			else:
				self.errorMsgs.append( "Could not create new character %s: "
						"%s" %
					(newCharName, res['errMsg']) )
			res = account.webGetCharacterList()
			self.characterList = res['characters']


	def renderCharacterList( self ):
		"""
		Prints out the character list as a list, plus an extra list item for
		creating characters with.
		"""
		contents = ''
		for characterInfo in self.characterList:
			link = xhtml.tag( 'a', characterInfo['name'],
				attributes=dict( href="?%s" %
					urllib.urlencode(
						dict( choose=characterInfo['name']  ) )
				) )
			contents += xhtml.tag( 'li', link )


		form = xhtml.form(
			"New character name: " +
			xhtml.formInputText( "new_character_name" ) +
			xhtml.formInputSubmit( "Create" ) )
		contents += xhtml.tag( 'li', form )

		return xhtml.tag( 'ul', contents )

	def renderBody( self ):
		self.echo( xhtml.heading( 'Characters' ) )

		if self.errorMsgs:
			self.echo( xhtml.list( self.errorMsgs, className='error' ) )
		self.echo( self.renderCharacterList() )

		if self.msgs:
			self.echo( xhtml.list( self.msgs, className='status' ) )

		self.renderMenuBar()

# Characters.py
