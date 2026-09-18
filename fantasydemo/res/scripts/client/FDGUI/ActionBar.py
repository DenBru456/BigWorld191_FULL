import BigWorld
import Helpers.PyGUI as PyGUI

import FDGUI
import FantasyDemo

from Helpers.PyGUI import PyGUIEvent
from Helpers.PyGUI.ToolTip import ToolTipInfo

from Helpers import BWKeyBindings
from Helpers.BWKeyBindings import BWKeyBindingAction

from functools import partial
from bwdebug import *

def setWireFrameMode( terrain, object ):

	mode = {
		(False, False): 0,
		(False, True): 1,
		(True, False): 2,
		(True, True): 3	} [ (object, terrain) ]

	BigWorld.setWatcher( "Render/Wireframe Mode", mode )


def getWireFrameModes():
	currentMode = int( BigWorld.getWatcher( "Render/Wireframe Mode" ) ) % 4
	terrain = (currentMode == 1 or currentMode == 3)
	object  = (currentMode == 2 or currentMode == 3)
	return terrain, object


def toggleTerrainWireframe():
	terrain, object = getWireFrameModes()
	setWireFrameMode( not terrain, object )
	return not terrain


def toggleObjectWireframe():
	terrain, object = getWireFrameModes()
	setWireFrameMode( terrain, not object )
	return not object


def toggleConsoleState( name ):
	newState = not (BigWorld.getWatcher( "Debug/activeConsole" ) == name)
	BigWorld.setWatcher( "Debug/activeConsole", name if newState else "")
	return newState


def toggleWatcher( name ):
	curState = BigWorld.getWatcher( name )
	newState = not (curState.upper() == 'TRUE')
	BigWorld.setWatcher( name, newState )
	return newState



