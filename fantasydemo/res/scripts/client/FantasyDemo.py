# --------------------------------------------------------------------------
# This is an Application Personality Script.  It contains classes to control
# and maintain various user interface components, such as the Direction
# Cursor settings and the console, followed by a small number of
# miscellaneous helper functions.  Finally a series of BigWorld Client
# callback functions are implemented that allow the game's 'personality' to
# be configured, executed and terminated.  These are the main methods to
# interact with the BigWorld Client engine.
# --------------------------------------------------------------------------

import time
import BigWorld
from Math import *
import math
from functools import partial
from Keys import *
import GUI
import types
import ResMgr
import os
import Account
import Avatar
from GraphicsPresets import GraphicsPresets
from Helpers import PyGUI
__import__('__main__').PyGUI = PyGUI
import FDGUI
__import__('__main__').FDGUI = FDGUI
import MainMenuGUI
__import__('__main__').MainMenuGUI = MainMenuGUI
import weakref
import MenuScreenSpace
import MenuScreenAvatar
import AvatarModel
import PlayerModel
from Helpers.BWCoroutine import *
from Helpers import BWKeyBindings
from Helpers import Region
from bwdebug import *
import CameraNode
import WeatherSystem


############################################################################
# The following classes implement various aspects of the user interface.   #
# They are used internal to this script.  Neither BigWorld Components, nor #
# any other script needs to make use of them.                              #
############################################################################

MENU_ENTRIES = {
	'MAINMENU'   : (
		'Main Menu',
		'gui/maps/main_title_main.tga',
		'gui/maps/main_help_main.tga'),
	'LANSERVERS' : (
		'Search for Servers on Local Network',
		'gui/maps/main_title_lan.tga',
		'gui/maps/main_help_menu.tga'),
	'CHARACTERSELECT'   : (
		'Select Character',
		'gui/maps/main_title_character_select.tga',
		'gui/maps/main_help_menu.tga'),
	'CHARACTERCREATE'   : (
		'Select Character',
		'gui/maps/main_title_character_create.tga',
		'gui/maps/main_help_char_create.tga'),
	'XMLSERVERS' : (
		'Connect to Standard Server',
		'gui/maps/main_title_servers.tga',
		'gui/maps/main_help_menu.tga'),
	'OFFLSPACES' : (
		'Explore Space Offline',
		'gui/maps/main_title_offline.tga',
		'gui/maps/main_help_menu.tga'),
	'SETTINGS' : (
		'Change Display Settings',
		'gui/maps/main_title_display.tga',
		'gui/maps/main_help_menu.tga'),
	'RESTART' : ('Restart Client', '', ''),
	'QUITGAME'   : ('Quit Game', '', '') }

HELP_EDIT        = 'gui/maps/main_help_edit.tga'
MAX_ERROR_LEN    = 19

FIRST_PERSON_NEAR_CLIP_PLANE = 0.15


# --------------------------------------------------------------------------
# Class:  DCSettings
# Description:
#	- Reads and stores direction cursor settings.
# --------------------------------------------------------------------------
class DCSettings:

	# --------------------------------------------------------------------------
	# Method:  __init__
	# Description:
	#	- Initialises all required attributes.
	# --------------------------------------------------------------------------
	def __init__(self):
		self.invertVerticalMovement = 0
		self.mouseSensitivity = 0
		self.mouseHVBias = 0
		self.maxPitch = 0
		self.minPitch = 0

	# -------------------------------------------------------------------------
	# Method:  load
	# Description:
	#	- Reads data taken from the BigWorld Client Configuration Script.
	# -------------------------------------------------------------------------
	def load(self, sect):
		self.invertVerticalMovement = sect.readBool('invertVerticalMovement',
													self.invertVerticalMovement)
		self.mouseSensitivity = sect.readFloat('mouseSensitivity',
											   self.mouseSensitivity)
		self.mouseHVBias = sect.readFloat('mouseHVBias', self.mouseHVBias)
		self.maxPitch = sect.readFloat('maxPitch', self.maxPitch)
		self.minPitch = sect.readFloat('minPitch', self.minPitch)

	# -------------------------------------------------------------------------
	# Method:  copy
	# Description:
	#	- Copies data from this class into another class.
	# -------------------------------------------------------------------------
	def copy(self, oth):
		self.__dict__.update(oth.__dict__)

###########################
# End of class DCSettings #
###########################



# -----------------------------------------------------------------------------
# Class: RDShare
# Description:
#	- Maintains all shared personality data.
# -----------------------------------------------------------------------------
class RDShare:

	# -------------------------------------------------------------------------
	# Method: __init__
	# Description:
	#	- Initialises shared personality data.
	# -------------------------------------------------------------------------
	def __init__(self):
		self.outsidePivotMaxDist = 0
		self.insidePivotMaxDist = 0
		self.reversePivotMaxDist = 0
		self.overridePivotMaxDist = 0

		self.useWoWMode = True
		self.mouseMoveThreshold = 5

		self.currFov = 0
		self.fovs = [60,20]

		self.fixedMatrix = Matrix()

		self.cc = None
		self.flc = None
		self.fic = None
		self.frc = None

		# Indexes by which the above 4 cameras are referred to from the outside
		self.CURSOR_CAMERA = 0
		self.FLEXI_CAM = 1
		self.FIXED_CAMERA = 2
		self.FREE_CAMERA = 3

		self.gameCamIdx = 0		# for free camera mode
		self.cameraKeyIdx = 0

		self.firstPersonDCSettings = DCSettings()
		self.thirdPersonDCSettings = DCSettings()

		self.inside = 0

		self.console = None

		self.maxBandwidth = 20000 # default of FantasyDemo

		self.spaceNameMap = {}
		self.deviceListeners = {}
		self.environmentChangeListeners = {}
		self.lastWeatherSpaceID = None
		self.cameraSpaceID = None
		self.flyThroughMode = False

		self.selfDisconnect = False
		self.__flyThroughStartNodeName = 'camera node0'


	def init( self):
		BigWorld.addWatcher('Comms/Max bandwidth per second', self.getMaxBps, self.setMaxBps)
		self.region = Region.Region()


	def fini( self ):
		BigWorld.delWatcher('Comms/Max bandwidth per second')
		self.region.fini()
		if hasattr( self, "waterListenerID" ):
			BigWorld.delWaterVolumeListener( self.waterListenerID )
		# unfortunately, we cannot have a weakref to a
		# [un]bound method. This is why we need to explicitly
		# break the cyclic references before exiting
		self.console.script.fini()
		del self.console
		self.selfDisconnect = False

	#TODO : add specific underwater graphical effects.
	def cameraWaterCallback(self, entering, volume):
		if entering == True:
			self.underwaterFogEmitter = BigWorld.addFogEmitter( (0,0,0), 10, -10, 100, 0x6060c0, False )
		else:
			BigWorld.delFogEmitter( self.underwaterFogEmitter )

	def initConsole(self):
		if self.console is None:
			# create fantasy demo console
			self.console = GUI.load("gui/fd_console.gui")
			self.console.script.active(True)

	def getMaxBps(self):
		return str(self.maxBandwidth)

	def setMaxBps(self, bps):
		self.maxBandwidth = int(bps)
		BigWorld.player().base.setBandwidthPerSecond(int(bps))

	def camera(self, idx):
		return (self.cc, self.flc, self.fic, self.frc)[ idx % 4 ]


	def baseFOV(self):
		return self.fovs[ self.currFov % len(self.fovs) ]


	def changeBaseFOV(self):
		self.currFov = self.currFov + 1
		self.currFov = self.currFov % len(self.fovs)
		self.fovs = [60,20]


	def updatePivotDist(self):
		self.cc.maxDistHalfLife = 1.5
		if self.overridePivotMaxDist > 0:
			self.cc.pivotMaxDist = self.overridePivotMaxDist
			self.cc.maxDistHalfLife = 0.15
		elif self.cc.reverseView:
			self.cc.pivotMaxDist = self.reversePivotMaxDist
		else: # m6rad changes
#		elif self.inside:
			self.cc.pivotMaxDist = self.insidePivotMaxDist
#		else:
#			self.cc.pivotMaxDist = self.outsidePivotMaxDist

	def toggleFlyThroughMode( self ):
		self.setFlyThroughMode( not self.flyThroughMode )
		return self.flyThroughMode

	def setFlyThroughMode( self, enabled ):
		if self.isFlightPathLoaded() == False:
			return
			
		if enabled:
			BigWorld.runFlyThrough( self.__flyThroughStartNodeName )
		else:
			BigWorld.cancelFlyThrough()
		self.flyThroughMode = enabled
		

	def isFlightPathLoaded( self ):
		"""
		Returns True if all the UDO CameraNodes in the flight path have finished loading, otherwise returns false.
		"""
		cameraNodes = [udo for udo in BigWorld.userDataObjects.values() if isinstance( udo, CameraNode.CameraNode )]
		startCamera = [cn for cn in cameraNodes if cn.name == self.__flyThroughStartNodeName]
		if len( startCamera ) != 1:
			return
		else:
			startCamera = startCamera[0]
		try:
			nextCamera = startCamera.next
			while True:
				if nextCamera == startCamera:
					return True
				else:
					nextCamera = nextCamera.next
		except BigWorld.UnresolvedUDORefException:
			pass
		return False

########################
# End of class RDShare #
########################


# -----------------------------------------------------------------------------
# Class: LoginInfo
# Description:
#	- Stores login information.
# -----------------------------------------------------------------------------
class LoginInfo:
	def __init__(self):
		self.username = ''
		self.password = 'a'
		self.inactivityTimeout = 60
		try:
			global rds
			self.username          = rds.userPreferences.readString('lastUsedAccountName')
			self.password          = rds.scriptsConfig._login._password.asString
			self.inactivityTimeout = rds.scriptsConfig._login._inactivityTimeout.asInt
		except:
			pass

##########################
# End of class LoginInfo #
##########################


############################################################################
# The following are miscellaneous functions/commands for internal use or   #
# use by other scripts.                                                    #
############################################################################


# -----------------------------------------------------------------------------
# Method: v4col
# Description:
#		- Helper function to turn a vector3 into a full-on vector4 colour
# -----------------------------------------------------------------------------
def v4col(v3col, alpha = 255):
	return (v3col[0], v3col[1], v3col[2], alpha)


# These commands will be executed when the script is run by BigWorld.


# Stores whether or not the use key is down
isUseKeyDown = 0


# Set the camera type. Used to be in script_bigworld.cpp
def cameraType(idx):
	global rds
	newcam = rds.camera(idx)
	newcam.set(BigWorld.camera().matrix)
	BigWorld.camera(newcam)
	if idx < 3: rds.gameCamIdx = idx


