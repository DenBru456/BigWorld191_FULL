###This module implements the Info client-only entity type.
###This entity shows information text when approached.

import BigWorld
import FantasyDemo
import Math
import GUI
import FDGUI
from FDGUI import Minimap
from Helpers import Caps

#Austin GDC 2007 - ability to toggle visibility of all info entities
allInfoEntities = []
infoEntitiesVisible = True

def setVisibilityOfAllInfoEntities( state ):
	global infoEntitiesVisible
	infoEntitiesVisible = state
	for i in allInfoEntities:
		i.model.visible = state

class Info( BigWorld.Entity ):
	MODEL_NONE			= 0
	MODEL_INFO			= 1
	MODEL_ARROW			= 2

	modelNames = {
		MODEL_NONE:			"",
		MODEL_INFO:			"sets/items/information.model",
		MODEL_ARROW:		"sets/items/arrow.model",
		}

	def __init__( self ):
		BigWorld.Entity.__init__( self )
		self.chunkModel = None
		self.targetCaps = []
		self.seen = False
		self.active = False
		self.infoGUI = None
		# allows activation when distance is equal or less to 'activateDist':
		if self.showWhenNear:
			self.activateDist = 3
		else:
			self.activateDist = 6

	# entity callbacks
	def prerequisites( self ):
		return [self.modelName(), 'gui/info.gui']

	def onEnterWorld( self, prereqs ):
		#hold onto prereqs, specifically for loading
		#info.gui on-demand when somebody enters our trap
		allInfoEntities.append(self)
		self.model = prereqs.pop(self.modelName())
		self.prereqs = prereqs
		BigWorld.addShadowEntity( self )
		self.model.scale = (1,1,1)
		self.targetFullBounds = True
		self.setupTrap()
		self.model.visible = infoEntitiesVisible
		FantasyDemo.addDeviceListener(self)
		Minimap.addEntity( self )

	def onLeaveWorld( self ):
		if self.infoGUI is not None:
			FantasyDemo.rds.fdgui.delChild( self.infoGUI )
		self.model = None
		self.infoGUI = None
		Minimap.delEntity( self )
		BigWorld.delShadowEntity( self )
		if hasattr(self, "potID"):
			BigWorld.delPot(self.potID)
			del self.potID

		FantasyDemo.delDeviceListener(self)
		allInfoEntities.remove(self)
		del self.prereqs

	def name( self ):
		return "Info"

	def use( self ):
		dist = Math.Vector3( self.model.position - BigWorld.player().position).length
		if dist > self.activateDist:
			return

		if not self.active:
			self.activate( True )
		else:
			self.activate( False )

	# methods for internal use:
	def modelName( self ):
		return Info.modelNames[ self.modelType ]

	def setupTrap( self ):
		try:
			self.potID = BigWorld.addPot( self.model.matrix, self.activateDist, self.infoTrap )
			self.activate( False )
		except EnvironmentError:
			# If chunk not yet loaded try again in 5s
			BigWorld.callback( 5, self.setupTrap )

	def infoTrap( self, entered, handle ):
		if entered:
			# in range anymore, activate.
			if self.showWhenNear:
				self.activate( True )
		else:
			# if not in range anymore, deactivate.
			self.activate( False )

	def activate( self, doActivate ):
		self.active = doActivate
		if doActivate:
			if self.infoGUI == None:
				self.infoGUI = GUI.load( self.prereqs['gui/info.gui'] )
				self.infoGUI.position.z = FDGUI.Z_ORDER_INFO
				self.infoGUI.windowGUI.script.text( self.text )
			FantasyDemo.rds.fdgui.addChild( self.infoGUI )
			self.infoGUI.visible = True
			self.invalidate()
			if not self.seen and self.modelType != Info.MODEL_NONE:
				self.model.PlayInactive()
				self.model.empty_skinned = 'inactive'
			self.seen = True
		else:
			if self.infoGUI != None:
				self.infoGUI.visible = False
			if not self.seen and self.modelType != Info.MODEL_NONE:
				self.model.PlayActive()
				self.model.empty_skinned = 'Default'

	def onRecreateDevice(self):
		self.invalidate()

	def invalidate(self):
		if self.infoGUI != None:
			self.infoGUI.windowGUI.script.invalidate()
			self.infoGUI.frameGUI.height = self.infoGUI.windowGUI.height
			self.infoGUI.height = self.infoGUI.windowGUI.height


#Info.py