class ActionBar( PyGUI.Window, BWKeyBindings.BWActionHandler ):

	factoryString = "FDGUI.ActionBar"

	def __init__( self, component ):
		PyGUI.Window.__init__( self, component )
		BWKeyBindings.BWActionHandler.__init__( self )
		self.component.script = self
		self.monitoredConsoles = {}
		self.__maxFlightPathWaitTime = 300	# Time in seconds. 5 minutes should be enough time.
		self.__avatarInitTime = 0
		
	def onBound( self ):
		PyGUI.Window.onBound( self )

		fdgui = FantasyDemo.rds.fdgui

		fdgui.inGameMenu.script.addListener( "activated", self.inGameMenuActivated )
		fdgui.weatherWindow.script.addListener( "activated", self.weatherWindowActivated )
		fdgui.statsWindow.script.addListener( "activated", self.networkStatsActivated )
		fdgui.inventoryWindow.script.addListener( "activated", self.inventoryWindowActivated )
		fdgui.helpWindow.script.addListener( "activated", self.helpWindowActivated )

		self.getButton( 2, "umbra" ).setToggleState( BigWorld.getWatcher( "Render/Umbra/occlusionCulling" ) )

		self.monitorConsoleState( "Python", 2, "python" )
		self.monitorConsoleState( "Watcher", 2, "watcher" )
		self.monitorConsoleState( "Statistics", 2, "fps" )
		self.monitorConsoleState( "Histogram", 2, "histogram" )

		toolTipManager = fdgui.toolTipManager
		toolTipManager.setToolTipFromAction( self.getButton( 1, "characterMenu" ), 'Character' )
		toolTipManager.setToolTipFromAction( self.getButton( 1, "equipMenu" ), 'Equipment' )
		toolTipManager.setToolTipFromAction( self.getButton( 1, "inventory" ), 'Inventory' )
		toolTipManager.setToolTipFromAction( self.getButton( 1, "weatherWindow" ), 'Weather' )
		toolTipManager.setToolTipFromAction( self.getButton( 1, "help" ), 'Help' )
		toolTipManager.setToolTipFromAction( self.getButton( 1, "networkStats" ), 'ClientServerStats' )
		toolTipManager.setToolTipFromAction( self.getButton( 1, "ingameMenu" ), 'EscapeKey' )

		toolTipManager.setToolTipFromAction( self.getButton( 2, "umbra" ), 'ToggleUmbra' )
		toolTipManager.setToolTipFromAction( self.getButton( 2, "uiDisplay" ), 'HideGUI' )
		toolTipManager.setToolTipFromAction( self.getButton( 2, "python" ), 'TogglePythonConsole' )
		toolTipManager.setToolTipFromAction( self.getButton( 2, "watcher" ), 'ToggleWatcherConsole' )
		toolTipManager.setToolTipFromAction( self.getButton( 2, "fps" ), 'ToggleStatsConsole' )
		toolTipManager.setToolTipFromAction( self.getButton( 2, "terrainWireframe" ), 'ToggleTerrainWireframe' )
		toolTipManager.setToolTipFromAction( self.getButton( 2, "objectWireframe" ), 'ToggleObjectWireframe' )
		toolTipManager.setToolTipFromAction( self.getButton( 2, "histogram" ), 'ToggleHistogram' )
		toolTipManager.setToolTipFromAction( self.getButton( 2, "cellBounds" ), 'CellBoundaryVisualisation' )
		toolTipManager.setToolTipFromAction( self.getButton( 2, "flyThrough" ), 'ToggleFlyThroughMode' )

		# Tooltips can also be done manual, so in this code:
		#umbraButton = self.getButton( 2, "umbra" )
		#toolTipInfo = ToolTipInfo( umbraButton.component, "tooltip3line",
		#	{'title':'Umbra', 'line1':'umbra is used', 'line2':'to make the game', 'line3':'FASTER!', 'shortcut': '!!'}  )
		#umbraButton.setToolTipInfo( toolTipInfo )


	def active( self, state ):
		if state == True:
			FantasyDemo.rds.keyBindings.addHandler( self )
		else:
			FantasyDemo.rds.keyBindings.removeHandler( self )
		PyGUI.Window.active( self, state )


	def avatarInit( self, avatar ):
		avatar.addListener( "cellBoundsEnabled", self.cellBoundsEnabled )
		self.__avatarInitTime = BigWorld.time()
		self._checkFlyThrough()
		
		
	def _checkFlyThrough( self ):
		if FantasyDemo.rds.isFlightPathLoaded():
			#DEBUG_MSG( "Flight path has completed loading, enabling flyThrough button." )
			self.getButton( 2, "flyThrough" ).setDisabledState( 0 )
		else:
			self.getButton( 2, "flyThrough" ).setDisabledState( 1 )
			timeDiff = BigWorld.time() - self.__avatarInitTime
			if timeDiff < self.__maxFlightPathWaitTime:
				BigWorld.callback( 5, self._checkFlyThrough )
			else:
				#DEBUG_MSG( "Flight path failed to load within %s seconds." % 
				#			self.__maxFlightPathWaitTime )
				pass
				
	# Group 1 button event handlers
	@PyGUIEvent( "group1.characterMenuButton", "onClick" )
	def characterMenuButtonClicked( self ):
		FantasyDemo.rds.keyBindings.callActionByName( 'Character' )


	@PyGUIEvent( "group1.equipMenuButton", "onClick" )
	def equipMenuButtonClicked( self ):
		FantasyDemo.rds.keyBindings.callActionByName( 'Equipment' )


	@PyGUIEvent( "group1.inventoryButton", "onClick" )
	def inventoryButtonClicked( self ):
		FantasyDemo.rds.keyBindings.callActionByName( 'Inventory' )


	@PyGUIEvent( "group1.weatherWindowButton", "onClick" )
	def weatherMenuButtonClicked( self ):
		FantasyDemo.rds.keyBindings.callActionByName( 'Weather' )


	@PyGUIEvent( "group1.networkStatsButton", "onClick" )
	def networkStatsButtonClicked( self ):
		FantasyDemo.rds.keyBindings.callActionByName( 'ClientServerStats' )


	@PyGUIEvent( "group1.helpButton", "onClick" )
	def helpButtonClicked( self ):
		FantasyDemo.rds.keyBindings.callActionByName( 'Help' )


	@PyGUIEvent( "group1.ingameMenuButton", "onClick" )
	def inGameMenuButtonClicked( self ):
		FantasyDemo.rds.keyBindings.callActionByName( 'InGameMenu' )


	#
	# Group 2 button event handlers
	@BWKeyBindingAction( "ToggleUmbra" )
	@PyGUIEvent( "group2.umbraButton", "onClick" )
	def umbraButtonClicked( self, isDown=True ):
		if isDown:
			newState = toggleWatcher( "Render/Umbra/occlusionCulling" )
			self.getButton( 2, "umbra" ).setToggleState( newState )
			if newState:
				FantasyDemo.addChatMsg( -1, "Umbra occlusion culling enabled" )
			else:
				FantasyDemo.addChatMsg( -1, "Umbra occlusion culling disabled" )


	@PyGUIEvent( "group2.uiDisplayButton", "onClick" )
	def uiDisplayButtonClicked( self ):
		FantasyDemo.rds.keyBindings.callActionByName( 'HideGUI' )


	@BWKeyBindingAction( "TogglePythonConsole" )
	@PyGUIEvent( "group2.pythonButton", "onClick" )
	def pythonButtonClicked( self, isDown=True ):
		if isDown:
			newState = toggleConsoleState( "Python" )
			self.getButton( 2, "python" ).setToggleState( newState )


	@BWKeyBindingAction( "ToggleWatcherConsole" )
	@PyGUIEvent( "group2.watcherButton", "onClick" )
	def watcherButtonClicked( self, isDown=True ):
		if isDown:
			newState = toggleConsoleState( "Watcher" )
			self.getButton( 2, "watcher" ).setToggleState( newState )


	@BWKeyBindingAction( "ToggleStatsConsole" )
	@PyGUIEvent( "group2.fpsButton", "onClick" )
	def fpsButtonClicked( self, isDown=True ):
		if isDown:
			newState = toggleConsoleState( "Statistics" )
			self.getButton( 2, "fps" ).setToggleState( newState )


	@BWKeyBindingAction( "ToggleHistogram" )
	@PyGUIEvent( "group2.histogramButton", "onClick" )
	def histogramButtonClicked( self, isDown=True ):
		if isDown:
			newState = toggleConsoleState( "Histogram" )
			self.getButton( 2, "histogram" ).setToggleState( newState )


	@BWKeyBindingAction( "ToggleTerrainWireframe" )
	@PyGUIEvent( "group2.terrainWireframeButton", "onClick" )
	def terrainWireframeButtonClicked( self, isDown=True ):
		if isDown:
			newState = toggleTerrainWireframe()
			self.getButton( 2, "terrainWireframe" ).setToggleState( newState )
			if newState:
				FantasyDemo.addChatMsg( -1, "Terrain wireframe mode enabled" )
			else:
				FantasyDemo.addChatMsg( -1, "Terrain wireframe mode disabled" )


	@BWKeyBindingAction( "ToggleObjectWireframe" )
	@PyGUIEvent( "group2.objectWireframeButton", "onClick" )
	def objectWireframeButtonClicked( self, isDown=True ):
		if isDown:
			newState = toggleObjectWireframe()
			self.getButton( 2, "objectWireframe" ).setToggleState( newState )
			if newState:
				FantasyDemo.addChatMsg( -1, "Object wireframe mode enabled" )
			else:
				FantasyDemo.addChatMsg( -1, "Object wireframe mode disabled" )


	@PyGUIEvent( "group2.cellBoundsButton", "onClick" )
	def cellBoundsButtonClicked( self ):
		FantasyDemo.rds.keyBindings.callActionByName( 'CellBoundaryVisualisation' )


	@BWKeyBindingAction( "ToggleFlyThroughMode" )
	@PyGUIEvent( "group2.flyThroughButton", "onClick" )
	def flyThroughButtonClicked( self, isDown=True ):
		if isDown:
			newState = FantasyDemo.rds.toggleFlyThroughMode()
			self.getButton( 2, "flyThrough" ).setToggleState( newState )


	#
	# Listener events
	def inGameMenuActivated( self, activated ):
		self.getButton( 1, "ingameMenu" ).setToggleState( activated )

	def weatherWindowActivated( self, activated ):
		self.getButton( 1, "weatherWindow" ).setToggleState( activated )

	def networkStatsActivated( self, activated ):
		self.getButton( 1, "networkStats" ).setToggleState( activated )

	def inventoryWindowActivated( self, activated ):
		self.getButton( 1, "inventory" ).setToggleState( activated )

	def helpWindowActivated( self, activated ):
		self.getButton( 1, "help" ).setToggleState( activated )

	def cellBoundsEnabled( self, activated ):
		self.getButton( 2, "cellBounds" ).setToggleState( activated )



	#
	# Misc utility methods
	def getButton( self, group, name ):
		group = getattr( self.component, "group" + str(group) )
		button = getattr( group, name + "Button" )
		return button.script


	def monitorConsoleState( self, consoleName, group, buttonName ):
		self.monitoredConsoles[ consoleName ] = self.getButton( group, buttonName )

		if len(self.monitoredConsoles) == 1:
			BigWorld.callback( 0.25, self._checkConsoles )


	def _checkConsoles( self ):

		activeConsole = BigWorld.getWatcher( "Debug/activeConsole" )

		# Set the current button toggle states for all buttons that
		# manipulate the active console.
		for consoleName, button in self.monitoredConsoles.iteritems():
			button.setToggleState( consoleName == activeConsole )

		# Keep checking while we still have consoles
		if len(self.monitoredConsoles) > 0:
			BigWorld.callback( 0.25, self._checkConsoles )