# Change to the fixed camera, and set it to the given points
def setFixedCamera(camPos, lookPos):
	global rds
	if not hasattr(camPos, 'x'):  camPos = Vector3(*camPos)
	if not hasattr(lookPos, 'x'): lookPos = Vector3(*lookPos)
	lookDir = lookPos - camPos
	lookDir.normalise()

	# could move out -1 * lookDir if we wanted no movement at all
	# in the fixed camera (-1 because of preferredPos setting)
	# like this is probably better for collision scene issues

	rds.fixedMatrix.lookAt(camPos, lookDir, (0,1,0))
	rds.fic.set(rds.fixedMatrix)

	rds.fixedMatrix.invert()
	BigWorld.camera(rds.fic)
	rds.gameCamIdx = 2


def camera(idx):
	global rds
	return rds.camera(idx)


# Change to the next camera
def nextCamera():
	global rds
	curcam = BigWorld.camera()
	if curcam == rds.cc:
		newcam = 1
	elif curcam == rds.flc:
		newcam = 2
	else:
		newcam = 0
	cameraType(newcam)


# Set free camera mode
def freeCamera(ison):
	resetCameraOffset()
	if ison:
		cameraType(3)
	else:
		cameraType(rds.gameCamIdx)


# Set first person mode
def firstPerson(ison):
	global rds

	rds.cc.firstPerson = ison

	if ison:
		dcSet = rds.firstPersonDCSettings
	else:
		dcSet = rds.thirdPersonDCSettings

	dc = BigWorld.dcursor()
	#dc.invertVerticalMovement = dcSet.invertVerticalMovement
	dc.mouseSensitivity       = dcSet.mouseSensitivity
	dc.mouseHVBias            = dcSet.mouseHVBias
	dc.maxPitch               = dcSet.maxPitch * math.pi / 180.0
	dc.minPitch               = dcSet.minPitch * math.pi / 180.0

	# stop any fov ramp in progress
	# (don't ask... app.cpp did this)
	p = BigWorld.projection()
	p.fov = p.fov


def setCursorCameraPivot(px, py, pz):
	global rds
	rds.cc.pivotPosition = (px, py, pz)


def cameraDistanceOverride(val):
	global rds
	rds.overridePivotMaxDist = val
	rds.updatePivotDist()


def cameraDistance(val):
	global rds
	rds.insidePivotMaxDist = val
	rds.updatePivotDist()


def cameraTarget(entity):
	global rds

	# Wow this function is so much easier than in C++!

	if entity == BigWorld.player():
		matrix = BigWorld.PlayerMatrix()
	else:
		matrix = entity.matrix

	rds.cc.target = matrix
	rds.flc.target = matrix


def fov(degs):
	BigWorld.projection().fov = degs * math.pi / 180.0


def changeFOV(degs, t):
	BigWorld.projection().rampFov(degs * math.pi / 180.0, t)


def initConsole():
	global rds
	rds.initConsole()


def console():
	global rds
	assert rds.console is not None
	return weakref.proxy(rds.console)


def addChatMsg(id, msg):
	global rds

	# add to system console
	if rds.console is not None and id == -1:
		rds.console.script.addMsg( msg, 3 )

	# add to chat console
	if not hasattr(rds, "fdgui") or rds.fdgui is None:
		return

	chatConsole = rds.fdgui.chatWindow
	if chatConsole:
		if id == -1:
			chatConsole.script.addMsg( msg, 3 )
		elif id == BigWorld.player().id:
			chatConsole.script.addMsg( 'you say: ' + msg, 0 )
		else:
			chatConsole.script.addMsg( getEntityName(id) + ': ' + msg, 1 )

def appendChatMsg(id, msg):
	global rds

	# add to system console
	if rds.console is not None and id == -1:
		rds.console.script.appendMsg( msg, 3 )

	# add to chat console
	if not hasattr(rds, "fdgui") or rds.fdgui is None:
		return

	chatConsole = rds.fdgui.chatWindow
	if chatConsole:
		if id == -1:
			chatConsole.script.appendMsg( msg, 3 )
		elif id == BigWorld.player().id:
			chatConsole.script.appendMsg( 'you say: ' + msg, 0 )
		else:
			chatConsole.script.appendMsg( getEntityName(id) + ': ' + msg, 1 )


def addMsg(msg, colourIndex = 3):
	addChatMsg( -1, msg )


def appendMsg(msg, colourIndex = 3):
	appendChatMsg( -1, msg )

def getEntityName(id):
	e = BigWorld.entity(id, 1)
	if not e:					# no such entity
		en = 'Nonexistent Entity'
	elif not hasattr(e, 'name'):			# no name attr
		en = e.__class__.__name__
	elif type(e.name) == types.StringType:		# it's a string attr
		en = e.name
	else:						# try as a callable attr
		try:	en = e.name()
		except:	en = '[error in entity[%d].name()]' % id
	return en


# A couple of helper functions to add and remove key bindings.
def addBindingForAction( actionName, binding ):
	rds.keyBindings.addBindingForAction( actionName, binding )
	rds.keyBindings.buildBindList()
	rds.keyBindings.writePreferenceKeyBindings( rds.userPreferences )
	BigWorld.savePreferences()


def removeBindingForAction( actionName, binding ):
	rds.keyBindings.removeBindingForAction( actionName, binding )
	rds.keyBindings.buildBindList()
	rds.keyBindings.writePreferenceKeyBindings( rds.userPreferences )
	BigWorld.savePreferences()



############################################################################
# The following functions implement the callbacks that BigWorld uses to    #
# initiate and maintain an application's 'personality'.                    #
############################################################################

# -----------------------------------------------------------------------------
# Method: init
# Description:
#	- The init function is called as part of the BigWorld Client
#	initialisation process.
#	- It receives the configuration script in a parsable format.
#	- This is the best place to configure all the application-specific
#		components, like initial Camera view, etc...
#	- init() creates a BigWorld Space and adds the parsed universe to it.
#	- It then creates a camera, configuring it using the values from the
#		appropriate xml data section.
#	- It also creates the Console class, again using the xml data.
# -----------------------------------------------------------------------------
def init(scriptsConfig, engineConfig, userPreferences, loadingScreenGUI = None):
	global rds

	rds.userPreferences = userPreferences

	rds.middleMouseButtonDown = False
	rds.cameraCloseUpTrigger = 0.65

	rds.scriptsConfig = scriptsConfig
	rds.clientSpace = None
	rds.clientSpaceMapping = None

	rds.loadingScreen = loadingScreenGUI

	rds.keyBindings = BWKeyBindings.BWKeyBindings()

	# TODO: should be read by a module in scripts/common/GameData
	keyBindingData = ResMgr.openSection( "scripts/data/default_key_bindings.xml" )
	rds.keyBindings.readInDefaultKeyBindings( keyBindingData )

	if rds.userPreferences.has_key( "keyBindings" ):
		keyBindingData = rds.userPreferences._keyBindings
		rds.keyBindings.readInPreferenceKeyBindings( keyBindingData )

	rds.keyBindings.buildBindList()
	#rds.keyBindings.printBindList()

	# An action handler for FantasyDemo module level actions
	rds.fantasyDemoActionHandler = FantasyDemoActionHandler()
	rds.keyBindings.addHandler( rds.fantasyDemoActionHandler )

	actionToolTipsSection = ResMgr.openSection( "scripts/data/action_tooltips.xml" )
	rds.fdgui = FDGUI.FDGUI()
	rds.fdgui.setupGUI( actionToolTipsSection, rds.keyBindings )

	#setLanguage(scriptsConfig.readString('ui/language', 'english'))

	cc = BigWorld.CursorCamera()
	cc.source = BigWorld.dcursor().matrix
	cc.target = BigWorld.PlayerMatrix()
	BigWorld.dcursor().yawReference = cc.invViewMatrix
	BigWorld.dcursor().minYaw = -2
	BigWorld.dcursor().maxYaw =  2

	cc.pivotPosition = scriptsConfig.readVector3(
		'camera/defTargetOffset', (0.0, 1.8, 0.0))

	rds.outsidePivotMaxDist = scriptsConfig.readFloat(
		'camera/maxDistanceFromPivot', cc.pivotMaxDist)
	rds.insidePivotMaxDist = scriptsConfig.readFloat(
		'camera/indoorDistanceFromPivot', rds.outsidePivotMaxDist)
	rds.reversePivotMaxDist = scriptsConfig.readFloat(
		'camera/faceDistanceFromPivot', rds.outsidePivotMaxDist)

	rds.useWoWMode = userPreferences.readBool('useWoWMode', rds.useWoWMode)
	rds.mouseMoveThreshold = scriptsConfig.readInt(
		'camera/mouseMoveThreshold', rds.mouseMoveThreshold)

	cc.pivotMaxDist = rds.outsidePivotMaxDist
	cc.pivotMinDist = scriptsConfig.readFloat(
		'camera/minDistanceFromPivot', cc.pivotMinDist)
	cc.terrainMinDist = scriptsConfig.readFloat(
		'camera/minDistanceFromTerrain', cc.terrainMinDist)
	cc.maxVelocity = scriptsConfig.readFloat(
		'camera/maxVelocity', cc.maxVelocity)
	cc.movementHalfLife = scriptsConfig.readFloat(
		'camera/movementHalfLife', cc.movementHalfLife)
	cc.turningHalfLife = scriptsConfig.readFloat(
		'camera/turningHalfLife', cc.turningHalfLife)

	rds.cc = cc
	rds.defaultPivotMaxDist = rds.outsidePivotMaxDist
	rds.defaultNearPlane = BigWorld.projection().nearPlane

	# flexi cam
	flc = BigWorld.FlexiCam()
	flc.target = cc.target
	flc.preferredPos = (0.0, 3.2, -2.5)
	flc.viewOffset = (0.0, 1.8, 0.0)
	flc.timeMultiplier = 8

	rds.flc = flc

	# fixed cam
	fic = BigWorld.FlexiCam()
	fic.target = rds.fixedMatrix
	fic.preferredPos = (0,0,-1)
	fic.viewOffset = (0,0,0)
	fic.timeMultiplier = 8

	rds.fic = fic

	# free cam
	rds.frc = BigWorld.FreeCamera()


	# compute matrix to translate camera position to near plane
	m = MatrixProduct()
	m.a = Matrix()
	m.a.setTranslate( (0, 0, BigWorld.projection().nearPlane) )
	m.b = rds.cc.invViewMatrix

	# hook up the cameras to water
	rds.waterListenerID = BigWorld.addWaterVolumeListener( m, rds.cameraWaterCallback )

	# start off with
	# cursor camera
	BigWorld.camera(cc)

	# now load direction
	# cursor details
	try:
		rds.thirdPersonDCSettings.load(engineConfig._directionCursor)
	except:
		pass

	try:
		rds.firstPersonDCSettings.copy(rds.thirdPersonDCSettings)
		rds.firstPersonDCSettings.load(scriptsConfig._dcFirstPersonOverrides)
	except:
		pass

	# make the console
	initConsole()

	# time of day when offline
	rds.offlineTimeOfDay = scriptsConfig.readString('offline/timeOfDay', '14:00')
	rds.offlineSpaces = None

	rds.lastWeatherSync = {}

	# load the logo gui
	rds.logoGui = None

	#__import__('Helpers').alertsGui.instance.init()
	#__import__('Helpers').Inventory.instance.init()

	# and we're done
	print 'fantasydemo personality selected.'

