import BigWorld
import FantasyDemo
from ActionBar import ActionBar
from CharStats import CharStats
from InGameMenu import InGameMenu
from InventoryWindow import InventoryWindow, InventorySlot, DraggedItem, ItemDropRegion
from HelpWindow import HelpWindow
from StatsWindow import StatsWindow
from TraderWindow import TraderWindow
from FDToolTip import FDGUIOneLineToolTip
from FDToolTip import FDToolTipManager
from WeatherWindow import WeatherWindow
from Helpers import BWKeyBindings
from Helpers.BWKeyBindings import BWKeyBindingAction
import Minimap
from SmallMinimap import SmallMinimap
from LargeMinimap import LargeMinimap
from Minimap import MinimapWindow
from ChatConsole import ChatConsole

import Helpers.PyGUI as PyGUI

import BigWorld
import GUI
import Cursor
import Info
from functools import partial
from bwdebug import ERROR_MSG, INFO_MSG, WARNING_MSG


MINIMUM_RES = (1280, 1024)

# Defining the Z ordering for all the elements so they can be ordered properly.
# Rear to front:
Z_ORDER_DROP_REGION = 0.9
Z_ORDER_COMBAT_TARGET = 0.85
Z_ORDER_INTERACTION_ICON = 0.84
Z_ORDER_SMALLMINIMAP_MAP = 0.81
Z_ORDER_SMALLMINIMAP_FRAME = 0.8
Z_ORDER_CHAR_STATS = 0.7
Z_ORDER_ACTION_BAR = 0.6
Z_ORDER_REAR_WINDOW = 0.5
Z_ORDER_WINDOW_LIMIT = 0.4
Z_ORDER_INFO = 0.3
Z_ORDER_LARGEMINIMAP_MAP = 0.21
Z_ORDER_LARGEMINIMAP_FRAME = 0.2
Z_ORDER_INGAME_MENU = 0.1
Z_ORDER_BINOCULARS = 0.09
Z_ORDER_TOOLTIP = 0.05
Z_ORDER_CHAT_BACKGROUND = 0.03
Z_ORDER_CHAT_CONSOLE = 0.02
Z_ORDER_LATENCY = 0.01


IS_HUD = 0
IS_WINDOW = 1
IS_NON_WINDOW = 2
IS_SPECIAL = 3
INITIALLY_VISIBLE = True
INITIALLY_INVISIBLE = False

NO_PIXEL_SNAP = False
PIXEL_SNAP = True

FDGUI_COMPONENTS = (
	("inGameMenu", 		"gui/ingame_menu.gui",		INITIALLY_INVISIBLE,	IS_NON_WINDOW,	Z_ORDER_INGAME_MENU),
	("weatherWindow", 	"gui/weather_window.gui",	INITIALLY_INVISIBLE,	IS_WINDOW,		Z_ORDER_REAR_WINDOW),
	("statsWindow", 	"gui/stats_window.gui", 	INITIALLY_INVISIBLE,	IS_WINDOW,		Z_ORDER_REAR_WINDOW),
	("helpWindow", 		"gui/help_window.gui", 		INITIALLY_INVISIBLE,	IS_WINDOW,		Z_ORDER_REAR_WINDOW),
	("inventoryWindow", "gui/inventory_window.gui",	INITIALLY_INVISIBLE,	IS_WINDOW,		Z_ORDER_REAR_WINDOW),
	("traderWindow", 	"gui/trader_window.gui",	INITIALLY_INVISIBLE,	IS_WINDOW,		Z_ORDER_REAR_WINDOW),
	("actionBar", 		"gui/action_bar.gui",		INITIALLY_VISIBLE,		IS_NON_WINDOW,	Z_ORDER_ACTION_BAR),
	("charStats", 		"gui/char_stats.gui",		INITIALLY_VISIBLE,		IS_NON_WINDOW,	Z_ORDER_CHAR_STATS),
	("minimap", 		"gui/minimap.gui",			INITIALLY_VISIBLE,		IS_NON_WINDOW,	Z_ORDER_SMALLMINIMAP_MAP),
	("gammaGui", 		"gui/gamma.gui",			INITIALLY_INVISIBLE,	IS_WINDOW,		Z_ORDER_REAR_WINDOW),
	("targetGui", 		"gui/target.gui",			INITIALLY_VISIBLE,		IS_HUD,			Z_ORDER_COMBAT_TARGET),
	("binocularGui", 	"gui/binocular.gui",		INITIALLY_INVISIBLE,	IS_SPECIAL,		Z_ORDER_BINOCULARS),
)


