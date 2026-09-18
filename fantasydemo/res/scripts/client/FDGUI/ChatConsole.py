import BigWorld, GUI
import Helpers.PyGUI as PyGUI

import FantasyDemo

from functools import partial

from Keys import *

import math

# -----------------------------------------------------------------------------
# Method: v4col
# Description:
#		- Helper function to turn a vector3 into a full-on vector4 colour
# -----------------------------------------------------------------------------
def v4col(v3col, alpha = 255):
	return (v3col[0], v3col[1], v3col[2], alpha)


class ChatConsole( PyGUI.Console ):


	def __init__( self, component ):
		PyGUI.Console.__init__( self, component )

		self.backgroundZOrder = 1.0
		self.consoleZOrder = 0.0


	def setZOrders( self, backgroundZOrder, consoleZOrder ):
		self.backgroundZOrder = backgroundZOrder
		self.consoleZOrder = consoleZOrder
		self.onRecreateDevice()


	def onSave( self, dataSection ):
		PyGUI.Console.onSave( self, dataSection )

		# save data to section
		dataSection.writeVector3( 'textColour', self.colours[0] )
		dataSection.writeVector3( 'otherWhisperColour', self.colours[1] )
		dataSection.writeVector3( 'otherSayColour', self.colours[2] )
		dataSection.writeVector3( 'systemColour', self.colours[3] )
		dataSection.writeBool( 'auto_hide' , self.autoHideEnable )
		dataSection.writeFloat( 'timeout' , self.autoHideTimeout )
		dataSection.writeVector3( 'colour', self.colour )
		dataSection.writeFloat( 'alpha', self.alpha )
		dataSection.writeBool( 'editable', self.editable )
		dataSection.writeInt( 'buffer_size', self.bufferSize )
		dataSection.writeInt( 'horizontal_padding', self.hpadding )
		dataSection.writeInt( 'vertical_padding', self.vpadding )
		dataSection.writeString( 'texture', self.chatWBack )
		dataSection.writeString( 'frame', self.chatWFrame )
		dataSection.writeString( 'edge', self.chatWEdge )
		dataSection.writeBool( 'invert', self.invert )


	def onLoad( self, dataSection ):
		PyGUI.Console.onLoad( self, dataSection )

		# load from data section
		self.colours = [
			v4col(dataSection.readVector3( 'textColour', (0,128,255) )),
			v4col(dataSection.readVector3( 'otherWhisperColour', (32,128,255) )),
			v4col(dataSection.readVector3( 'otherSayColour', (64, 128, 255) )),
			v4col(dataSection.readVector3( 'systemColour', (255, 128, 0) )) ]
		self.autoHideEnable = dataSection.readBool( 'auto_hide' , 1 )
		self.autoHideTimeout = dataSection.readFloat( 'timeout' , 10.0 )
		self.colour = dataSection.readVector3( 'colour', (0, 0, 0) )
		self.alpha = dataSection.readFloat( 'alpha', 0 )
		self.editable = dataSection.readBool( 'editable', False )
		self.bufferSize = dataSection.readInt( 'buffer_size', 250 )
		self.hpadding = dataSection.readInt( 'horizontal_padding', 0 )
		self.vpadding = dataSection.readInt( 'vertical_padding', 0 )
		self.chatWBack = dataSection.readString( 'texture', 'system/maps/aid_null.bmp' )
		self.chatWFrame = dataSection.readString( 'frame', 'system/maps/aid_null.bmp' )
		self.chatWEdge = dataSection.readString( 'edge', 'system/maps/aid_null.bmp' )
		self.invert = dataSection.readBool( 'invert', False )


	def onBound( self ):

		# setup chat console
		self.component.textureName = 'system/maps/aid_null.bmp'

		# set the auto hide counter
		self.autoHideCount = 0

		# create chat window background window and assign it a texture
		self.chatWindow = GUI.Frame(self.chatWBack, self.chatWFrame, self.chatWEdge, 16, 16)
		self.chatWindow.colour = v4col( self.colour, self.alpha )
		self.chatWindow.materialFX = 'BLEND'

		# set chat window alpha shader for fading out
		self.alphaShader = GUI.AlphaShader('ALL')
		self.alphaShader.alpha = 0
		self.alphaShader.speed = 0
		self.chatWindow.as = self.alphaShader

		# init chat window geometry
		self.chatWindow.horizontalAnchor = self.component.horizontalAnchor
		self.chatWindow.verticalAnchor = self.component.verticalAnchor
		self.chatWindow.verticalPositionMode = self.component.verticalPositionMode
		self.chatWindow.horizontalPositionMode = self.component.horizontalPositionMode
		self.chatWindow.heightMode = self.component.heightMode
		self.chatWindow.widthMode = self.component.widthMode
		self.chatWindow.width = self.component.width
		self.chatWindow.height = self.component.height

		# init console geometry
		self.component.visible = 0

		# set up edit stuff
		self.editing = False
		self.disableEdit()
		self.setEditPrompt( '> ' )
		self.setEditColour( self.colours[0] )

		# set buffer size
		self.setMaxLines( self.bufferSize )

		# store the current position
		p = self.component.position
		self.position = (p[0], p[1], p[2])

		# adjust the chat console to current resolution
		self.onRecreateDevice()

		if self.editable:
			self.editCallback( self.handleConsoleInput )

		self.hideNow()

	def active( self, state ):
		if state:
			GUI.addRoot(self.chatWindow)
		else:
			GUI.delRoot(self.chatWindow)
			self.hideNow()

		PyGUI.Console.active( self, state )

		GUI.reSort()


	def handleConsoleInput( self, msg ):
		if msg == '':
			self.hideNow()
		else:
			if BigWorld.player() and hasattr( BigWorld.player(), "handleConsoleInput" ):
				BigWorld.player().handleConsoleInput( msg )
			self.showNow()
			self.hideLater()


	def onRecreateDevice( self ):

		# character font size on screen
		size = self.component.characterSize

		# overridden gui resolution
		screenWidth, screenHeight = GUI.screenResolution()
		(realScreenWidth, realScreenHeight) = BigWorld.screenSize()

		scalex = realScreenWidth / screenWidth
		scaley = realScreenHeight / screenHeight

		# console pixel size
		(width, height) = self.consolePixelSize()

		# new line length and number of lines for console
		lineLength = int( math.floor( (width - self.hpadding * 2) * scalex / size[0] ) )
		totalLines = int( math.floor( (height - self.vpadding * 2) * scaley / size[1] ) )

		numLines = totalLines
		if self.editable:
			numLines -= 1 # take 1 line for editing

		# dynamically adjust the line length and number of lines base on font size
		self.setLineLength( lineLength )
		self.setNumberOfLines( numLines )

		# update edit cursor position
		self.setEditCursor( (0, numLines) )

		# update the position
		(x, y, z) = self.position

		# invert the y position if needed
		if self.invert:
			if self.component.verticalPositionMode == "CLIP":
				y *= -1
			else:
				y = screenHeight - y

		self.chatWindow.position = (x, y, self.backgroundZOrder)

		if self.component.horizontalPositionMode == "CLIP":
			x += self.hpadding / screenWidth
		else:
			x += self.hpadding

		if self.component.verticalPositionMode == "CLIP":
			y += self.vpadding / screenHeight
		else:
			y += self.vpadding

		self.component.position = ( x, y, self.consoleZOrder)

		# redraw the chat console
		PyGUI.Console.onRecreateDevice( self )


	def fini(self):
		if self.editable:
			self.editCallback( None )

		self.active(False)

		del self.chatWindow
		del self.component


	def addMsg( self, msg, colourIndex ):
		self.addLine( str(msg), self.colours[colourIndex] )
		self.showNow();
		self.hideLater()


	def appendMsg( self, msg, colourIndex ):
		self.appendLine( str(msg), self.colours[colourIndex] )
		self.showNow()
		self.hideLater()


	def edit(self, ison, nohide = 0):
		if self.editing == ison:
			return

		self.editing = ison
		self.component.editEnable = ison
		self.component.visible = True
		self.setEditText( '' )

		if ison:
			self.showNow()
		elif not nohide:
			self.hideLater()


	def hideLater(self, when = None):
		if self.autoHideEnable and not self.editing:
			self.autoHideCount += 1
			BigWorld.callback(
				self.autoHideTimeout if when is None else when,
				partial(self.autoHideStart, self.autoHideCount))


	def autoHideStart(self, count):
		# make sure we haven't been cancelled
		if self.editing or count != self.autoHideCount: return

		# ok start fading ourselves out then
		self.alphaShader.alpha = 0
		self.alphaShader.speed = 1.0
		self.component.visible = 0

		# could add another callback for when we're totally faded out,
		# but it's not actually necessary...


	def hideNow(self):
		# stop editing if we were
		if self.editing:
			self.edit(0, 1)

		# and start fading out immediately
		self.autoHideCount += 1
		self.autoHideStart(self.autoHideCount)
		self.component.visible = 0


	def showNow(self):
		self.autoHideCount += 1
		self.alphaShader.alpha = 1
		self.alphaShader.speed = 0
		self.component.visible = 1
