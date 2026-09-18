import BigWorld, GUI, Keys

from PyGUIBase import PyGUIBase

"""
This class implements an edit field
"""
class EditField( PyGUIBase ):

	factoryString = "PyGUI.EditField"
	CURSOR_CHAR   = "|"

	def __init__( self, component = None ):

		PyGUIBase.__init__( self, component )
		if ( self.component==None ):
			self.component = GUI.Text("")
			self.component.text = self.CURSOR_CHAR
			self.component.position = ( 0,0,0.5 )
			self.component.colour = ( 92, 92, 92, 128 )
			self.component.width = 256
			self.component.height = 32
			self.component.script = self

		self.colour    = (
			self.component.colour.x, self.component.colour.y,
			self.component.colour.z, self.component.colour.w)
		self.onEnter   = None
		self.onEscape  = None
		self.maxLength = 15


	def focus( self, state ):
		c = self.component
		if ( state ):
			c.colour = self.colour
			c.text = c.text + self.CURSOR_CHAR
		else:
			c.colour = ( 155, 155, 155, 255 )
			c.text = c.text[0:len(c.text)-1]


	def handleKeyEvent( self, down, key, modifiers ):
		def _addChar( key ):
			if len( c.text ) >= self.maxLength:
				return

			character = BigWorld.keyToString( key )
			if ( not shiftDown ):
				character = character.swapcase()

			c.text = c.text[0:len(c.text)-1] + character + self.CURSOR_CHAR

		c = self.component
		shiftDown = BigWorld.isKeyDown( Keys.KEY_LSHIFT ) or BigWorld.isKeyDown( Keys.KEY_RSHIFT )

		if ( down ):

			if ( key == Keys.KEY_BACKSPACE ) :
				c.text = c.text[0:len(c.text)-2] + self.CURSOR_CHAR
				return 1

			elif ( key >= Keys.KEY_1 and key <= Keys.KEY_0 ) :
				_addChar( key )
				return 1

			elif ( key >= Keys.KEY_Q and key <= Keys.KEY_P ) :
				_addChar( key )
				return 1

			elif ( key >= Keys.KEY_A and key <= Keys.KEY_L ) :
				_addChar( key )
				return 1

			elif ( key >= Keys.KEY_Z and key <= Keys.KEY_M ) :
				_addChar( key )
				return 1

			elif ( key == Keys.KEY_SPACE ) :
				if len( c.text ) < self.maxLength:
					c.text = c.text[0:len(c.text)-1] + ' ' + self.CURSOR_CHAR
				return 1

			elif ( key == Keys.KEY_RETURN and
					not BigWorld.isKeyDown( Keys.KEY_LALT ) and
					not BigWorld.isKeyDown( Keys.KEY_RALT ) ):
				if ( self.eventHandler != None ):
					textString = c.text
					self.eventHandler.onClick( c.text[:-1] )
					return 1
				elif self.onEnter is not None:
					self.onEnter( c.text[:-1] )
					return 1

			elif ( key == Keys.KEY_ESCAPE ) :
				if self.onEscape is not None:
					self.onEscape()
					return 1
		return 0


	def adjustFont( self, screenWidth ):
		if screenWidth < 700:
			self.component.font = self.smallFont
		else:
			self.component.font = self.bigFont


	def onLoad( self, section ):
		self.smallFont = section.readString( "smallFont", "default_small.font" )
		self.bigFont = section.readString( "bigFont", "default_medium.font" )

