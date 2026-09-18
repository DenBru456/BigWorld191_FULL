import BigWorld, GUI

from PyGUIBase import PyGUIBase
from DraggableComponent import DraggableComponent

class Window( PyGUIBase ):

	factoryString="PyGUI.Window"

	def __init__( self, component ):
		PyGUIBase.__init__( self, component )
		component.script = self


	def onSave( self, dataSection ):
		PyGUIBase.onSave( self, dataSection )


	def onLoad( self, dataSection ):
		PyGUIBase.onLoad( self, dataSection )


	@staticmethod
	def create( texture ):
		c = GUI.Window( texture )
		return Window( c ).component



class DraggableWindow( Window, DraggableComponent ):

	factoryString="PyGUI.DraggableWindow"

	def __init__( self, component, horzDrag = True, vertDrag = True, restrictToParent = True ):
		Window.__init__( self, component )
		DraggableComponent.__init__( self, horzDrag, vertDrag, restrictToParent )
		component.script = self
		self.onBeginDrag = self._onBeginDrag


	def handleMouseButtonEvent( self, comp, key, down, modifiers, pos ):
		return DraggableComponent.handleMouseButtonEvent( self, comp, key, down, modifiers, pos )


	def onSave( self, dataSection ):
		DraggableComponent.onSave( self, dataSection )
		Window.onSave( self, dataSection )


	def onLoad( self, dataSection ):
		DraggableComponent.onLoad( self, dataSection )
		Window.onLoad( self, dataSection )


	def _onBeginDrag( self ):
		self.listeners.onBeginDrag()


	@staticmethod
	def create( texture ):
		c = GUI.Window( texture )
		return DraggableWindow( c ).component

