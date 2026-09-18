import BigWorld
from Helpers import PyGUI
from functools import partial
from Helpers.BWCoroutine import *

class MainMenu(PyGUI.PyGUIBase):

	factoryString="MainMenuGUI.MainMenu"	

	def __init__( self, component = None ):
		PyGUI.PyGUIBase.__init__( self, component )
		self.mainmenuComponent  = None

	@BWMemberCoroutine
	def showCharacterScreen( self, active, fadeSpeed = 2.0 ):
		if active:
			self.component.background.fader.speed = fadeSpeed
			self.component.background.fader.value = 0.0
			self.mainmenuComponent.position = (-0.9, 0.0, 0.5)
			self.mainmenuComponent.width = 0.7
			self.component.scrollUp.position.x = -0.1
			self.component.scrollDown.position.x = -0.1
			self.doLayout( None )			
			
			BigWorld.worldDrawEnabled( True )

			yield BWWaitForPeriod( fadeSpeed )

		else:
			self.component.background.fader.speed = fadeSpeed
			self.component.background.fader.value = 1.0
			self.mainmenuComponent.position = (-0.6, 0.0, 0.5)
			self.mainmenuComponent.width = 1.2
			self.component.scrollUp.position.x = 0.5
			self.component.scrollDown.position.x = 0.5
			self.doLayout( None )

			yield BWWaitForPeriod( fadeSpeed )

			BigWorld.worldDrawEnabled( False )



	def onBound( self ):
		PyGUI.PyGUIBase.onBound( self )
		self.mainmenuComponent = self.component.mainmenu


class SmoothMover( PyGUI.SmoothMover ):
	def __init__( self, component ):
		PyGUI.SmoothMover.__init__( self, component )

	def doLayout( self, parent ):
		self.component.width = parent.component.width
		PyGUI.SmoothMover.doLayout( self, parent )


# -------------------------------------------------------------------------
# This class implements an individual item in the a scrolling list page.
# Each item is initialised with a text label and a functor
# -------------------------------------------------------------------------
class MenuItem( PyGUI.PyGUIBase ):

	factoryString="MainMenuGUI.MenuItem"

	def __init__( self, component ):
		PyGUI.PyGUIBase.__init__( self, component )
		self.event = None

	#when the list item is created, what to do.
	def setup( self, setupParams ):
		self.component.name.text = setupParams[0]
		self.event = setupParams[1]

	def canSelect( self ):
		return not (self.event == None)

	def adjustFont( self, width ):
		if width < 700:
			self.component.name.font = self.smallFont
		else:
			self.component.name.font = self.bigFont
		self.component.name.reset()
		self.component.height = self.component.name.height * 1.1
		return self.component.height

	#arggh generic item colouring
	def select( self, state ):
		if not self.event:
			self.component.colour = (0,0,0,0)
			self.component.name.colour = (0,0,0,255)
		elif state:
			self.component.colour = (0,0,0,128)
			self.component.name.colour = (255,174,136,255)
		else:
			self.component.colour = (0,0,0,0)
			self.component.name.colour = (0,0,0,255)

	def doLayout( self, parent ):
		self.component.width = parent.component.width
		self.component.name.width = parent.component.width
		self.component.name.position.x = -parent.component.width / 2 + 0.05

		PyGUI.PyGUIBase.doLayout( self, parent )

	#i.e. the button was pressed. make event happen
	def onSelect( self, mainGui ):
		if self.event:
			mainGui.active(0)
			self.event()

	def onLoad( self, section ):
		self.smallFont = section.readString( "smallFont", "default_small.font" )
		self.bigFont = section.readString( "bigFont", "default_medium.font" )
		
		
		

