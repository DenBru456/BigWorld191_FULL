import BigWorld, GUI
import weakref
from bwdebug import *

from functools import partial

from Helpers.Listener import Listenable


# TODO: evaluate this more in depth and clean up (e.g. activate stuff is a bit questionable).


"""
This is the base class for all python gui classes.
There is a simple interface.

active(bool)		//must use this entry point to show the gui
setEventHandler(ev)	//this function gets called back on an event
self.component		//the underlying component.  Must be set by derived classes/
"""
class PyGUIBase(object, Listenable):

	def __init__( self, component = None ):
		Listenable.__init__( self )
		#derived classes must set this
		self.component = component
		self.eventHandler = None
		self._parent = None
		self.isActive = False

	def active( self, state ):
		if state == self.isActive:
			return

		if not self.component:
			return

		self.isActive = state
		if state:
			if not self._parent:
				GUI.addRoot( self.component )
			else:
				self._parent.addChild( self.component )

			self.component.focus = True
			self.component.moveFocus = True
			self.component.crossFocus = True
		else:
			if not self._parent:
				GUI.delRoot( self.component )
			else:
				self._parent.delChild( self.component )

			self.component.focus = False
			self.component.moveFocus = False
			self.component.crossFocus = False

		self.listeners.activated( state )

	def _setparent( self, parent ):
		if self.isActive:
			if not self._parent:
				GUI.delRoot( self.component )
			else:
				self._parent.delChild( self.component )

		if parent:
			self._parent = weakref.proxy(parent)
		else:
			self._parent = parent

		if self.isActive:
			if not self._parent:
				GUI.addRoot( self.component )
			else:
				self._parent.addChild( self.component )


	def _getparent( self ):
		return self._parent

	parent = property(_getparent, _setparent)

	def getWindow( self ):
		import Window
		if isinstance( self, Window.Window ):
			return self
		elif self.component.parent and self.component.parent.script:
			return self.component.parent.script.getWindow()
		else:
			return None

	def toggleActive( self ):
		self.active( not self.isActive )

	def setEventHandler( self, eh ):
		self.eventHandler = eh

	def doLayout( self, parent ):
		for name, child in self.component.children:
			child.script.doLayout( self )


	def setToolTipInfo( self, toolTipInfo ):
		self.toolTipInfo = toolTipInfo


	def removeToolTipInfo( self ):
		if hasattr( self, toolTipInfo ):
			del self.toolTipInfo


	#stubbing out fns that SimpleGUIComponent ( C++ ) calls into
	def focus( self, state ):
		pass

	def handleKeyEvent( self, down, key, modifiers ):
		return False

	def handleMouseEvent( self, comp, pos ):
		return False

	def handleMouseButtonEvent( self, comp, key, down, modifiers, pos ):
		window = self.getWindow()
		if window:
			window.listeners.windowClicked()
		return False


	def handleMouseClickEvent( self, component, position ):
		return False


	def handleMouseEnterEvent( self, comp, pos ):
		if getattr( self, 'toolTipInfo', None ):
			import ToolTip
			ToolTip.ToolTipManager.instance.setupToolTip( self.component, self.toolTipInfo )

		return False


	def handleMouseLeaveEvent( self, comp, pos ):
		return False


	def handleAxisEvent( self, axis, value, dTime ):
		return False


	def handleDragStartEvent( self, comp, pos ):
		return False


	def handleDragStopEvent( self, comp, pos ):
		return False


	def handleDragEnterEvent( self, comp, pos, dragged ):
		return False


	def handleDragLeaveEvent( self, comp, pos, dragged ):
		return False


	def handleDropEvent( self, comp, pos, dropped ):
		return False


	def onLoad( self, dataSection ):
		if dataSection.has_key( "toolTipInfo" ):
			import ToolTip
			self.toolTipInfo = ToolTip.ToolTipInfo()
			self.toolTipInfo.onLoad( dataSection._toolTipInfo )

	def onSave( self, dataSection ):
		if hasattr( self, "toolTipInfo" ) and self.toolTipInfo is not None:
			toolTipInfoSection = dataSection.createSection( "toolTipInfo" )
			self.toolTipInfo.onSave( toolTipInfoSection )

	def onBound( self ):
		for name, child in self.component.children:
			if not child.script:
				child.script = PyGUIBase( child )
			assert isinstance( child.script, PyGUIBase )

		# Bind event handler decorators
		self._bindEvents( self.__class__ )


	def _bindEvents( self, cls ):
		for name, function in cls.__dict__.iteritems():
			if hasattr( function, "_PyGUIEventHandler" ):
				for componentName, eventName, args, kargs in function._PyGUIEventHandler:
					assert( callable( function ) )

					component = self.component
					for name in componentName.split("."):
						component = getattr( component, name, None )
						if component is None:
							break

					if component is None:
						ERROR_MSG( "PyGUIEvent: '%s' has no component named '%s'." % (str(self), componentName,) )
						continue

					function = getattr( self, function.__name__ )
					setattr( component.script, eventName, partial( function, *args, **kargs ) )

		for base in cls.__bases__:
			self._bindEvents( base )