# -----------------------------------------------------------------------------
# Method: start
# Description:
#	- The start function is called after the BigWorld Client has initialised
#	and is used	to begin the game.
#	- Although it receives no data, it uses the shared personality data to
#	initiate the login process.
#	- Other instances may display an introduction or initiate some other game
#	flow process...
# -----------------------------------------------------------------------------
def start():
	import sys
	if len(sys.argv) >= 4 and sys.argv[1] == 'profile':
		# fantasydemo.exe -sa profile -sa spaces/highlands -sa gf8800
		_runProfiler( sys.argv[2], sys.argv[3] )
		return
	elif len(sys.argv) >= 3 and sys.argv[1] == 'loadtimer':
		# fantasydemo.exe -sa loadtimer -sa spaces/highlands
		print "Starting load timer run ..."
		_loadTimerStart( sys.argv[2] )
		return

	global rds
	BigWorld.worldDrawEnabled(False)
	rds.startupGUI = GUI.load('gui/main_menu.gui')

	rds.mainMenuGUI = rds.startupGUI.mainmenu
	rds.mainMenuGUI.script.scrollUp = rds.startupGUI.scrollUp
	rds.mainMenuGUI.script.scrollDown = rds.startupGUI.scrollDown

	rds.mainMenuGUI.script.parent   = rds.startupGUI
	rds.mainMenuGUI.script.isActive = True
	rds.mainMenuGUI.script.active(False)

	rds.menuCaptionsGUI = rds.startupGUI.captions

	rds.usernameGUI = rds.startupGUI.username

	rds.editField = rds.usernameGUI.edit
	rds.editField.script.parent   = rds.usernameGUI
	rds.editField.script.isActive = True

	rds.li = LoginInfo()

	_showLogoScreen(False)
	_showLoadingBar(False)
	_startMainMenu()

	onRecreateDevice()
	BigWorld.callback(0.1, _testEngineFeatures)


############################################################################
# Main menu, server discovery and login related functions.
############################################################################

def _startMainMenu():
	'''Activates the game menu. The game menu is a two level menu.
	Calling 	this method, activates the first level. The second
	level menus are activated by callback functions attached to
	the first level menu items.
	'''
	global rds

	rds.menuStack = []

	rds.startupGUI.script.active(True)
	rds.startupGUI.fader.alpha = 1.0
	rds.startupGUI.fader.reset()
	rds.startupGUI.script.showCharacterScreen( lambda: None, False, 0 )

	mainMenuItems = [
		(MENU_ENTRIES[ 'XMLSERVERS' ][0], _showXMLServersMenu),
		(MENU_ENTRIES[ 'LANSERVERS' ][0], _showLanServersMenu),
		(MENU_ENTRIES[ 'OFFLSPACES' ][0], _showOfflineSpacesMenu),
		(MENU_ENTRIES[ 'SETTINGS'   ][0], _showSettingsMenu),
		(MENU_ENTRIES[ 'QUITGAME'   ][0], _quitGame) ]

	_pushMainMenu()
	_setMainMenu(mainMenuItems, 'MAINMENU')
	_showUserNameEdit(False)
	_showLogoScreen( False )

	if not MenuScreenSpace.g_menuSpaceID:
		MenuScreenSpace.init()

def _quitGame():
	global rds

	_showLoadingBar(False)
	_showLogoScreen(True, False)

	rds.loadingScreen.fader.reset()
	gui = rds.startupGUI
	gui.fader.alpha = 0
	BigWorld.callback(gui.fader.speed, lambda: gui.script.active(False))
	BigWorld.callback(gui.fader.speed + 0.5, BigWorld.quit)

def _testEngineFeatures():
	allOkay = True
	for featureKey, active, options, desc in BigWorld.graphicsSettings():
		if options and not options[0][1]:
			allOkay = False
			feature = desc
			if options[0][0] == 'On' and options[1][0] == 'Off':
				addMsg('%s not supported (turning it off)' % feature)
			else:
				addMsg('%s not fully supported (using %s)' % (feature, options[active][0]))
	if allOkay:
		addMsg('Engine features fully supported on this system')


@BWCoroutine
def _finishMainMenu():
	'''Clears the menu stack.
	'''
	gui = rds.startupGUI
	gui.fader.alpha = 0
	BigWorld.callback(gui.fader.speed, lambda: gui.script.active(False))
	yield BWWaitForCoroutine( 10, _disconnectFromServer, rds.startupGUI.script.showCharacterScreen, False, 0 )

	rds.mainMenuGUI.script.active(False)
	MenuScreenSpace.fini()

# this function tries to get the current menu index
# if there is no current menu index it returns 0
def _indexInMenu():
	global rds
	try:
		return rds.mainMenuGUI.script.selection
	except:
		return 0

def _pushMainMenu(indexInPrevMenu = -1):
	'''Pushes the current menu into the menu stack.
	Params:
		indexInPrevMenu		index of item to be selected when returning
									from this menu to parent menu
	'''
	global rds
	if indexInPrevMenu == -1:
		indexInPrevMenu = _indexInMenu()

	rds.menuStack.append((None, [], indexInPrevMenu, None, lambda x: None))


def _setMainMenu(
	menuItems, caption, backFunc = lambda: True, selectedItem = 0, selectItemCallback = lambda x: None):
	'''Sets and shows current main menu items.
	'''
	global rds

	def chainedBackFunc():
		if backFunc():
			_popMainMenu()

	if len(rds.menuStack) > 1 and backFunc is not None:
		callbackFunc = chainedBackFunc
	else:
		callbackFunc = None

	# a menu may wish not to change the caption set by it's previous
	# menu (by passing it None). In this case, save the caption of the
	# previous menu so it can be restored (if None was saved, it would
	# use the same caption of the forecoming menu when poping back.
	if caption is not None:
		pushedCaption = caption
	else:
		assert len(rds.menuStack) > 1
		pushedCaption = rds.menuStack[-2][3]

	rds.menuStack[-1] = (callbackFunc, menuItems,
						rds.menuStack[-1][2], pushedCaption, selectItemCallback)

	_createMainMenu(callbackFunc, menuItems, selectedItem, caption, selectItemCallback )


def _popMainMenu():
	'''Pops the topmost menu from the menu stack and shows it.
	'''
	global rds
	previousMenu = rds.menuStack.pop()
	# selection index to go to is on the top of the stack,
	# so modify the current menu so it goes back to the right selection
	currentMenu  = list(rds.menuStack[-1][:])
	currentMenu[2] = previousMenu[2]
	_createMainMenu( *currentMenu )


def _createMainMenu(callbackFunc, menuItems, itemIndex, caption, selectItemCallback ):
	'''Creates the main menu from the given parameters.
	'''
	global rds

	# append a back option if menu is not the
	# root and if first option is selectable
	items = menuItems[:]
	if len(rds.menuStack) > 1 and items[0][1]:
		items.append(('<back>', callbackFunc))

	rds.mainMenuGUI.script.selectItemCallback = selectItemCallback
	rds.mainMenuGUI.script.active(True)
	rds.mainMenuGUI.script.setupItems(callbackFunc, items)
	rds.mainMenuGUI.items.script.scrollTo(0, 0)
	rds.mainMenuGUI.items.script.scrollTransform.setIdentity()
	rds.mainMenuGUI.items.transform.reset()
	rds.mainMenuGUI.script.selectItem(itemIndex)
	rds.startupGUI.script.doLayout( None )
	if caption:
		rds.menuCaptionsGUI.title.textureName = MENU_ENTRIES[ caption ][1]
		rds.menuCaptionsGUI.help.textureName = MENU_ENTRIES[ caption ][2]


def _showXMLServersMenu():
	'''Shows menu with all hosts listed in
	scripts_config.xml file under the <login>/<host> field.
	'''
	xmlServers  = rds.scriptsConfig.readStrings('login/host')
	menuEntries = _createHostsItems(zip(xmlServers, xmlServers))

	_pushMainMenu()
	_setMainMenu(menuEntries, 'XMLSERVERS')


def _showLanServersMenu():
	'''Activates menu with list of lan servers. The menu is
	populated using bigWorld server discovery feature. Uses
	the _serversDiscovered function to actually build the menu.
	'''
	global rds
	rds.menuUpdatesAllow = False

	def _startSearchingForServers():
		_setMainMenu(
			[('Searching for servers on local network', None)],
			'LANSERVERS', _stopSearchAndGoPreviousMenu)

		BigWorld.serverDiscovery.searching = 1
		BigWorld.serverDiscovery.changeNotifier = _serversDiscovered
		BigWorld.callback(0.5, _menuUpdatesAllow)

	def _stopSearchAndGoPreviousMenu():
		rds.menuUpdatesAllow = False
		BigWorld.serverDiscovery.searching = 0
		return True

	def _serversDiscovered():
		'''Callback function called by BigWorld server discovery mechanism
		(from _lanServersMenu). Each time it is triggered, the lan servers
		menu is recreated with the updated servers information.
		'''
		if not rds.menuUpdatesAllow:
			return

		lastUsedServerUID = rds.userPreferences.readInt('lastServer/uid')

		lanServers = [
			(_serverNiceName(server), _serverNetName(server))
			for server in BigWorld.serverDiscovery.servers if server.uid == lastUsedServerUID ]

		lanServers = lanServers + [
			(_serverNiceName(server), _serverNetName(server))
			for server in BigWorld.serverDiscovery.servers if server.uid != lastUsedServerUID ]

		_setMainMenu(
			_createHostsItems(lanServers, _startSearchingForServers), 'LANSERVERS',
			_stopSearchAndGoPreviousMenu)

	def _menuUpdatesAllow():
		if BigWorld.serverDiscovery.searching:
			rds.menuUpdatesAllow = True
			if len(BigWorld.serverDiscovery.servers) > 0:
				_serversDiscovered()
			else:
				BigWorld.callback(1.5, _noServersFound)

	def _noServersFound():
		if rds.menuUpdatesAllow and \
				BigWorld.serverDiscovery.searching and \
					len(BigWorld.serverDiscovery.servers) == 0:
			_setMainMenu(
				[('No servers found on local network', None)],
				'LANSERVERS')
			BigWorld.serverDiscovery.searching = 0
			rds.menuUpdatesAllow = False

	_pushMainMenu()
	_startSearchingForServers()

