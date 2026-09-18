import BigWorldConstants
import os
from mod_python import apache

from xml.dom import minidom

import logging

log = logging.getLogger( "fd_python.lib.ItemManager" )

class ItemType( object ):
	def __init__( self, name, title, description ):
		self.name = name
		self.title = title
		self.description = description


class ItemManager( object ):

	def __init__( self, path ):
		self._itemMap = {}
		log.info( "path = %s", path )
		doc = minidom.parse( path )
		for itemTypeElement in \
				doc.documentElement.getElementsByTagName( "itemType" ):
			id, name, title = map( itemTypeElement.getAttribute,
				["id", "name", "title"] )
			descElement = itemTypeElement.\
				getElementsByTagName( "description" )[0]
			desc = None
			if descElement.childNodes:
				desc = descElement.firstChild.nodeValue
			self.addItemType( int( id ), name, title, desc )


	def addItemType( self, itemTypeID, *itemTypeArgs ):
		self._itemMap[itemTypeID] = ItemType( *itemTypeArgs )

	def removeItemType( self, itemTypeID ):
		self._itemMap.remove( itemTypeID )

	def getThumbnailImgUrl( self, itemTypeID ):
		if itemTypeID in self._itemMap:
			item = self._itemMap[ itemTypeID ]
			return "/".join( [BigWorldConstants.ITEMS_IMAGE_ROOT,
				"icon_%s.gif" % item.name] )
		else:
			return None

	def getItem( self, itemTypeID ):
		return self._itemMap[ itemTypeID ]

itemManager = ItemManager( BigWorldConstants.ITEMS_DEF_PATH )

# ItemManager.py