RESOLUTION_BRACKETS = (
	{
		'name': 'laptop_16:9',
		'exact': (1280, 768),
		'resolutionOverride': (1680, 1050),
		'filterTypeMappings': {
			'POINT': 'LINEAR'
		},
		'fontAliases': {
			'Label.font': 	('Label_small.font',	NO_PIXEL_SNAP),
			'Heading.font': ('Heading_small.font',	NO_PIXEL_SNAP),
		},
	},

	{
		'name': 'laptop_16:10',
		'exact': (1280, 720),
		'resolutionOverride': (1680, 945),
		'filterTypeMappings': {
			'POINT': 'LINEAR'
		},
		'fontAliases': {
			'Label.font': 	('Label_small.font',	NO_PIXEL_SNAP),
			'Heading.font': ('Heading_small.font',	NO_PIXEL_SNAP),
		},
	},

	{
		'name': 'low',
		#'min': (0,0),
		'max': (1024,768),
		'resolutionOverride': (1280, 1024),
		'filterTypeMappings': {
			'POINT': 'LINEAR'
		},
		'fontAliases': {
			'Label.font': 	('Label_small.font',	NO_PIXEL_SNAP),
			'Heading.font': ('Heading_small.font',	NO_PIXEL_SNAP),
		},
	},

	{
		'name': 'high',
		'min': (1280, 1024),
		#'max': (inf, inf),
	},
)

def getResBracket( size ):
	width = size[0]
	height = size[1]

	for bracket in RESOLUTION_BRACKETS:

		if bracket.has_key( 'exact' ):
			res = bracket[ 'exact' ]
			if res[0] == width and res[1] == height:
				return bracket
		else:
			min = bracket.get( 'min', (0,0) )
			max = bracket.get( 'max', (99999,99999) )

			if height >= width and width >= min[0] and width <= max[0] or \
			   width > height and height >= min[1] and height <= max[1]:
				return bracket

	return None