def _createHostsItems(servers_list, abortCallback=None):
	'''Creates list of host menu items from a list of
	2-tuples (human readable label, connection callback).
	'''
	server_items = []
	for i, (label, host) in enumerate(servers_list):
		server_items.append((label,
				partial(_inputUserNameAndConnect, host, label, i, abortCallback)))
	return server_items


def _showUserNameEdit(visible):
	'''Shows/hides a edit field for input of username.
	'''
	global rds
	rds.usernameGUI.visible = visible
	rds.editField.script.active(visible)


def _inputUserNameAndConnect(host, label, index, abortCallback = None):
	'''Asks for username. Try to connect to
	given host after <enter> key is pressed.
	'''
	global rds
	rds.menuUpdatesAllow = False

	def _saveNameAndConnect(username):
		if username != '':
			rds.userPreferences.writeString('lastUsedAccountName', str(username))

			rds.userPreferences.write( 'lastServer', '' )

			for i in BigWorld.serverDiscovery.servers:
				if _serverNetName( i ) == host:
					'''
					Although only the uid is currently used. The full server
					info is saved for completeness and to assist in debugging.
					'''
					rds.userPreferences.writeString(	'lastServer/hostName',		i.hostName )
					rds.userPreferences.writeString(	'lastServer/ip',			_serverDottedHost( i.ip ) )
					rds.userPreferences.writeString(	'lastServer/ownerName',		i.ownerName )
					rds.userPreferences.writeInt(		'lastServer/port',			i.port )
					rds.userPreferences.writeString(	'lastServer/spaceName',		i.spaceName )
					rds.userPreferences.writeInt(		'lastServer/uid',			i.uid )
					rds.userPreferences.writeString(	'lastServer/universeName',	i.universeName )
					rds.userPreferences.writeInt(		'lastServer/usersCount',	i.usersCount )

			BigWorld.savePreferences()
			_connectToServer(host, label, str(username))
			_showUserNameEdit(False)

	def _goBackToServersMenu():
		_popMainMenu()
		_showUserNameEdit(False)
		if abortCallback:
			abortCallback()

	_pushMainMenu()
	_setMainMenu([('Enter a new or existing Account name:', None)], None, None)
	rds.menuCaptionsGUI.help.textureName = HELP_EDIT

	rds.editField.text            = rds.li.username
	rds.editField.script.onEnter  = _saveNameAndConnect
	rds.editField.script.onEscape = _goBackToServersMenu
	_showUserNameEdit(True)


@BWCoroutine
def _showCharacterSelectionScreen():

	if isinstance( BigWorld.player(), Avatar.Avatar ):
		_proceedTooLevel( lambda: None )
		return

	assert BigWorld.player() == None or isinstance( BigWorld.player(), Account.Account )

	@BWCoroutine
	def onCharacterSelect( characterName ):
		_setMainMenu( [ ('Retrieving Character', None ) ], None, _disconnectFromServer )
		rds.userPreferences.writeString('lastPlayedAvatar', characterName )
		BigWorld.savePreferences()

		yield BWWaitForCoroutine( 10, _disconnectFromServer, rds.startupGUI.script.showCharacterScreen, False )

		if BigWorld.server() is None:
			return

		BigWorld.player().base.characterBeginPlay( str( characterName ) )

		yield BWWaitForCondition( 0.5, 120, _disconnectFromServer, lambda: BigWorld.player() and BigWorld.player().inWorld )

		if BigWorld.server() is None:
			return

		_proceedTooLevel( lambda: None )


	@BWCoroutine
	def onCancel():
		try:
			menuScreenAvatars = filter( lambda e: isinstance( e, MenuScreenAvatar.MenuScreenAvatar ), BigWorld.entities.values() )
			menuScreenAvatars[0].setModel( AvatarModel.defaultModel() )
		except Exception, e:
			print e

		rds.startupGUI.script.showCharacterScreen( lambda: None, False, 1.0 )

		yield BWWaitForPeriod( 1.0 )

		_disconnectFromServer()

	def onChangeCurrentSelection( avatarModels, index ):
		try:
			menuScreenAvatars = filter( lambda e: isinstance( e, MenuScreenAvatar.MenuScreenAvatar ), BigWorld.entities.values() )
			if index >= 1 and index <= len( avatarModels ):
				menuScreenAvatars[0].setModel( avatarModels[index - 1] )
			else:
				menuScreenAvatars[0].setModel( AvatarModel.defaultModel() )
		except Exception, e:
			print e


	_setMainMenu( [ ('Waiting for Character List', None ) ], 'CHARACTERSELECT', _disconnectFromServer )
	yield BWWaitForCondition( 0.01, 120, _disconnectFromServer, lambda: MenuScreenSpace.g_loaded and BigWorld.player() != None )

	yield BWWaitForCoroutine( 10, lambda: None, rds.startupGUI.script.showCharacterScreen, True )

	if BigWorld.server() is None:
		return

	initialSelection = 0
	lastPlayedAvatar = rds.userPreferences.readString('lastPlayedAvatar')
	menuList = [ ('<create character>', _showCharacterCreationScreen) ]
	for characterInfo in BigWorld.player().characterList:
		menuList.append( ( characterInfo['name'], partial( onCharacterSelect, lambda: None, characterInfo['name'] )  ) )
		if characterInfo['name'] == lastPlayedAvatar:
			initialSelection = BigWorld.player().characterList.index( characterInfo ) + 1

	unpackedCharacterModels = [AvatarModel.unpack( character['characterModel'] ) for character in BigWorld.player().characterList]
	selectionCallbackObject = partial( onChangeCurrentSelection, unpackedCharacterModels )
	_setMainMenu( menuList, 'CHARACTERSELECT', partial( onCancel, lambda: None ), initialSelection, selectionCallbackObject)


def _showCharacterCreationScreen():
	'''Asks for a character name. Try to add a new character to the account.
	'''
	def _createCharacter( characterName ):

		def finishCharacterCreate( succeded, msg ):
			if succeded:
				_popMainMenu()
				_setMainMenu([(msg, None)], None, None)
			else:
				_displayErrorInMenu( msg )

			if not succeded:
				BigWorld.callback( 3, partial( _showCharacterSelectionScreen, lambda: None ) )
			else:
				_showCharacterSelectionScreen( lambda: None )

		BigWorld.player().createNewCharacter( str(characterName), finishCharacterCreate )
		_showUserNameEdit(False)

	def _cancelCharacterCreate():
		_popMainMenu()
		_showUserNameEdit(False)

	_pushMainMenu()
	_setMainMenu([('Character name:', None)], 'CHARACTERCREATE', None)

	rds.editField.text            = ''
	rds.editField.script.onEnter  = _createCharacter
	rds.editField.script.onEscape = _cancelCharacterCreate
	_showUserNameEdit(True)


def onCreateAvatarFailed():
	print 'Avatar.clientOnCreateCellFailure'
	_setMainMenu( [ ( 'Failed to Retrieve Character', None ),
					( 'Logging Out', None ) ], None, None )
	BigWorld.callback( 5.0, _disconnectFromServer )


def _connectToServer(host, label, username):
	'''Callback triggered when the user choses a server
	from the servers menu. Tries to connect to it.
	'''
	global rds

	message1 = 'Server: %s ' % label
	message2 = 'Account name: %s' % username
	_setMainMenu([(message1, None), (message2, None)], None, None)
	addMsg(message1 + message2)

	_disconnectFromServer()

	rds.li.username = username
	rds.li.password = "pass" 	# this has an even number of characters to pass
								# the stub billing request: see the
								# AsyncBillingRequest class in the
								# base/Account.py module.
	BigWorld.serverDiscovery.searching = 0

	def doConnect():
		BigWorld.resetEntityManager( False, True )
		BigWorld.clearAllSpaces( True )
		BigWorld.connect(host, rds.li, _connectionCallback)

	BigWorld.callback(1.5, doConnect)


def _showOfflineSpacesMenu():
	'''Shows menu with all spaces listed in
	the space root directory (res/spaces).
	'''
	_pushMainMenu()
	_setMainMenu(_enumOfflineSpaces(), 'OFFLSPACES')


def _enumOfflineSpaces():
	'''Enumerates all spaces listed in the space root
	directory (res/spaces). Return them as menu-item
	2-tuples (human readable label, connection callback).
	'''
	global rds

	def _onSpaceChosen(spaceName):
		_disconnectFromServer()
		BigWorld.serverDiscovery.searching = 0

		message = 'Exploring offline space: %s' % spaceName
		_setMainMenu([(message, None)], None, None)

		BigWorld.resetEntityManager( False, True )
		BigWorld.clearAllSpaces( True )
		BigWorld.connect('', '', _connectionCallback)
		BigWorld.callback(1.0, lambda: _exploreOffline(spaceName))

	# list spaces
	if rds.offlineSpaces is None:
		spacesRoot = 'spaces'
		rds.offlineSpaces = []
		for direct in ResMgr.openSection(spacesRoot).values():
			if direct.has_key('space.settings'):
				name = '%s/%s' % (spacesRoot, direct.name)
				if name.endswith('/main'):
					# make sure the main
					# space always comes first
					rds.offlineSpaces.insert(0, name)
				else:
					rds.offlineSpaces.append(name)
	spaces = []
	for space in rds.offlineSpaces:
		spaces.append((space, partial(_onSpaceChosen, space)))

	return spaces


@BWCoroutine
def _proceedTooLevel():
	'''Put up the loading screen and wait for the level to load.
	'''
	def loadFinished():
		# connection may have been
		# cancelled half way through
		if BigWorld.server() is not None:
			_showLoadingBar( False )
			_showLogoScreen( False )

	_showLogoScreen( True, False )

	yield BWWaitForCoroutine( 20, _disconnectFromServer, _finishMainMenu )

	_startChunkLoadingBar( loadFinished )
	_showLoadingBar( True )
	rds.selfDisconnect = False


