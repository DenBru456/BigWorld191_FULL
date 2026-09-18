import BigWorld
import Cursor
from Keys import *
import Helpers.PyGUI as PyGUI
from Helpers.PyGUI import PyGUIEvent
from Helpers.Listener import Listenable
from Helpers import BWKeyBindings
from Helpers.BWKeyBindings import BWKeyBindingAction
import FantasyDemo
from GuardSpawner import spawnGuardsEverywhere
from GuardSpawner import destroyGuardsEverywhere


#------------------------------------------------------------------------------
# This class handles the minimap when it is in 'large' mode.  The buttons and
# events are different to when it is in 'small' mode.
#------------------------------------------------------------------------------
class LargeMinimap( PyGUI.Window, BWKeyBindings.BWActionHandler ):

	factoryString = "FDGUI.LargeMinimap"

	def __init__( self, component ):
		PyGUI.Window.__init__( self, component )
		BWKeyBindings.BWActionHandler.__init__( self )
		self.component.script = self
		self.minimap = None
		self.timeCallback = None


	def onActive( self ):
		BigWorld.callback( 1.0, self._updateCallback )
		self.boundariesButton.setToggleState( self._minimap().cellBoundsVisible )
		self.entriesButton.setToggleState( self._minimap().simpleEntriesVisible )
		m = self._minimap()
		m.maskName = self.maskName
		m.script.maxZoom = 5000
		m.script.minZoom = 250


	def _updateCallback( self ):
		if self.isActive:
			BigWorld.callback( 1.0, self._updateCallback )
			self.updateStats()


	def active( self, state ):
		if state == True:
			FantasyDemo.rds.region.addListener( self )
			FantasyDemo.rds.keyBindings.addHandler( self )
			self.component.region.text = FantasyDemo.rds.region.describeCurrent()
		else:
			FantasyDemo.rds.region.delListener( self )
			FantasyDemo.rds.keyBindings.removeHandler( self )
		self.component.focus = state
		self._minimap().mouseEntryPicking = state
		PyGUI.Window.active( self, state )
		self.onActive()
		self._updateRangeLabel()
		player = BigWorld.player()
		if player:
			player.cell.enableEntityInfoCapture(state)


	@PyGUIEvent( "cellBoundaries", "onActivate", True )
	@PyGUIEvent( "cellBoundaries", "onDeactivate", False )
	def onCellBoundariesActivate( self, activated ):
		self._minimap().cellBoundsVisible = activated


	@PyGUIEvent( "simpleEntries", "onActivate", True )
	@PyGUIEvent( "simpleEntries", "onDeactivate", False )
	def onSimpleEntriesActivate( self, activated ):
		self._minimap().simpleEntriesVisible = activated


	@PyGUIEvent( "spawn", "onClick" )
	def onSpawnClick( self ):
		spawnGuardsEverywhere( 100 )


	@PyGUIEvent( "destroy", "onClick" )
	def onDestroyClick( self ):
		destroyGuardsEverywhere( 100 )


	@BWKeyBindingAction( "ToggleMinimap" )
	@BWKeyBindingAction( "MinimiseMinimap" )
	@PyGUIEvent( "minimise", "onClick" )
	def onMinimiseClick( self, isDown = True ):
		if isDown:
			self._minimap().script.maximise( False )


	@PyGUIEvent( "zoomIn", "onClick" )
	def onZoomInClick( self ):
		self._minimap().script.zoomIn()
		self._updateRangeLabel()


	@PyGUIEvent( "zoomOut", "onClick" )
	def onZoomOutClick( self ):
		self._minimap().script.zoomOut()
		self._updateRangeLabel()


	def _updateRangeLabel( self ):
		range = self._minimap().range
		if range < 1000.0:
			self.component.visibleMapRange.text = "%dm" % (int(range))
		else:
			self.component.visibleMapRange.text = "%0.1fkm" % (range/1000.0)


	def onBound( self ):
		PyGUI.Window.onBound( self )
		self.boundariesButton = self.component.cellBoundaries.script
		self.entriesButton = self.component.simpleEntries.script
		self.containerSize = (1024,900)
		self.minimapSize = self.containerSize
		self.maskName = ""


	#Callback from region event listener
	def onEnterRegion( self, description ):
		self.component.region.text = description


	#Callback from region event listener
	def onLeaveRegion( self, description ):
		self.component.region.text = description


	def updateStats( self ):
		self.component.entitiesInAOI.text = BigWorld.getWatcher( "Entities/Active Entities" )
		if BigWorld.player() is not None:
			self.component.entitiesOnCell.text = str(BigWorld.player().entityInfo)
			self.component.currentCellID.text = str(BigWorld.player().cellAppID)


	def _minimap( self ):
		return self.minimap


	@BWKeyBindingAction( "Teleport" )
	def teleport( self, isDown = True ):
		if isDown:
			self._minimap().script.teleportToMousePosition()
			return True


	def avatarFini( self, avatar ):
		""" Function called when our PlayerAvatar leaves the world. """
		#~ # Large minimap does not get left in a valid state when maximised, so minimise it when we leave.
		self._minimap().script.maximise( False )
