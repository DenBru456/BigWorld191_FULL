from lib import BigWorldAuthPage
from lib import xhtml
from lib.ItemManager import itemManager

import datetime

class Inventory( BigWorldAuthPage.BigWorldAuthPage ):
	"""
	Inventory page for the current authenticated player.
	"""
	def __init__( self, req ):
		BigWorldAuthPage.BigWorldAuthPage.__init__( self, req,
			title='Inventory',
			stylesheets=['styles/style.css'] )
		self.gold = None
		self.invList = None

		self.addMenuItem( 'Welcome', 'Welcome' )

	def initialise( self ):
		player = self.session['player']

		res = player.webGetGoldAndInventory()

		self.gold = res['goldPieces']
		self.invList = res['inventoryItems']

	def renderItemList( self ):
		"""
		Render a list of the player's inventory.
		"""
		contents = ''

		for item in self.invList:
			itemType = item['itemType']
			itemTypeInfo = itemManager.getItem( itemType )
			url = itemManager.getThumbnailImgUrl( itemType )

			itemContents = ''

			# the image (if it can be found)
			if not url is None:
				itemContents  += \
					xhtml.img( url, 
						'%s [%d]' % (itemTypeInfo.title, itemType) ) + \
					xhtml.BR

			# title
			itemContents += xhtml.tag( 'b', itemTypeInfo.title )

			# description and trade selection checkbox
			itemContents += xhtml.para( itemTypeInfo.description + xhtml.BR )

			# stick it into a div element
			contents  += xhtml.tag( 'div',
				itemContents,
				attributes={
					'style':'border:1px black solid; '
					'text-align: center; '
					'padding-left:auto; '
					'padding-right:auto;'
				}
			)
		return contents

	def renderBody( self ):
		self.echo( xhtml.heading( 'Inventory' ) )

		if not self.gold is None:
			self.echo( xhtml.tag( 'div',
					xhtml.tag( 'b', '%d' % self.gold ) + 
					xhtml.img( 'images/goldcoin.png', 'gold' ),
				attributes=dict( align='right' )
			) )


		self.echo( self.renderItemList() )

		self.renderMenuBar()

		if self.msgs:
			self.echo( xhtml.list( self.msgs, className='status' ) )

# Inventory.py