def _exploreOffline(spaceName, doConnectionCallback = True):
	'''Callback triggered when the user choses a space from
	the offline spaces menu. Loads the space and run offline.
	'''
	global rds

	message = 'Exploring offline space: %s' % spaceName
	addMsg(message)

	if rds.clientSpace is not None:
		BigWorld.releaseSpace(rds.clientSpace)
		rds.clientSpace = None

	rds.clientSpaceName = spaceName
	rds.clientSpace = BigWorld.createSpace()

	try:
		rds.clientSpaceMapping = BigWorld.addSpaceGeometryMapping(
			rds.clientSpace, None, rds.clientSpaceName)
	except ValueError:
		message = 'Could not load space: %s' % spaceName
		addMsg(message)
		BigWorld.releaseSpace(rds.clientSpace)
		rds.clientSpace = None
		_popMainMenu()
		return

	startPosition = rds.scriptsConfig._player._startPosition.asVector3
	startDirection = rds.scriptsConfig._player._startDirection.asVector3
	try:
		ssect = ResMgr.openSection(spaceName + '/space.settings')
		startPosition = ssect._startPosition.asVector3
		startDirection = ssect._startDirection.asVector3
	except:
		pass

	playerModel = PlayerModel.defaultPlayerModel()

	etype = rds.scriptsConfig._player._class.asString
	BigWorld.createEntity( etype, rds.clientSpace, 0,
		startPosition, startDirection, {'avatarModel':AvatarModel.pack( playerModel )})

	BigWorld.timeOfDay(rds.offlineTimeOfDay)

	# we have 'connected' now ... locally as it were
	if doConnectionCallback == True:
		_connectionCallback(1, 'CUSTOM_MSG', 'Single user mode')

	# pretend we did get data too.
	# C01: stage = 2 / status = 'OFFLINE' is never generated by BigWorld
	# It's been used here to signed the connection callback that
	# we're running offline, so it changes the time of day just
	# before hiding the loading screen (I'd prefer setting it
	# here, but this is crashing the client).
	if doConnectionCallback == True:
		BigWorld.callback(2, lambda: _connectionCallback(2, 'OFFLINE', ''))

	BigWorld.player().onChangeEnvironments( False )

#########################
# The settings menues   #
#########################

# this function sets up and shows the settings menu
def _showSettingsMenu(selectedItem = 0):
	'''????
	'''
	_pushMainMenu()

	menuitems = [ ('Video', _showVideoSettingsMenu),
				('Graphics Detail', _showDetailSettingsMenu)]

	_setMainMenu( menuitems, 'SETTINGS', _updateSettingsForceRestart )

# This function sets up and displays the detail settings menu
def _showDetailSettingsMenu(selectedItem = 0):
	'''
	'''
	def _togglePresets(presets, optionIndex):
		presets.selectGraphicsOptions( optionIndex )
		_updateSettings()

	def _exitSettingsMenu():
		BigWorld.savePreferences()
		return True, selectedItem

	_pushMainMenu()

	presets = GraphicsPresets()

	advancedMsg = 'Advanced Settings'
	if presets.selectedOption == -1:
		advancedMsg += ' *'

	menuitems = []

	for i in range(0, len(presets.entryNames)):
		presetMsg = presets.entryNames[i]
		if i == presets.selectedOption:
			presetMsg += ' *'
		menuitems.append( ( presetMsg,
							partial( _togglePresets, presets, i )))

	menuitems.append( (advancedMsg,   _showAdvancedSettingsMenu) )
	
	autoDetectMsg = "Auto-Detect"
	menuitems.append( (autoDetectMsg, _autoDetectGraphicsSettings) )

	_setMainMenu( menuitems,
				'SETTINGS', _exitSettingsMenu, selectedItem)

# This funtion refreshes the contents of the of the detail settings menu
def _refreshDetailSettingsMenu():
	indexInPrevMenu = _indexInMenu()
	_popMainMenu()
	_showDetailSettingsMenu(indexInPrevMenu)

# This function commits any pending graphics settings
def _commitSettings():
	BigWorld.commitPendingGraphicsSettings()
	_refreshDetailSettingsMenu()

# This function checks for pending graphics settings
def _checkPending():
	if BigWorld.hasPendingGraphicsSettings():
		_setMainMenu([('Applying new settings...', None)], None)
		BigWorld.callback(0.1, _commitSettings)
	else:
		_refreshDetailSettingsMenu()

# This function updates the graphics settings
def _updateSettings():
	BigWorld.savePreferences()
	if BigWorld.graphicsSettingsNeedRestart():
		menu = [
			('New settings require restarting game ', None),
			('Restart now', BigWorld.restartGame),
			('Restart later', _checkPending)]
		_setMainMenu(menu, None, lambda: True, 1)
	else:
		_checkPending()

def _updateSettingsForceRestart():
	BigWorld.savePreferences()
	if BigWorld.graphicsSettingsNeedRestart():
		global rds
		menu = [
			('New settings require restarting game ', None),
			(MENU_ENTRIES[ 'SETTINGS' ][0], _showSettingsMenu),
			(MENU_ENTRIES[ 'RESTART'  ][0], BigWorld.restartGame),
			(MENU_ENTRIES[ 'QUITGAME' ][0], _quitGame) ]

		rds.menuStack = []
		_pushMainMenu()
		_setMainMenu(menu, 'RESTART', lambda: False, 1)
		return False
	else:
		_checkPending()
		return True

# This function sets up and shows the video settings menu
def _showVideoSettingsMenu(selectedItem = 0):
	def _refreshVideoSettingsMenu():
		indexInPrevMenu = _indexInMenu()
		_popMainMenu()
		delDeviceListener(rds.refreshMenu)
		_showVideoSettingsMenu(indexInPrevMenu)


	# Local functions used by the settings menu
	def _toggleWindowed():
		curModeIdx = BigWorld.videoModeIndex()
		BigWorld.changeVideoMode(curModeIdx, not BigWorld.isVideoWindowed())
		_refreshVideoSettingsMenu()

	def _toggleVSync():
		BigWorld.setVideoVSync(not BigWorld.isVideoVSync())
		_refreshVideoSettingsMenu()

	def _toggleTripleBuffering():
		BigWorld.setTripleBuffering(not BigWorld.isTripleBuffered())
		_refreshVideoSettingsMenu()

	def _exitSettingsMenu():
		BigWorld.savePreferences()
		delDeviceListener(rds.refreshMenu)
		return True, selectedItem

	# resolution strings
	if BigWorld.isVideoWindowed():
		toggleWindowedMsg = 'Switch to Full Screen'
		resolutionText    = 'Select Window Size'
	else:
		toggleWindowedMsg = 'Switch to Windowed Mode'
		resolutionText    = 'Select Resolution'

	# vsync strings
	if BigWorld.isVideoVSync():
		toggleVSyncMsg = 'Turn Vertical Sync Off'
	else:
		toggleVSyncMsg = 'Turn Vertical Sync On'

	# triple buffering strings
	if BigWorld.isTripleBuffered():
		toggleTripleMsg = 'Turn Triple Buffering Off'
	else:
		toggleTripleMsg = 'Turn Triple Buffering On'

	_pushMainMenu()

	menuitems = [ (toggleWindowedMsg,     _toggleWindowed),
				(resolutionText,        _showVideoModesMenu),
				('Select Fullscreen Aspect Ratio', _showAspectRatioMenu),
				(toggleVSyncMsg,        _toggleVSync),
				(toggleTripleMsg, _toggleTripleBuffering)]

	_setMainMenu( menuitems,
				'SETTINGS', _exitSettingsMenu, selectedItem)

	class RefreshMenu:
		def __init__(self):
			self.enabled = True

		def onRecreateDevice(self):
			if self.enabled:
				_refreshVideoSettingsMenu()
			else:
				self.enabled = True

		def disableOnce(self):
			self.enabled = False

	global rds
	rds.refreshMenu = RefreshMenu()
	addDeviceListener(rds.refreshMenu)

def _showAspectRatioMenu():
	def _setAspectRatio(ratio):
		BigWorld.changeFullScreenAspectRatio(ratio)
		rds.fdgui.chooseResolutionBracket()
		_popMainMenu()

	def _enumApectRatios():
		ratios = [
			(16, 9, None),
			(4, 3, None),
			(16, 10, 'Dell'),
			(5, 4, None)]

		ratiosMenu = []
		currentlySelected = 0
		current = 0
		currentAspectRatio = BigWorld.getFullScreenAspectRatio()
		for x, y, comment in ratios:
			desc = '%d:%d' % (x, y)
			if comment:
				desc += ' [%s]' % comment
			ratio = float(x)/y
			ratiosMenu.append((desc, partial(_setAspectRatio, ratio)))
			if abs(ratio - currentAspectRatio) < 0.01:
				currentlySelected = current
			current += 1
		return (ratiosMenu,currentlySelected)

	_pushMainMenu()
	menu, current = _enumApectRatios()
	_setMainMenu( menu, 'SETTINGS', lambda: True, current)


def _showVideoModesMenu():
	_pushMainMenu()
	modes, current = _enumVideoModes()
	_setMainMenu(modes, 'SETTINGS', lambda: True, current)


def _enumVideoModes():
	def _changeMode(mode):
		rds.refreshMenu.disableOnce()
		if BigWorld.isVideoWindowed():
			BigWorld.resizeWindow(mode[1], mode[2])
		else:
			BigWorld.changeVideoMode(mode[0], False)
		_popMainMenu()

	modes = []
	current = 0
	for mode in BigWorld.listVideoModes():
		if mode[3] == 32:
			modes.append((mode[4], partial(_changeMode, mode)))
			if BigWorld.isVideoWindowed():
				w, h = BigWorld.windowSize()
				if (mode[1], mode[2]) == (int(w), int(h)):
					current = len(modes)-1
			else:
				if mode[0] == BigWorld.videoModeIndex():
					current = len(modes)-1

	return modes, current
	
	
def _autoDetectGraphicsSettings():
	BigWorld.autoDetectGraphicsSettings()
	_updateSettings()
	
	
def _showAdvancedSettingsMenu():
	def _showAdvSubMenu(settingIndex, settingId):
		def _setGraphicsSetting(settingId, optionIndex):
			BigWorld.setGraphicsSetting(settingId, optionIndex)
			_popMainMenu()

		def _makeCallBack(optionIndex, supported):
			if supported:
				return lambda: _setGraphicsSetting(settingId, optionIndex)
			else:
				return None

		_pushMainMenu()
		setting = BigWorld.graphicsSettings()[settingIndex]
		active  = setting[1]
		options = setting[2]
		desc = setting[3]
		settingsSubMenu = [
			(desc, _makeCallBack(index, supported))
			for index, (option, supported, desc)
			in enumerate(options)]

		_setMainMenu(settingsSubMenu, 'SETTINGS', lambda: True, active)

	def _exitAdvancedSettings():
		_popMainMenu()
		_updateSettings()
		return False

	_pushMainMenu()
	settingsMenu = [
		(desc, partial(_showAdvSubMenu, index, settingId))
		for index, (settingId, active, options, desc)
		in enumerate(BigWorld.graphicsSettings())]

	_setMainMenu(settingsMenu, 'SETTINGS', _exitAdvancedSettings)


def _displayErrorInMenu(msg):
	errorMsg = []
	while len(msg):
		if len(msg) <= MAX_ERROR_LEN:
			errorMsg.append((msg, None))
			break

		spcPos = msg.rfind(' ', 0, MAX_ERROR_LEN)
		if spcPos == -1:
			spcPos = MAX_ERROR_LEN

		errorMsg.append((msg[:spcPos], None))
		msg = msg[spcPos+1:]

	for i, (msg, func) in enumerate(errorMsg[1:]):
		errorMsg[i+1] = (msg, func)
	_setMainMenu(errorMsg, None)


