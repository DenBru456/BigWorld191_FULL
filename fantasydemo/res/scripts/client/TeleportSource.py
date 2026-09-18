import BigWorld
import Pixie
import Keys
import Math
import GUI
from Helpers import Bloom
import FantasyDemo as FantasyDemo
from bwdebug import INFO_MSG
from Helpers import Caps
from functools import partial

# ------------------------------------------------------------------------------
# Section: Teleportation Methods
# ------------------------------------------------------------------------------

teleportGui = None
wasTargetingEnabled = False
teleportParticles = None

teleportXML = "partilces/teleport.xml"
teleportScreen = "gui/teleport_screen.gui"


def instantTeleport( dst ):
	BigWorld.player().base.teleportTo( dst )


def startTeleportation( dst ):	
	global teleportParticles
	
	#don't let us teleport again while in mid-flight
	if teleportGui != None:
		FantasyDemo.addChatMsg( -1, "Already teleporting please wait" )
		return
	
	if not teleportParticles:
		teleportParticles = Pixie.createBG("particles/teleport.xml", partial( attachTeleportParticles, dst ) )
	else:
		attachTeleportParticles( dst, teleportParticles )	
		
		
def attachTeleportParticles( dst, particles ):
	global teleportParticles
	
	teleportParticles = particles	
	teleportParticles.clear()
	
	BigWorld.player().model.root.attach( teleportParticles )
	BigWorld.player().actionCommence()
	
	# let teleport particles animation play a while before blurring screen
	BigWorld.callback( 2.5, lambda:blurScreen( dst ) )
	
	
def blurScreen( dst ):
	global teleportGui
	global wasTargetingEnabled
	
	wasTargetingEnabled = BigWorld.target.isEnabled
	BigWorld.target.isEnabled = False
	BigWorld.target.clear()
	
	# create teleport gui screen
	teleportGui = GUI.load( teleportScreen )
	teleportGui.script.active(1)		
	teleportGui.script.preTeleport( lambda:teleportPlayer( dst ) )
	
	
def teleportPlayer( dst ):
	global teleportGui
	
	INFO_MSG( "Disabling World Drawing" )
	#BigWorld.worldDrawEnabled(False)
	FantasyDemo.disableWorldDrawing()
	
	BigWorld.player().base.teleportTo( dst )
	BigWorld.callback( 0.5, startChangeSpaceCheck )
	

#This method checks whether the player is in a different space
#than the camera, and moves the camera in there.  This starts
#the chunk loading process beginning.
def startChangeSpaceCheck( counter = 0 ):
	if BigWorld.cameraSpaceID() != BigWorld.player().spaceID:
		BigWorld.cameraSpaceID( BigWorld.player().spaceID )
		onChangeSpace()
	else:
		if counter < 25:
			BigWorld.callback( 0.5, partial( startChangeSpaceCheck, counter + 1 ) )
		else:
			teleportGui.script.start( -1.0, endTeleportation )
			
			
#start Progress Check for the new space to load
def onChangeSpace():
	global teleportGui
	teleportGui.script.start( -1.0, endTeleportation)

		
def endTeleportation( didNotCompletelyLoadSpace = False ):
	global teleportGui
	global wasTargetingEnabled
	global teleportParticles
	
	INFO_MSG( "Enabling World Drawing" )	
	#BigWorld.worldDrawEnabled(True)
	FantasyDemo.enableWorldDrawing()
	
	BigWorld.player().actionComplete()
	BigWorld.player().model.root.detach( teleportParticles )
	
	BigWorld.target.isEnabled = wasTargetingEnabled
	
	teleportGui.script.active(0)
	teleportGui = None


def cleanupTeleportGUI():	
	global teleportGui
	if teleportGui != None:
		teleportGui.script.active(0)
		teleportGui = None


# ------------------------------------------------------------------------------
# Section: A class to allow testing of the teleport blur effect
# ------------------------------------------------------------------------------

class TestTeleportBlur:
	def __init__( self ):
		self.component = GUI.Gobo( "system/maps/col_white.dds" )
		self.component.size = (2,2)
		self.shader = GUI.AlphaShader()
		self.shader.alpha = 0
		self.shader.reset()

		self.component.addShader( self.shader )
		self.component.materialFX = "BLEND"

		Bloom.selectPreset("Gobo")
		GUI.addRoot( self.component )

	def setBlurAmount( self, amount):
		self.shader.speed = 0
		self.shader.alpha = amount

	def killTeleportBlur( self ):
		GUI.delRoot( self.component )
		
# ------------------------------------------------------------------------------
# Section: class TeleportSource
# ------------------------------------------------------------------------------

MODEL_NAME = "sets/dungeon/props/honourstone.model" 
nameSeparator = "/"

class TeleportSource( BigWorld.Entity ):

	def __init__( self ):
		BigWorld.Entity.__init__( self )

	def modelName( self ):
		# TODO: Use model type.
		return MODEL_NAME

	def prerequisites( self ):
		return [ self.modelName() ]

	def onEnterWorld( self, prereqs ):
		self.prereqs = prereqs
		self.set_modelType()

	def onLeaveWorld( self ):
		self.model = None
		self.prereqs = None

	def set_modelType( self, oldType= None ):
		self.model = self.prereqs[ self.modelName() ]
		self.model.motors[0].entityCollision = 1
		self.model.motors[0].collisionRooted = 1
		self.targetCaps = [ Caps.CAP_CAN_USE ]

	# Player wants to use Teleport Source
	def use( self ):
		BigWorld.player().tryToTeleport( self.spaceLabel + nameSeparator + self.destination, True )

	def name( self ):
		return "Teleport to " + self.spaceLabel + nameSeparator + self.destination

# TeleportSource.py
