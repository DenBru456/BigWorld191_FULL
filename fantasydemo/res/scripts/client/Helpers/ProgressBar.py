from PyGUI import PyGUIBase
import BigWorld
import GUI
import ResMgr
import FantasyDemo
import Bloom

"""
This classes implements the interface to GUI Progress Bars.
"""
class IProgressBar( PyGUIBase ):

	factoryString="PyGUI.IProgressBar"

	def __init__( self, component ):
		PyGUIBase.__init__( self, component )

	def setMinMax( self, min, max ):
		pass

	def setProgress( self, value ):
		pass

	def reset( self, value ):
		pass

	def addMessage( self, str ):
		pass

	def appendMessage( self, str ):
		pass



"""
This classes implements a simple GUI progress bar, with a scrolling
text region for status messages
"""
class ProgressBar( IProgressBar ):

	factoryString="PyGUI.ProgressBar"

	def __init__( self, component ):
		self.min = 0.0
		self.max = 1.0
		self.msgs = []
		IProgressBar.__init__(self,component)

	def setMinMax( self, min, max ):
		self.min = min
		self.max = max

	def setProgress( self, value ):
		#remap value into the correct range
		range = self.max - self.min
		value = self.min + value * range
		self.component.bar.clipper.value = value
		self.component.bar.clipper.reset()

	def reset( self, value ):
		self.component.bar.clipper.reset()

	def addMessage( self, str ):
		FantasyDemo.rds.console.script.addMsg( str, 0 )

	def appendMessage( self, str ):
	 	FantasyDemo.rds.console.script.appendMsg( str, 0 )

	def onLoad( self, section ):
		PyGUIBase.onLoad( self, section )
		FantasyDemo.initConsole()

	def onBound( self ):
		IProgressBar.onBound( self )

"""
This classes implements a progress bar for chunk loading.
The component tree should have :
- screen
	- fader (AlphaGUIShader)
	- back
	- bar
		- clipper (ClipGUIShader)
"""
class ChunkLoadingProgressBar( ProgressBar ):

	factoryString="PyGUI.ChunkLoadingProgressBar"

	def __init__( self, component ):
		ProgressBar.__init__( self, component )
		self.phase1Ratio = 1.0
		self.checkRate = 0.05
		self.timeout = 60
		self.last = 0.0
		self.inPhase1 = True
		self.cancelled = False

	def start( self, distance, callbackFn ):
		self.distance = distance
		self.last = 0.0
		self.callbackFn = callbackFn
		self.cancelled = False
		self.progressCheck( BigWorld.time() + self.timeout )

	def cancel( self ):
		self.cancelled = True

	def progressCheck( self, endTime ):
		timedOut = (endTime < BigWorld.time())
		finished = timedOut
		if not finished:
			status = BigWorld.spaceLoadStatus( self.distance )
			finished = (status > 0.95)

		if finished:
			self.setProgress(1.0)
			if self.callbackFn and not self.cancelled:
				if timedOut:
					self.callbackFn( True )
				else:
					self.callbackFn()
		else:
			if status > self.last:
				self.setProgress( status )
				self.last = status
			BigWorld.callback( self.checkRate, lambda:self.progressCheck(endTime ) )

	def onLoad( self, section ):
		ProgressBar.onLoad( self, section )
		self.phase1Ratio = section.readFloat( "phase1Ratio", self.phase1Ratio )
		self.checkRate = section.readFloat( "checkRate", self.checkRate )
		self.timeout = section.readInt( "timeout", self.timeout )
		if section.readBool( "useDefaultLoadingScreen", True ):
			self.replaceLoadingScreen(section)
		self.startPhase(1)
		self.active(True)

	def replaceLoadingScreen( self, section ):
		sect = ResMgr.openSection( "resources.xml/system" )
		self.component.textureName = sect.readString("loadingScreen")

	def startPhase( self, num ):
		if num == 1:
			self.setMinMax( 0.0, self.phase1Ratio )
		else:
			self.setMinMax( self.phase1Ratio, 1.0 )


"""
This classes implements a progress bar for chunk loading after a teleport.
It is similar to the standard chunk loading progress bar, but instead
of throwing up a splash screen, it uses a GOBO component to blur the
background.
useDefaultLoadingScreen is ignored for this component
"""
class TeleportProgressBar( ChunkLoadingProgressBar ):

	factoryString="PyGUI.TeleportProgressBar"

	def __init__( self, component ):
		ChunkLoadingProgressBar.__init__( self, component )

	#Note - intentionally stubbing out base class method
	def replaceLoadingScreen( self, section ):
		pass

	def preTeleport( self, callbackFn ):
		Bloom.selectPreset("Gobo")
		self.component.fader.value = 1.0
		BigWorld.callback( self.component.fader.speed, lambda:self.onBlurred(callbackFn) )

	def onBlurred( self, callbackFn ):
		self.component.freeze()
		Bloom.selectPreset("Standard")
		if callbackFn:
			callbackFn()