def _connectionCallback(stage, status, serverMsg):
	'''Callback trig by BigWorld to report on the status of the connection.
	Logs the status in the console and update the GUI accordingly.
	'''
	loginErrorStrs = {
		'NOT_SET'										: 'Not set',
		'LOGGED_ON'										: 'Account Login succeeded',
		'CONNECTION_FAILED'							: 'Login failed: Unable to contact login server',
		'DNS_LOOKUP_FAILED'							: 'Login failed: DNS lookup failed',
		'UNKNOWN_ERROR'								: 'Login failed: Unknown local client error',
		'CANCELLED'										: 'Login failed: Login cancelled',
		'ALREADY_ONLINE_LOCALLY'					: 'Login failed: Already online',
		'PUBLIC_KEY_LOOKUP_FAILED'					: 'Login failed: Public key lookup failed',
		'LOGIN_MALFORMED_REQUEST'					: 'Login failed: Malformed login request',
		'LOGIN_BAD_PROTOCOL_VERSION'				: 'Login failed: Wrong protocol version',
		'LOGIN_REJECTED_NO_SUCH_USER'				: 'Login failed: No such user: %(username)s',
		'LOGIN_REJECTED_INVALID_PASSWORD'		: 'Login failed: Invalid password',
		'LOGIN_REJECTED_ALREADY_LOGGED_IN'		: 'Login failed: Someone with account name %(username)s already logged in',
		'LOGIN_REJECTED_BAD_DIGEST'				: 'Login failed: Defs digest mismatch',
		'LOGIN_REJECTED_DB_GENERAL_FAILURE'		: 'Login failed: Misc database rejection',
		'LOGIN_REJECTED_DB_NOT_READY'				: 'Login failed: Unable to contact server database',
		'LOGIN_REJECTED_ILLEGAL_CHARACTERS'		: 'Login failed: Illegal characters in user name/password',
		'LOGIN_REJECTED_SERVER_NOT_READY'		: 'Login failed: Server not ready',
		'LOGIN_REJECTED_UPDATER_NOT_READY'		: 'Login failed: Unable to contact Updater',
		'LOGIN_REJECTED_NO_BASEAPPS'				: 'Login failed: Unable to contact BaseApps',
		'LOGIN_REJECTED_BASEAPP_OVERLOAD'		: 'Login failed: BaseApp overloaded',
		'LOGIN_REJECTED_CELLAPP_OVERLOAD'		: 'Login failed: CellApp overloaded',
		'LOGIN_REJECTED_BASEAPP_TIMEOUT'			: 'Login failed: BaseApp timed-out',
		'LOGIN_REJECTED_BASEAPPMGR_TIMEOUT'		: 'Login failed: BaseAppMgr overloaded',
		'LOGIN_REJECTED_DBMGR_OVERLOAD'			: 'Login failed: Database overloaded',
		'LOGIN_REJECTED_LOGINS_NOT_ALLOWED'		: 'Login failed: Logins not allowed',
	}

	global rds
	if stage == 1 :
		defaultMsg = serverMsg if serverMsg else 'Unknown server error'
		errorMsg = loginErrorStrs.get(status, defaultMsg)
		errorMsg = errorMsg % rds.li.__dict__
		_displayErrorInMenu(errorMsg)
		addMsg(errorMsg)

	elif stage == 2:
		if status == 'OFFLINE':
			_proceedTooLevel( lambda: None )
		else:
			_showCharacterSelectionScreen( lambda: None )

	elif stage == 6:
		_handleDisconnectionFromServer( lambda: None )


@BWCoroutine
def _handleDisconnectionFromServer():
	rds.fdgui.handleDisconnectionFromServer()
	_showLoadingBar(False)

	_deactivateChatWindow()

	rds.startupGUI.fader.alpha = 1.0
	rds.startupGUI.script.showCharacterScreen( lambda: None, False, 2.0 )
	_setMainMenu( [ ('Disconnected from Server', None ) ], None )

	if rds.selfDisconnect:
		addMsg('Client disconnected itself from server')
	else:
		addMsg('Client lost connection to server')

	_showLogoScreen( True, False )

	BigWorld.resetEntityManager( False, True )
	BigWorld.clearAllSpaces( True )

	yield BWWaitForPeriod( 2.0 )

	_startMainMenu()


def _disconnectFromServer():
	'''Disconnect client from server.
	'''
	if BigWorld.server() is not None:
		global rds
		rds.selfDisconnect = True
		# Temporary solution until there is an official function that
		# gets rid of the proxy on the base.
		if BigWorld.player() is not None:
			try:
				BigWorld.player().base.logOff()
			except:
				pass

		if rds.clientSpace != None:
			BigWorld.resetEntityManager()
			BigWorld.releaseSpace(rds.clientSpace)
			rds.clientSpaceMapping = None
			rds.clientSpace = None

		_showLogoScreen( True, False )
		BigWorld.disconnect()

	WeatherSystem.newWeather().toggleRandomWeather( False )

def _serverNetName(details):
	'''Given a ServerDiscoveryDetails object,
	returns the network name for it.
	'''
	name = _serverDottedHost(details.ip)
	if details.port:
		name += ':%d' % details.port
	return name


def _serverNiceName(details):
	'''Given a ServerDiscoveryDetails object,
	returns a human readable name for it.
	'''
	name = details.hostName
	if not name:
		name = _serverDottedHost(details.ip)
	if details.port:
		name += ':%d' % details.port
	if details.ownerName:
		name += ' (' + details.ownerName + ')'
	return name


def _serverDottedHost(ip):
	'''Given a numeric IP address, returns a
	four digit, dot notation IP address.
	'''
	return '%d.%d.%d.%d' % (
		(ip>>24) & 0xFF,
		(ip>>16) & 0xFF,
		(ip>>8)  & 0xFF,
		(ip>>0)  & 0xFF)

############################################################################
# The following functions implement a loading screen overlay to hide the
# initial chunk loading phase.
############################################################################

def disableWorldDrawing():
	BigWorld.worldDrawEnabled(False)
	if BigWorld.player() and hasattr(BigWorld.player(), 'hud') and BigWorld.player().hud:
		GUI.delRoot(BigWorld.player().hud)

def enableWorldDrawing():
	BigWorld.worldDrawEnabled(True)
	if BigWorld.player() and hasattr(BigWorld.player(), 'hud') and BigWorld.player().hud:
		GUI.addRoot(BigWorld.player().hud)


def _showLogoScreen( active, fadeIn = True ):
	'''Shows/hide the BigWorld logo screen.
	'''
	if fadeIn:
		fadeTime = rds.loadingScreen.fader.speed
	else:
		fadeTime = 0.0

	if active:
		rds.loadingScreen.fader.value = 1.0
		BigWorld.callback( fadeTime, disableWorldDrawing )
	else:
		rds.loadingScreen.fader.value = 0.0
		enableWorldDrawing()

	BigWorld.callback( fadeTime, partial( rds.loadingScreen.script.active, active ) )
	if not fadeIn:
		rds.loadingScreen.fader.reset()



def _showLoadingBar(active):
	'''Shows/hide the loading bar.
	'''
	global rds
	rds.loadingScreen.bar.visible  = active
	rds.loadingScreen.back.visible = active
	if not active:
		rds.loadingScreen.script.cancel()


def _recommendSettings():
	# if timed out and a lower graphics setting exists then print out a message
	# to indicate this, unless the user cancelled the loading screen.

	if rds.loadingScreen.fader.value == 0.0:
		return

	presets	= GraphicsPresets()
	doNotify = False

	if presets.selectedOption == -1:
		doNotify = True
	else:
		for i in range(0, len(presets.entryNames)):
			presetMsg = presets.entryNames[i]
			if presetMsg != "Low" and presets.selectedOption == i:
				doNotify = True
				break

	if doNotify == True:
		addMsg("FantasyDemo loading timeout please try a lower graphics setting")


def _startChunkLoadingBar(finishedCallback):
	'''Starts the chunk loaing progress bar.
	'''
	global rds
	if rds.loadingScreen == None:
		rds.loadingScreen = GUI.load('gui/loading_screen.gui')

	rds.loadingScreen.script.setProgress(0)
	rds.loadingScreen.script.reset(0)

	def _finishedLoading( timedOut = False ):
		if timedOut:
			_recommendSettings()
		BigWorld.worldDrawEnabled(True)

		_activateChatWindow()

		rds.loadingScreen.script.reset(0)
		finishedCallback()

	# Loading progress bar measures first 500 metres
	rds.loadingScreen.script.start(500.0, _finishedLoading)
	addMsg('Loading World Data')

############################################################################
# The following functions implement a feature that times the loading of a
# space.
############################################################################

def _loadTimerStart( spaceName ):
	# Start loading requested space without loading screen
	startTime = time.time()
	_exploreOffline( spaceName, False )
	_showLogoScreen( False )

	# Start the callback chain to do the timing
	print "Load timer: Processing space '", spaceName, "'"
	BigWorld.callback( 1.0, partial( _loadTimerTick, spaceName, startTime ) )

def _loadTimerTick( spaceName, startTime ):
	s = BigWorld.spaceLoadStatus()
	if s < 1.0:
		# Tick
		print "Load timer: Space load status =", s
		BigWorld.callback( 1.0, partial( _loadTimerTick, spaceName, startTime ) )
	else:
		# End
		timeNow = time.time()
		elapsed = timeNow - startTime
		_loadTimerFinish( spaceName, elapsed )

def _loadTimerFinish( spaceName, elapsedTime ):

	# declare filename and default mode
	filename = "..\game\load_timer.csv"
	mode = "a"

	print "Load timer: Space loaded in", elapsedTime, "seconds. Writing results to", filename

	# open file and write
	f = open( filename, mode )
	try:
		f.write( '"' + spaceName + '","' + str(elapsedTime) + '",\n' )
	finally:
		f.close()

	# ... and quit so we can run again.
	BigWorld.quit()
			
############################################################################
# The following functions implement the automatic profiling
############################################################################

def _runProfiler( spaceName, cvsPrefix):
	# Start loading requested space without loading screen
	_exploreOffline( spaceName, False )
	_showLogoScreen( False )	
	
	def _loadTick( spaceName, cvsPrefix):
		if BigWorld.spaceLoadStatus() < 1.0:
			BigWorld.callback(1.0,partial(_loadTick,spaceName, cvsPrefix))
		else:
			_runProfilerStart( spaceName, cvsPrefix )

	BigWorld.callback(1.0,partial(_loadTick, spaceName, cvsPrefix))
	
def _runProfilerStart ( spaceName, cvsPrefix ):
	BigWorld.runProfiler('camera node0', 3 , cvsPrefix)