class FDGUI( BWKeyBindings.BWActionHandler ):

	def __init__( self ):
		BWKeyBindings.BWActionHandler.__init__( self )

		self.windows = dict()
		self.openWindowsOrder = []
		self._root = None
		self.filterConvertedComponents = []
		self.aliasedFontComponents = []
		self.bracket = None


	def setupGUI( self, actionToolTipsSection, keyBindings ):
		# All FDGUI elements are children of an invisible simple GUI component.
		# This allows us to easily toggle visibility of the HUD, as well as
		# control the overall sorted Z position of the hud relative to non-HUD
		# components.
		self._root = GUI.Simple("")
		self._root.script = PyGUI.PyGUIBase( self._root )
		self._root.size = (2,2)
		self._root.visible = False
		GUI.addRoot( self._root )
		self._root.visible = False

		self.chatWindow = GUI.load( "gui/chat_window.gui" )
		self.chatWindow.script.setZOrders( Z_ORDER_CHAT_BACKGROUND, Z_ORDER_CHAT_CONSOLE )

		self.toolTipManager = FDToolTipManager( self._root, Z_ORDER_TOOLTIP )
		self.toolTipManager.readInActionToolTips( actionToolTipsSection )
		self.toolTipManager.addKeyboardShortcutsToActionToolTips( keyBindings )

		for name, filename, initiallyVisible, hudType, zorder in FDGUI_COMPONENTS:
			component = GUI.load( filename )
			if not component:
				ERROR_MSG( "Error loading FDGUI component '%s' from '%s'" % (name, filename) )
				continue

			setattr( self, name, component )
			component.position.z = zorder
			if component.script:
				if hudType == IS_WINDOW:
					self.setupWindowListeners( component )
				if hudType != IS_SPECIAL:
					component.script.parent = self._root
			if initiallyVisible:
				component.script.active( True )
				#self._root.addChild( component, name )
			if hudType == IS_WINDOW:
				self.windows[ name ] = component

		self.dropRegion = GUI.load( "gui/item_drop_region.gui" )
		self.dropRegion.position.z = Z_ORDER_DROP_REGION
		self.dropRegion.script.parent = self._root
		self.dropRegion.script.active( True )

		self.interactionGui = GUI.Simple( "" )
		self.interactionGui.width = 0 # to stop it displaying wierd textures
		self.interactionGui.position.z = Z_ORDER_INTERACTION_ICON
		self._root.interactionGui = self.interactionGui

		self.latencyGui = GUI.Latency()
		self.latencyGui.label.position = ( -0.8, 0.90, Z_ORDER_LATENCY )
		GUI.addRoot( self.latencyGui )
		self.latencyGui.visible = False

		FantasyDemo.rds.keyBindings.addHandler( self )
		FantasyDemo.addDeviceListener( self )


	def fini( self ):

		self.filterConvertedComponents = None

		self.chatWindow.script.fini()
		self.inGameMenu = None
		for window in self.windows.values():
			window.script.active( False )
		self.windows = None
		self.dropRegion.script.active( False )
		self.dropRegion = False
		FantasyDemo.rds.keyBindings.removeHandler( self )


	def onPlayerAvatarEnterWorld( self, avatar ):
		for c in [ x[1] for x in self._root.children ]:
			if hasattr( c.script, "avatarInit" ):
				c.script.avatarInit( avatar )

		self._root.visible = True
		self.latencyGui.visible = True


	def onPlayerAvatarLeaveWorld( self, avatar ):
		for c in [ x[1] for x in self._root.children ]:
			if hasattr( c.script, "avatarFini" ):
				c.script.avatarFini( avatar )

		self._root.visible = False
		self.latencyGui.visible = False


	def setVisible( self, visible ):
		self._root.visible = visible
		GUI.mcursor().visible = visible

	def getVisible( self ):
		return self._root.visible

	visible = property( getVisible, setVisible )


	def addChild( self, component ):
		self._root.addChild( component )

	def delChild( self, component ):
		self._root.delChild( component )


	def windowClicked( self, window ):
		if window in self.openWindowsOrder:
			self.bringWindowToFront( window )


	def windowActivated( self, window, activated ):
		if activated:
			if window not in self.openWindowsOrder:
				self.openWindowsOrder.append( window )
			self.bringWindowToFront( window )
		else:
			if window  in self.openWindowsOrder:
				self.openWindowsOrder.remove( window )


	def bringWindowToFront( self, window ):
		if window not in self.openWindowsOrder:
			ERROR_MSG( "Attempting to bring hidden window to front", window )
			return

		self.openWindowsOrder.remove( window )
		self.openWindowsOrder.append( window )

		zposition = Z_ORDER_REAR_WINDOW
		increment = (Z_ORDER_WINDOW_LIMIT - Z_ORDER_REAR_WINDOW) / len(self.openWindowsOrder)
		for window in self.openWindowsOrder:
			window.position.z = zposition
			zposition += increment

		GUI.reSort()


	def setupWindowListeners( self, window ):
		window.script.addListener( "activated", partial( self.windowActivated, window ) )
		window.script.addListener( "windowClicked", partial( self.windowClicked, window ) )
		window.script.addListener( "onBeginDrag", partial( self.windowClicked, window ) )


	def onRecreateDevice( self ):
		self.chooseResolutionBracket()


	def chooseResolutionBracket( self ):
		self.bracket = getResBracket( BigWorld.screenSize() )

		if self.bracket is None:
			self.bracket = dict( RESOLUTION_BRACKETS[-1] )
			#WARNING_MSG( 'Failed to select appropriate resolution bracket for %dx%d.' %
			#			(BigWorld.screenWidth(), BigWorld.screenHeight()) )
		else:
			self.bracket = dict(self.bracket) # make a copy

		#INFO_MSG( 'Using resolution bracket %s.' % (self.bracket['name']) )

		fullscreen = not BigWorld.isVideoWindowed()
		fsAspect = BigWorld.getFullScreenAspectRatio()
		actualAspect = BigWorld.screenWidth()/BigWorld.screenHeight()
		resolutionOverride = self.bracket.get( 'resolutionOverride', None )

		if fullscreen:
			# We're in fullscreen mode. If the full screen aspect differs from the actual aspect, then
			# setup a resolution override that adjusts for this discrepancy.
			if abs(actualAspect - fsAspect) > 0.0001:
				#WARNING_MSG( "Adjusting full screen UI due to difference between actual aspect and fullscreen aspect." )
				if resolutionOverride is not None:
					height = resolutionOverride[1]
				else:
					height = BigWorld.screenHeight()
				resolutionOverride = (height*fsAspect, height)
			elif resolutionOverride is not None:
				# If we're at the correct fullscreen aspect ratio for this resolution, but we have a resolution
				# override which is wrong for this resolution, then adjust.
				overrideAspect = float(resolutionOverride[0])/float(resolutionOverride[1])
				if abs(overrideAspect - actualAspect) > 0.0001:
					#WARNING_MSG( "Adjusting fullscreen resolution %s for different aspects (%f, %f)." %
					#			(repr(resolutionOverride), actualAspect, overrideAspect) )

					if BigWorld.screenWidth() > BigWorld.screenHeight():
						resolutionOverride = (resolutionOverride[1]*actualAspect, resolutionOverride[1])
					else:
						resolutionOverride = (resolutionOverride[0], resolutionOverride[0]/actualAspect)

		else:
			# We're in windowed mode. If there is a resolution override, and we have been scaled into
			# a different aspect ratio than the override, adjust the override so we don't get
			# a squished UI (we don't do anything if there isnt an override because we'd be at
			# 1-1 pixel mapping anyway).
			if resolutionOverride is not None:
				overrideAspect = float(resolutionOverride[0])/float(resolutionOverride[1])
				if abs(actualAspect - overrideAspect) > 0.0001:
					#WARNING_MSG( "Adjusting windowed resolution override %s for different aspects (%f, %f)." %
					#			(repr(resolutionOverride), actualAspect, overrideAspect) )

					if BigWorld.screenWidth() > BigWorld.screenHeight():
						resolutionOverride = (resolutionOverride[1]*actualAspect, resolutionOverride[1])
					else:
						resolutionOverride = (resolutionOverride[0], resolutionOverride[0]/actualAspect)


		if resolutionOverride is not None:
			GUI.setResolutionOverride( resolutionOverride )
		else:
			GUI.setResolutionOverride( (0,0) )

		self.setupFilterTypes()
		self.setupFonts()
 		self.chatWindow.script.onRecreateDevice()


	def setupFilterTypes( self ):

		# Restore original filter types
		for component in self.filterConvertedComponents:
			component[0].filterType = component[1]

		self.filterConvertedComponents = []

		self.setupFilterTypesInternal( self._root )
		self.setupFilterTypesInternal( self.minimap.m.script.smallMinimap )
		self.setupFilterTypesInternal( self.minimap.m.script.largeMinimap )
		for c in FDGUI_COMPONENTS:
			self.setupFilterTypesInternal( getattr( self, c[0] ) )


 	def setupFilterTypesInternal( self, component ):
 		ft = str(component.filterType)
 		mappings = self.bracket.get( 'filterTypeMappings', {} )

 		if type(component) is not GUI.Text and ft in mappings:
 			component.filterType = mappings[ft]
 			self.filterConvertedComponents.append( (component, ft) )

 		for child in component.children:
			self.setupFilterTypesInternal( child[1] )


 	def setupFonts( self ):

 		# First restore to original fonts of any previously aliased components.
 		for component in self.aliasedFontComponents:
 			component[0].font = component[1]
 			component[0].pixelSnap = component[2]

 		self.aliasedFontComponents = []

 		# Set the pygui text styles
 		fontAliases = self.bracket.get( 'fontAliases', {} )
 		PyGUI.TextStyles.fontAliases = dict( [ (key, value[0]) for (key, value) in fontAliases.iteritems() ] )

 		# Go through and find text components
 		self.setupFontsInternal( self._root )
 		self.setupFontsInternal( self.minimap.m.script.smallMinimap )
		self.setupFontsInternal( self.minimap.m.script.largeMinimap )
 		for c in FDGUI_COMPONENTS:
			self.setupFontsInternal( getattr( self, c[0] ) )
		
		# Go through tool tips and update
		for component in self.toolTipManager.toolTipGUIs.values():
			self.setupFontsInternal( component )


 	def setupFontsInternal( self, component ):
 		if self.bracket is None:
 			return

 		fontAliases = self.bracket.get( 'fontAliases', {} )

 		if type(component) is GUI.Text:
 			curFontName = str(component.font)
 			if curFontName in fontAliases:
				alias = fontAliases[ curFontName ]
				component.font = alias[0]
				pixelSnap = component.pixelSnap
				component.pixelSnap = alias[1]

				# Remember this component so we can restore original font
				self.aliasedFontComponents.append( (component, curFontName, pixelSnap) )


 		for child in component.children:
			self.setupFontsInternal( child[1] )



 	def _componentAdded( self, component ):
 		self.setupFilterTypesInternal( component )
 		self.setupFontsInternal( component )


 	def isScaling( self ):
 		return self.bracket is not None and self.bracket.has_key( 'resolutionOverride' )

	@BWKeyBindingAction( "Character" )
	def toggleCharacter( self, isDown=True ):
		pass


	@BWKeyBindingAction( "Equipment" )
	def toggleEquipment( self, isDown=True ):
		pass


	@BWKeyBindingAction( "Inventory" )
	def toggleInventory( self, isDown=True ):
		if isDown:
			self.inventoryWindow.script.toggleActive()


	@BWKeyBindingAction( "Weather" )
	def toggleWeather( self, isDown=True ):
		if isDown:
			self.weatherWindow.script.toggleActive()


	@BWKeyBindingAction( "Help" )
	def toggleHelp( self, isDown=True ):
		if isDown:
			self.helpWindow.script.toggleActive()


	@BWKeyBindingAction( "ClientServerStats" )
	def toggleClientServerStats( self, isDown=True ):
		if isDown:
			self.statsWindow.script.toggleActive()

	@BWKeyBindingAction( "InGameMenu" )
	def toggleInGameMenu( self, isDown=True ):
		if isDown:
			self.inGameMenu.script.toggleActive()


	@BWKeyBindingAction( "HideGUI" )
	def toggleHideGUI( self, isDown=True ):
		if isDown:
			if self.binocularGui.script.isActive:
				# When hiding the GUI for screen shots we don't want to hide the
				# binoculars gui, as that's what the screen shot would be of.
				# But hide (or show) the latency label anyway.
				self.latencyGui.visible = not self.latencyGui.visible

			elif self.visible:
				self.chatWindow.script.addMsg( 'Press Esc to show the GUI again.' , 3 )
				self.chatWindow.script.hideLater( 2 )
				self.visible = False
				self.latencyGui.visible = False
				Info.setVisibilityOfAllInfoEntities( False )
			else:
				self.visible = True
				self.latencyGui.visible = True
				Info.setVisibilityOfAllInfoEntities( True )


	@BWKeyBindingAction( "GammaGui" )
	def toggleGammaGui(self, isDown):
		if isDown:
			self.gammaGui.script.toggleActive()


	@BWKeyBindingAction( "EscapeKey" )
	def handleEscapeKey( self, isDown=True ):
		if not isDown:
			return False

		if not self.visible:
			self.toggleHideGUI()
			return True

		if self.chatWindow.script.component.visible:
			self.chatWindow.script.hideNow()
			return True

		# This closes all open windows before opening the in-game menu.
		#if self.inGameMenu.script.isActive:
		#	self.toggleInGameMenu()
		#elif not self.hideAllWindows():
		#	self.toggleInGameMenu()

		# This simply toggles the in-game menu without first closing windows.
		self.toggleInGameMenu()

		return True


	def showBinoculars( self, show ):
		self._root.visible = not show
		self.binocularGui.script.active( show )


	def hideAllWindows( self ):

		# Note: this doesn't include the in-game menu
		windowsActive = False
		for windowComponent in self.windows.itervalues():
			if windowComponent.script.isActive:
				windowComponent.script.active( False )
				windowsActive = True

		return windowsActive


	def handleDisconnectionFromServer( self ):
		# Hide all in-game UI's that may be visible.
		self.inGameMenu.script.active( False )


	#---------------------------------------------------------------------------
	#
	# Interaction Icon Information
	#

	# Action IDs or AIDs
	AID_Shonk			= 1
	AID_ShonkPaper		= 2
	AID_ShonkScissors	= 3
	AID_ShonkRock		= 4
	AID_Handshake		= 5
	AID_BunkUp			= 6
	AID_LiftUp			= 7
	AID_NarrowTarget	= 8
	AID_JoinGroup		= 9
	AID_Throw			= 10
	AID_Catch			= 11

	#	Icon Maps:
	interactionIcons = {
		AID_Shonk			: "gui/maps/gui_shonk.tga",
		AID_ShonkPaper		: "gui/maps/gui_shonk_paper.tga",
		AID_ShonkScissors	: "gui/maps/gui_shonk_scissors.tga",
		AID_ShonkRock		: "gui/maps/gui_shonk_rock.tga",
		AID_Handshake		: "gui/maps/gui_shake.tga",
		AID_BunkUp			: "gui/maps/gui_bunkup.tga",
		AID_LiftUp			: "gui/maps/gui_liftup.tga",
		AID_NarrowTarget	: "gui/maps/alert_target.tga",
		AID_JoinGroup		: "gui/maps/gui_askjointeam.tga",
		AID_Throw			: "gui/maps/gui_askthrow.tga",
		AID_Catch			: "gui/maps/gui_drop.tga",
	}

	#	Icon Angles: Usually 180 or 0
	interactionIconAngles = {
		AID_Shonk			: 0.0,
		AID_ShonkPaper		: 0.0,
		AID_ShonkScissors	: 0.0,
		AID_ShonkRock		: 0.0,
		AID_Handshake		: 0.0,
		AID_BunkUp			: 0.0,
		AID_LiftUp			: 0.0,
		AID_NarrowTarget	: 0.0,
		AID_JoinGroup		: 0.0,
		AID_Throw			: 0.0,
		AID_Catch			: 0.0,
	}

	#	Icon Colours: R/G/B/Alpha (values 0-255)
	interactionIconColours = {
		AID_Shonk			: (  64, 255, 64, 220 ),
		AID_ShonkPaper		: (  64, 255, 64, 220 ),
		AID_ShonkScissors	: (  64, 255, 64, 220 ),
		AID_ShonkRock		: (  64, 255, 64, 220 ),
		AID_Handshake		: (  64, 255, 64, 220 ),
		AID_BunkUp			: (  64, 255, 64, 220 ),
		AID_LiftUp			: (  64, 255, 64, 220 ),
		AID_NarrowTarget	: (  64, 255, 64, 220 ),
		AID_JoinGroup		: (  64, 255, 64, 220 ),
		AID_Throw			: (  64, 255, 64, 220 ),
		AID_Catch			: (  64, 255, 64, 220 ),
	}

	def setInteractionIcon( self, entity, iconID = None ):
		if entity.overheadGui != None:
			if entity.overheadIcon != None:
				entity.overheadGui.delChild( entity.overheadIcon )
				entity.overheadIcon = None
			self.interactionGui.delChild( entity.overheadGui )
			entity.overheadGui.source = None
			entity.overheadGui = None

		if iconID != None:
			# Set up the bounding box GUI for the entity.
			entity.overheadGui = GUI.BoundingBox( "" )
			entity.overheadGui.absoluteSubspace = 2

			entity.overheadGui.source = entity.model.bounds
			entity.overheadGui.colour = ( 128, 128, 128, 255 )
			self.interactionGui.addChild( entity.overheadGui )

			# Set up the entity's icon.
			entity.overheadIcon = GUI.Simple( FDGUI.interactionIcons[ iconID ] )
			# set the dimensions as a percentage of half the screen height and width
			entity.overheadIcon.width = 0.15
			entity.overheadIcon.height = 0.15
			entity.overheadIcon.angle = FDGUI.interactionIconAngles[ iconID ]
			entity.overheadIcon.colour = FDGUI.interactionIconColours[ iconID ]
			entity.overheadIcon.position = ( 0.5, 1.05, 1 )
			entity.overheadIcon.horizontalAnchor = "CENTER"
			entity.overheadIcon.verticalAnchor = "BOTTOM"
			entity.overheadIcon.visible = 1
			entity.overheadGui.addChild( entity.overheadIcon )


