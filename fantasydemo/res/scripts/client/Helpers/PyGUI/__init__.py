from PyGUIBase import PyGUIBase
from Button import Button, ButtonVisualState
from CheckBox import CheckBox
from RadioButton import RadioButton
from EditField import EditField
from Grid import Grid
from Slider import Slider, SliderThumb, SliderVisualState
from ScrollingList import ScrollingList
from ScrollWindow import ScrollWindow
from SmoothMover import SmoothMover
from TextField import TextField
from ToolTip import ToolTip
from ToolTip import ToolTipInfo
from ToolTip import ToolTipManager
from Window import Window
from Window import DraggableWindow
from Console import Console

import EditUtils
import Test
import TextStyles
import Utils
import VisualStateComponent

# TODO: should these be in PyGUI?
from Helpers.videoFeeds import s_videoFeeds
from Helpers.videoFeeds import VideoFeed
from Helpers.ProgressBar import IProgressBar
from Helpers.ProgressBar import ProgressBar
from Helpers.ProgressBar import ChunkLoadingProgressBar
from Helpers.ProgressBar import TeleportProgressBar


def handleKeyEvent(down, key, mods):
	import DraggableComponent
	return DraggableComponent.dragManager.handleKeyEvent( down, key, mods )

def handleMouseEvent(dx, dy, dz):
	ToolTipManager.instance.handleMouseEvent(dx, dy, dz)

	import DraggableComponent
	return DraggableComponent.dragManager.handleMouseEvent( dx, dy, dz )


def PyGUIEvent( componentName, eventName, *args, **kargs ):
	"""
		@PyGUIEvent decorator.
		
		Note: If you override a function that is marked with this decorator
		in the base class, the derived class function is not required to be
		decorated. If you do decorate both, the event handler will be called
		twice.
	"""
	from functools import partial

	def addEvent( componentName, eventName, args, kargs, eventFunction ):
		if not hasattr( eventFunction, "_PyGUIEventHandler" ):
			eventFunction._PyGUIEventHandler = []
		eventFunction._PyGUIEventHandler += [(componentName, eventName, args, kargs)]
		return eventFunction

	return partial( addEvent, componentName, eventName, args, kargs )