# -----------------------------------------------------------------------------
# Method: onChangeEnvironments
# Description:
#	- This is called automatically when player moves from inside to outside
#	environment, or vice versa.
#	- It should be used to adapt any personality related data (eg, camera
#	position/nature, etc).
# -----------------------------------------------------------------------------
def onChangeEnvironments(inside):
	global rds
	rds.inside = inside
	rds.updatePivotDist()
	for listener in rds.environmentChangeListeners.keys():
		listener(inside)


def addChangeEnvironmentsListener(listener):
	global rds
	rds.environmentChangeListeners[listener] = ''


def delChangeEnvironmentsListener(listener):
	try:
		if 'rds' in globals():
			del rds.environmentChangeListeners[listener]
	except:
		pass


def onGeometryMapped(spaceID, spacePath):
	rds.spaceNameMap[spaceID] = spacePath
	onChangeEnvironments(False)
	if rds.clientSpace == spaceID:
		rds.clientSpaceName = spacePath
		online = BigWorld.server() if BigWorld.server() else 'offline'
		print 'Entering space: %s (server: %s)' % (spacePath, online)


# -----------------------------------------------------------------------------
# Method: onCameraSpaceChange
# Description:
#	- This is called automatically when the camera moves from one space to
#	another.
#	- The space ID and space.settings datasection is passed in to this function
# -----------------------------------------------------------------------------
def onCameraSpaceChange(spaceID, spaceSettings):
	rds.cameraSpaceID = spaceID
	import WeatherSystem
	WeatherSystem.newWeather().onChangeSpace()
	try:
		weather = rds.lastWeatherSync[spaceID]
	except KeyError:
		rds.lastWeatherSync[spaceID] = spaceSettings.readString("defaultWeather", "Clear")
		weather = rds.lastWeatherSync[spaceID]

	#This line only really to stop problems at startup
	if BigWorld.player() is not None:
		WeatherSystem.newWeather().summon( weather, immediate = True, serverSync = True )


def onRecreateDevice():
	'''Called by BigWorld whenever the graphics device is reset
	(usually, after a screen resise or switching full screen mode).
	'''
	for listener in rds.deviceListeners.keys():
		listener.onRecreateDevice()

	rds.startupGUI.script.doLayout( None )
	rds.editField.script.adjustFont(BigWorld.screenWidth())
	rds.console.script.onRecreateDevice()


def addDeviceListener(listener):
	global rds
	rds.deviceListeners[listener] = ''


def delDeviceListener(listener):
	try:
		if 'rds' in globals():
			del rds.deviceListeners[listener]
	except:
		pass


# -----------------------------------------------------------------------------
# Method: enableEnvironmentSync
# Description:
#	- This method is a demo-only and enables environment synchronisation.
#	Server time of day and weather updates will be displayed on the client.
# -----------------------------------------------------------------------------
def enableEnvironmentSync():
	if hasattr( BigWorld, 'setEnvironmentSync' ):
		BigWorld.setEnvironmentSync( True )
		addMsg("Environment sync enabled")
		spaceID = BigWorld.player().spaceID
		BigWorld.player().cell.resyncServTime( spaceID )
		import WeatherSystem
		WeatherSystem.newWeather().summon( rds.lastWeatherSync[spaceID], \
											immediate = True, serverSync = True )


# -----------------------------------------------------------------------------
# Method: disableEnvironmentSync
# Description:
#	- This method is a demo-only and disables environment synchronisation.
#	Server time of day and weather updates will be ignored.
# -----------------------------------------------------------------------------
def disableEnvironmentSync():
	if hasattr( BigWorld, 'setEnvironmentSync' ):
		BigWorld.setEnvironmentSync( False )
		addMsg("Environment sync disabled")


# -----------------------------------------------------------------------------
# Method: onWeatherChange
# Description:
#	- This method is called when the weather space data is updated from the
#	server.  This feature is demo-only and is not compiled into the consumer
#	client release build.
# -----------------------------------------------------------------------------
def onWeatherChange( spaceID, weather ):
	import Helpers.ConsoleCommands

	global rds
	rds.lastWeatherSync[spaceID] = weather

	#If this is a weather change for the current space, then update the
	#weather gracefully (i.e. not immediate)
	if rds.cameraSpaceID == spaceID:
		try:
			apply = BigWorld.getEnvironmentSync()
		except KeyError:
			apply = True

		if apply:
			import WeatherSystem
			WeatherSystem.newWeather().summon( weather, immediate = False, serverSync = True )


# -----------------------------------------------------------------------------
# Method: fini
# Description:
#	- The fini function is called when the client is about to shutdown.  It
#		should be used to clean up the game.
# -----------------------------------------------------------------------------
def fini():
	if BigWorld.player() != None:
		try:
			BigWorld.player().base.logOff()
		except:	pass
	BigWorld.disconnect()
	BigWorld.savePreferences()

	import WeatherSystem
	WeatherSystem.fini()

	BigWorld.resetEntityManager()
	BigWorld.clearAllSpaces()

	global rds

	rds.fdgui.fini()
	rds.fini()

	del rds


# -----------------------------------------------------------------------------
# Method: onTimeOfDayLocalChange
# Description:
#	- This is called automatically when Time of Day changes on the client
#	- It should only be used to sync game time from client to server
# -----------------------------------------------------------------------------
def onTimeOfDayLocalChange( gameTimeInHrs, secondsPerGameHour ):
	global rds

	if hasattr( BigWorld, 'getEnvironmentSync' ):
		if not BigWorld.getEnvironmentSync():
			return

	if secondsPerGameHour > 0.0:
		gameSecondsPerSecond = 3600.0/secondsPerGameHour
	else:
		gameSecondsPerSecond = 0.0
	gameTimeInSeconds = gameTimeInHrs * 3600.0

	try:
		BigWorld.player().cell.syncServTime(
			BigWorld.player().spaceID,
			gameTimeInSeconds, gameSecondsPerSecond )
	except:
		pass


# -----------------------------------------------------------------------------
# Method: handleKeyEvent
# Description:
#	- This is called automatically when a key is pressed.
# -----------------------------------------------------------------------------
def handleKeyEvent(down, key, mods):
	global rds

	# scroll player chat console if we can
	chatConsole = rds.fdgui.chatWindow
	if chatConsole and chatConsole.script.isActive:
		if down and key == KEY_PGUP:
			chatConsole.script.scrollUp()
			return True
		elif down and key == KEY_PGDN:
			chatConsole.script.scrollDown()
			return True
		elif down and (key == KEY_RETURN and mods == 0):
			# check if the in game menu is active

			if not rds.fdgui.inGameMenu.script.isActive and not chatConsole.script.editing:
				chatConsole.script.edit(1)  # if already editing then
				return True		    #  it'll catch return above
		elif down and (key == KEY_ESCAPE and mods == 0) and chatConsole.script.component.visible:
			chatConsole.script.hideNow()
			return True


	# try the gui
	PyGUI.handleKeyEvent( down, key, mods )
	handled =  GUI.handleKeyEvent(down, key, mods)
	if handled:
		return True

	if down and key == KEY_F4 and mods == MODIFIER_ALT:
		if BigWorld.player() != None:
			try:
				BigWorld.player().base.logOff()
			except:	pass

	return False


class FantasyDemoActionHandler( BWKeyBindings.BWActionHandler ):

	# handle the change camera mode key event
	@BWKeyBindings.BWKeyBindingAction( "CameraKey" )
	def cameraKey( self, isDown ):
		if isDown:
			handleCameraKey()

	@BWKeyBindings.BWKeyBindingAction( "DisconnectFromServer" )
	def disconnectFromServer( self, isDown ):
		if isDown and BigWorld.server() is not None:
			_disconnectFromServer()
			return True
		else:
			return False

	@BWKeyBindings.BWKeyBindingAction( "CancelLoading" )
	def cancelLoading( self, isDown ):
		if isDown and BigWorld.player() is not None and not BigWorld.worldDrawEnabled():
			addMsg("User cancelled loading screen.")
			BigWorld.worldDrawEnabled(True)
			_showLogoScreen(False)
			_showLoadingBar(False)

			_activateChatWindow()

			return True
		else:
			return False

	@BWKeyBindings.BWKeyBindingAction( "EnableEnvironmentSync" )
	def enableEnvironmentSync( self, isDown ):
		if isDown:
			enableEnvironmentSync()
			return True
		else:
			return False

	@BWKeyBindings.BWKeyBindingAction( "DisableEnvironmentSync" )
	def disableEnvironmentSync( self, isDown ):
		if isDown:
			disableEnvironmentSync()
			return True
		else:
			return False


# -----------------------------------------------------------------------------
# Method: setCursorCameraSource
# Description:
#	- This is called to override the source matrix provider for the cursor camera.
# -----------------------------------------------------------------------------
def setCursorCameraSource( source ):
	rds.cc.source = source

# -----------------------------------------------------------------------------
# Method: handleCameraKey
# Description:
#	- This is called in response to the 'next camera' key being pressed.
# -----------------------------------------------------------------------------
def handleCameraKey( forceToStandardCamera = False ):
	if isinstance( BigWorld.player(), Avatar.Avatar) and BigWorld.player().firstPerson:
		resetCameraOffset()
		cameraDistanceOverride(rds.defaultPivotMaxDist)
		BigWorld.projection().nearPlane = rds.defaultNearPlane
		BigWorld.player().toggleFirstPersonMode(False)
		return

	if forceToStandardCamera:
		rds.cameraKeyIdx = 0
	else:
		rds.cameraKeyIdx = (rds.cameraKeyIdx + 1) % 3
	BigWorld.target.isEnabled = 1

	pivotMaxDist = 2
	import Ripper
	if isinstance( BigWorld.player(), Ripper.PlayerRipper):
		pivotMaxDist = 3.5

	if rds.cameraKeyIdx == 0:
		rds.cc.inaccuracyProvider=None
		rds.cc.reverseView = False
		rds.updatePivotDist()
		cameraType(0)

	elif rds.cameraKeyIdx == 1:
		cameraType(0)
		#disable targeting system
		BigWorld.target.clear()
		BigWorld.target.isEnabled = 0
		#enable orbit camera
		v1 = Vector4LFO()
		v1.waveform = 'SAWTOOTH'
		v1.period = 20.0
		v1.amplitude = (3.141592654*2.0)
		v2 = Vector4(1,0,0,0)
		v = Vector4Product()
		v.a=v1
		v.b=v2
		rds.cc.inaccuracyProvider=v
		rds.cc.pivotMaxDist = pivotMaxDist
		rds.cc.maxDistHalfLife = 1.5

	elif rds.cameraKeyIdx == 2:
		cameraType(3)
		resetCameraOffset()
		rds.cc.inaccuracyProvider=None
		rds.cc.reverseView = False
		rds.updatePivotDist()

	# check for wow mode
	player = BigWorld.player()
	if player is not None and isinstance( player, Avatar.Avatar ) and player._useWoWMode:
		setCursorCameraSource( player.entityDirProvider )


