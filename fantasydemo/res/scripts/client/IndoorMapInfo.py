"""This module implements the IndoorMapInfo entity type."""


import BigWorld
from functools import partial
import FantasyDemo
from FDGUI import Minimap


class MinimapInfo:
	#This class static serial number helps us ignore late / out of order
	#callbacks, necessary since we do asnychronous loading of files.
	serial = 0
	
	def __init__( self ):
		self.textureName = ""
		self.range = 0.0
		self.worldMapWidth = 1000.0
		self.worldMapHeight = 1000.0
		self.worldMapAnchor = (0,0)
		self.rotate = False

	
	#Apply this minimap info to the given minimap. We may require
	#a texture map to load, and we may also need to load a space.settings
	#file to retrieve the space bounds.  These are loaded in the background
	#thread.  The serial number is used to ignore out-of-order callbacks
	#from these asnychronous load methods.
	def apply( self, minimap, serial = -1 ):
	
		if serial == -1:
			MinimapInfo.serial += 1
			serial = MinimapInfo.serial
			
		if serial != MinimapInfo.serial:
			return

		if self.textureName != None:
			BigWorld.loadResourceListBG( (self.textureName,), partial(self._onLoadTexture,minimap,serial) )
		else:
			spaceID = BigWorld.player().spaceID
			try:
				spaceName = FantasyDemo.rds.spaceNameMap[spaceID]
			except:
				spaceName = "spaces/navgen_test_space"
			self.textureName = spaceName + "/space.thumbnail.dds"
			callback = partial(self._onLoadSpaceSettings,minimap,serial)
			settingsFile = spaceName+"/space.settings"
			BigWorld.loadResourceListBG((settingsFile,), callback)


	#Get the minimap information from space.settings.  If the space
	#settings file has no minimap information, then use the default
	#space map from World Editor, and read the bounds in from the
	#space bounds.
	def _onLoadSpaceSettings( self, minimap, serial, resourceRef ):
		if serial != MinimapInfo.serial:
			return
					
		ds = resourceRef.values()[0]
		
		bounds = ds["bounds"]
		minX = bounds.readInt("minX",-5)
		maxX = bounds.readInt("maxX",4)
		minY = bounds.readInt("minY",-5)
		maxY = bounds.readInt("maxY",4)
		self.worldMapWidth = ((maxX - minX) + 1) * 100.0
		#NOTE - the automatic outdoor space map we use are upside-down,
		#so we need to negate the y-axis here
		self.worldMapHeight = -((maxY - minY) + 1) * 100.0
		xCenter = (minX * 100.0) + self.worldMapWidth / 2.0
		yCenter = (minY * 100.0) + -self.worldMapHeight / 2.0
		self.worldMapAnchor = (xCenter, yCenter)
			
		if ds.has_key( "minimap" ):
			ds = ds["minimap"]
			self.textureName = ds.readString( "mapName" )
			self.worldMapWidth = ds.readFloat( "worldMapWidth", self.worldMapWidth )
			self.worldMapHeight = ds.readFloat( "worldMapHeight", self.worldMapHeight )
			self.worldMapAnchor = ds.readVector2( "worldMapAnchor" )
			
		self.apply( minimap, serial )


	def _onLoadTexture( self, minimap, serial, resourceRef ):
		if serial != MinimapInfo.serial:
			return
		
		minimap.texture = resourceRef[self.textureName]
		minimap.range = self.range
		minimap.rotate = self.rotate
		minimap.worldMapWidth = self.worldMapWidth
		minimap.worldMapHeight = self.worldMapHeight
		minimap.worldMapAnchor = self.worldMapAnchor
		

# ------------------------------------------------------------------------------
# Class IndoorMapInfo:
#
# A IndoorMapInfo entity tells the client what the bitmap will be for the minimap
# when the player goes into an indoor area, as well as specifying other minimap
# settings.
# ------------------------------------------------------------------------------
class IndoorMapInfo( BigWorld.Entity ):

	# --------------------------------------------------------------------------
	# Method: __init__
	# --------------------------------------------------------------------------
	def __init__( self ):
		BigWorld.Entity.__init__( self )

		#
		# Set all standard entity variables.
		#
		self.targetCaps = []
		self.model = None


	# --------------------------------------------------------------------------
	# Method: checkProperties
	# Description:
	#	- Checks all properties defined in the XML file to see if they are
	#	  valid.
	# --------------------------------------------------------------------------
	def checkProperties( self ):
		# methodName = "IndoorMapInfo.checkProperties: "
		pass


	# --------------------------------------------------------------------------
	# Method: onEnterWorld
	# --------------------------------------------------------------------------
	def onEnterWorld( self, prereqs ):
		self.potID = BigWorld.addPot( self.matrix, self.radius, self.hitPot )
		mi = MinimapInfo()
		mi.textureName = self.mapName
		mi.range = self.minimapRange
		mi.worldMapWidth = self.worldMapWidth
		mi.worldMapHeight = self.worldMapHeight
		mi.worldMapAnchor = self.worldMapAnchor
		mi.rotate = self.minimapRotate
		self.mi = mi


	# --------------------------------------------------------------------------
	# Method: onLeaveWorld
	# --------------------------------------------------------------------------
	def onLeaveWorld( self ):
		if hasattr( self, "potID" ):
			BigWorld.delPot( self.potID )
		self.prereqs = None


	# --------------------------------------------------------------------------
	# Method: hitPot
	#
	# This method is called when the player enters / leaves the radius.
	# --------------------------------------------------------------------------
	def hitPot( self, enter, id = None ):
		player = BigWorld.player()
		if not player:
			return
			
		if enter:
			BigWorld.player().triggeredIndoorMapEntity = self.id
			#re-trigger minimap creation.  This is necessary because the
			#player may have just teleported from one indoor area to another
			BigWorld.player().onChangeEnvironments( BigWorld.player().inside )


	# --------------------------------------------------------------------------
	# Method: mapInfo
	#
	# This method returns the information we want to set on the minimap.
	# --------------------------------------------------------------------------
	def mapInfo( self ):
		return self.mi
		
	# --------------------------------------------------------------------------
	# Method: name
	#
	# This method returns the name of this class.
	# --------------------------------------------------------------------------
	def name( self ):
		return "Indoor Map Info"


#IndoorMapInfo.py