# -----------------------------------------------------------------------------
# Method: handleMouseEvent
# Description:
#	- This is called automatically when a mouse event is generated.
# -----------------------------------------------------------------------------
def handleMouseEvent(dx, dy, dz):
	global rds

	# try the gui
	PyGUI.handleMouseEvent(dx, dy, dz)
	GUI.handleMouseEvent(dx, dy, dz)

	player = BigWorld.player()
	if BigWorld.camera() != rds.frc:
		if rds.middleMouseButtonDown and hasattr(rds.cc.source,'yaw'):
			msens = BigWorld.dcursor().mouseSensitivity * BigWorld.projection().fov / 1.04719755 #60 degrees
			newYaw = rds.cc.source.yaw + dx * BigWorld.dcursor().mouseHVBias * msens
			if BigWorld.dcursor().invertVerticalMovement:
				newPitch = rds.cc.source.pitch + dy * (1.0 - BigWorld.dcursor().mouseHVBias) * msens
			else:
				newPitch = rds.cc.source.pitch - dy * (1.0 - BigWorld.dcursor().mouseHVBias) * msens

			if newPitch > BigWorld.dcursor().maxPitch:
				newPitch = BigWorld.dcursor().maxPitch
			elif newPitch < BigWorld.dcursor().minPitch:
				newPitch = BigWorld.dcursor().minPitch

			# set the camera yaw and pitch
			rds.cc.source.setRotateYPR((newYaw, newPitch, rds.cc.source.roll))
			# we want to make the player 'looking' at the same direction as the camera
			BigWorld.dcursor().yawPitch(BigWorld.dcursor().yaw, newPitch)

		elif hasattr(rds, 'dYaw'):
			# fix the camera offset based on current player direction
			msens = BigWorld.dcursor().mouseSensitivity * BigWorld.projection().fov / 1.04719755 #60 degrees
			if BigWorld.dcursor().invertVerticalMovement:
				newPitch = rds.cc.source.pitch + dy * (1.0 - BigWorld.dcursor().mouseHVBias) * msens
			else:
				newPitch = rds.cc.source.pitch - dy * (1.0 - BigWorld.dcursor().mouseHVBias) * msens
			if newPitch > BigWorld.dcursor().maxPitch:
				newPitch = BigWorld.dcursor().maxPitch
			elif newPitch < BigWorld.dcursor().minPitch:
				newPitch = BigWorld.dcursor().minPitch

			rds.cc.source.setRotateYPR((BigWorld.dcursor().yaw + rds.dYaw,
										newPitch,
										rds.cc.source.roll))

		# don't try to move camera if player
		# is not the standard Player Avatar.
		if isinstance(BigWorld.player(), Avatar.PlayerAvatar):
			if dz != 0:
				clicks = dz/120.0	# add 20% for each notch... or something
				nextDist = math.exp(math.log(rds.cc.targetMaxDist) - clicks*math.log(1.2))
			if dz > 0:
				if nextDist < 0.5 and rds.cc.pivotMaxDist > 0.75:
					nextDist = 0.5	# don't go to first person until smoothly moved in close
				if nextDist >= 0.5:
					cameraDistanceOverride(nextDist)
					if nextDist <= rds.cameraCloseUpTrigger:
						BigWorld.projection().nearPlane = FIRST_PERSON_NEAR_CLIP_PLANE
				else:
					if player and player.inWorld and not player.firstPerson:
						player.toggleFirstPersonMode(True)
			elif dz < 0:
				if nextDist > 15.0: nextDist = 15.0
				if player and player.inWorld and hasattr( player, 'firstPerson' ) and player.firstPerson:
					if player.toggleFirstPersonMode(False):
						resetCameraOffset()
				else:
					cameraDistanceOverride(nextDist)
				if nextDist > rds.cameraCloseUpTrigger:
					BigWorld.projection().nearPlane = rds.defaultNearPlane

	if player and player.inWorld and hasattr(player, 'handleMouseEvent'):
		player.handleMouseEvent(dx, dy, dz)

	if rds.middleMouseButtonDown:
		return 1

	return 0


# -----------------------------------------------------------------------------
# Method: resetCameraOffset
# Description:
#	- Reset the camera facing at the back of player
# -----------------------------------------------------------------------------
def resetCameraOffset():
	global rds

	if id(rds.cc.source) != id(BigWorld.dcursor().matrix):
		rds.cc.source = BigWorld.dcursor().matrix
	if hasattr(rds, 'dYaw'):
		delattr(rds, 'dYaw')


# -----------------------------------------------------------------------------
# Method: resetCamera
# Description:
#	- Reset the camera
# -----------------------------------------------------------------------------
def resetCamera():
	global rds

	resetCameraOffset()
	cameraDistanceOverride(rds.defaultPivotMaxDist)
	BigWorld.projection().nearPlane = rds.defaultNearPlane
	BigWorld.player().toggleFirstPersonMode(False)


# -----------------------------------------------------------------------------
# Method: handleAxisEvent
# Description:
#	- This is called automatically when an axis event is generated.
# -----------------------------------------------------------------------------
def handleAxisEvent(axis, value, dTime):
	# try the gui
	return GUI.handleAxisEvent(axis, value, dTime)


def _activateChatWindow():
	global rds

	rds.console.script.active(False)

	chatConsole = rds.fdgui.chatWindow
	if chatConsole:
		chatConsole.script.active(True)

def _deactivateChatWindow():
	global rds

	rds.console.script.active(True)

	chatConsole = rds.fdgui.chatWindow
	if chatConsole:
		chatConsole.script.clear()
		chatConsole.script.active(False)




############################################################################
# Resource Updater notification handlers								   #
############################################################################

# -----------------------------------------------------------------------------
# Method: onResUpdateDownloadBegin
#
# A download has started, aiming to bring the given version point to the
# given version number. The download will occur in the background, even
# if these resources are required to enable entities, i.e. required to
# receive player data from the server. The first 3 elements of the
# progressV4Provider will indiciate the progress of the download:
# x: version number currently being downloaded
# y: files progress within current version number
# z: byte progress within file
# Note: If through script action, directly or indirectly, resources
# need to be loaded in the main from a non-root version point that is
# not up-to-date, then the main thread will block until those resources have
# been downloaded. The game will not progress except for processing messages
# from the server. This would be very bad! However, since scripts should
# never be loading resources in the main thread anyway - for the relatively
# small loading pause that would result - avoiding this is no extra burden.
# -----------------------------------------------------------------------------
def onResUpdateDownloadBegin(version, point, progressV4Provider):
	print 'onResUpdateDownloadBegin', version, point

# -----------------------------------------------------------------------------
# Method: onResUpdateDownloadEnd
#
# A download signalled above has ended. There may be a short time
# (up to one frame) when progressV4Provider.x is -1 before this function
# is called.
# Note: onResUpdateAutoRelaunch might be called before this function
# if an auto relaunch is going to occur.
# -----------------------------------------------------------------------------
def onResUpdateDownloadEnd(version, point, progressV4Provider):
	print 'onResUpdateDownloadEnd', version, point

# -----------------------------------------------------------------------------
# Method: onResUpdateLoadin
#
# It is time to begin loading in the updated resources in the client.
# Since the client doesn't yet have this capability for some resources,
# for now we must relaunch the client here. But give the user some
# notice first. (If we don't disconnect after a few minutes, the server
# will kick us off.)
# -----------------------------------------------------------------------------
def onResUpdateLoadin():
	print 'onResUpdateLoadin'
	BigWorld.callback(30, relaunchNow)

# The user has had enough time to prepare for the relaunch, so do it
def relaunchNow():
	try:
		BigWorld.player().base.logOff()
	except:	pass

	print 'Relaunching now'
	BigWorld.resUpdateInstallAndRelaunch()

# -----------------------------------------------------------------------------
# Method: onResUpdateAutoRelaunch
#
# We logged in but didn't enable entities / create a player, because
# out resources were out of date. We now have the new resources and they
# have been installed. The client is going to relaunch so it can use them
# as soon as this call returns.
# Note: onResUpdateDownloadBegin might not yet have been received if the update
# was very small or was a rollback. If it was received, then the corresponding
# onResUpdateDownloadEnd might not yet have been received before this call.
# -----------------------------------------------------------------------------
def onResUpdateAutoRelaunch():
	print 'onResUpdateAutoRelaunch'


def create(type):
	player = BigWorld.player()
	return BigWorld.createEntity(type, player.spaceID, 0, player.position, (0,0,0), {})


# ------------------------------------------------------------------------------
# Section: Macro expansion
# ------------------------------------------------------------------------------

# These are the python console macro expansions supported by FantasyDemo
PYTHON_MACROS = {
	"p":"BigWorld.player()",
	"t":"BigWorld.target()",
	"B":"BigWorld",
	"G":"doppleganger()",
	"a":"BigWorld.createEntity(\"Avatar\", BigWorld.player().spaceID, 0, BigWorld.player().position,(0,0,0),{})",
	"r":"BigWorld.entity(BigWorld.createEntity(\"Ripper\", BigWorld.player().spaceID, 0, BigWorld.player().position,(0,0,0),{}))",
	"s":"BigWorld.createEntity(\"Seat\", BigWorld.player().spaceID, 0,BigWorld.player().position,(0,0,0),{\"seatType\":1})",
	"e":"BigWorld.createEntity(\"Effect\", BigWorld.player().spaceID, 0,BigWorld.player().position,(0,0,BigWorld.player().yaw),{\"effectType\":6})",
	"o":"BigWorld.createEntity(\"Effect\", BigWorld.player().spaceID, 0,BigWorld.player().position,(0,0,0),{\"effectType\":3})",
	"S":"BigWorld.createEntity(\"Effect\", BigWorld.player().spaceID, 0,BigWorld.player().position,(0,0,0),{\"effectType\":4})",
	"v":"BigWorld.createEntity(\"Effect\", BigWorld.player().spaceID, 0,(-79.4,78.6,298.4),(0,0,0),{\"effectType\":6})",
	"V":"BigWorld.createEntity(\"VideoScreen\", BigWorld.player().spaceID, 0, BigWorld.player().position,(0,0,0),{})",
	"A":"m=BigWorld.Model('sets/items/xbow_bolt.model'); m.position=(0,1.2,-5); m.yaw = -1.55; BigWorld.player().addModel(m); h=BigWorld.Homer(); h.target=BigWorld.player().model; h.offset=(0,1.2,0); h.speed=1; h.turnRate=1; h.tripTime=8"
}

import re

# Implementation for BWPersonality.expandMacros() callback
def expandMacros( line ):

	# Glob together the keys from the macros dictionary into a pattern
	patt = "\$([%s])" % "".join( PYTHON_MACROS.keys() )

	def repl( match ):
		return PYTHON_MACROS[ match.group( 1 ) ]

	return re.sub( patt, repl, line )


rds = RDShare()
rds.init()
