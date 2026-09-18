import BigWorld, GUI

import math

from PyGUIBase import PyGUIBase

class Console( PyGUIBase ):
    
    factoryString = "PyGUI.Console"
    
    def __init__( self, component ):
        PyGUIBase.__init__( self, component )
        component.script = self
	
	# maximum lines the console can store
	self.maxLines = 255
	
	# console line list
	self.lines = []
	
	# console display line list 
	# note: display lines are line wrapped to screen size and are
	# recalulated each time the window is resized which is an 
	# expensize operation
	self.displayLines = []
	
	# maximum length of the each console line
	self.lineLength = component.visibleWidth()
	
	# maximum number of lines in the console
	self.numOfLines = component.visibleHeight()
	
	# current scroll index in the console
	self.scrollIndex = 0
	
	# the colour of the edit text
	self.editColour = (255, 255, 255, 255)
	
	# set cursor to (0, 0)
	self.component.cursor = (0, 0)
	
	self.setEditColour( self.editColour )
	self.setEditCursor( (0, 0) )
	self.setPosition( self.component.position )
        
	
    def onSave( self, dataSection ):
	PyGUIBase.onSave( self, dataSection )

	
    def onLoad( self, dataSection ):
	PyGUIBase.onLoad( self, dataSection )
	
	
    def onRecreateDevice( self ):
	self.displayLines = []
	for line in self.lines:
	    self._addDisplayLine( line[0], line[1] )
	self.redraw()
	

    @staticmethod
    def create():
	c = GUI.Console()
	return Console( c ).component
    

    def getMaxLines( self ):
	return self.maxLines
    
    
    def setMaxLines( self, maxLines ):
	if self.maxLines > 0:
	    self.clear()
	    self.maxLines = maxLines
	    self.redraw()
	
    
    def addLine( self, str, colour = (255, 255, 255, 255) ):
	# add line to list
	if len( self.lines ) == self.maxLines:
	    # remove display lines
	    ( line, colour ) = self.lines[0]
	    
	    n = int(math.ceil( len( line ) / self.lineLength )) + 1
	    self.displayLines = self.displayLines[n:]
	    
	    self.lines = self.lines[1:]
	    
	self.lines.append( (str, colour) )
	
	self._addDisplayLine( str, colour )
		
	self.redraw()
	
	    
    def appendLine( self, str, colour = (255, 255, 255, 255) ):
	( line, colour ) = self.lines.pop()
	n = int(math.ceil( len( line ) / self.lineLength ))
	self.displayLines = self.displayLines[ 0: int( len( self.displayLines ) - n) - 1 ]
	self.addLine( line + str, colour )
	
	
    def _addDisplayLine( self, str, colour ):
	# add line to display list with line wrapping included
	s = 0
	while s < len( str ):
	    line = str[s:s + self.lineLength]
	    s += self.lineLength
	    
	    self.displayLines.append( (line, colour) )
	
	    # update scroll index
	    self.scrollIndex = len(self.displayLines) - self.numOfLines
	    if self.scrollIndex < 0:
		self.scrollIndex = 0
    
    
    def clear( self ):
	self.lines = []
	self.displayLines = []
	self.scrollIndex = 0
	self.redraw()
    
    
    def scrollUp( self ):
	if self.scrollIndex > 0:
	    self.scrollIndex -= 1
	    self.redraw()	    
    
    
    def scrollDown( self ):
	if self.scrollIndex < len( self.displayLines ) - self.numOfLines:
	    self.scrollIndex += 1
	    self.redraw()
    
    
    def getScrollIndex( self ):
	return self.scrollIndex
    
    
    def setScrollIndex( self, index ):
	if index < 0:
	    self.scrollIndex = 0
	elif index > len( self.displayLines ) - self.numOfLines:
	    self.scrollIndex = len( self.displayLines ) - self.numOfLines
	else:
	    self.scrollIndex = index
	self.redraw()
    
    
    def getLineLength( self ):
	return self.lineLength
    
    
    def setLineLength( self, length ):
	lineLength = length
	if lineLength > self.component.visibleWidth():
	    lineLength = self.component.visibleWidth()
	self.lineLength = lineLength
	self.component.editLineLength = lineLength
	self.redraw()
    
    
    def getNumberOfLines( self ):
	return self.numOfLines

    
    def setNumberOfLines( self, numOfLines ):
	self.numOfLines = numOfLines
	if self.numOfLines > self.component.visibleHeight():
	    self.numOfLines = self.component.visibleHeight()
	self.redraw()
	
	
    def getPosition( self ):
	return self.component.position
    
    
    def setPosition( self, position ):
	self.component.position = position
	self.redraw()
    
    
    def getEditCursor( self ):
	return (self.component.editCol, self.component.editRow)
    
    
    def setEditCursor( self, cursorPos ):
	self.component.editCol = cursorPos[0]
	self.component.editRow = cursorPos[1]
	self.setEditColour( self.editColour )
	self.redraw()
    
    
    def enableEdit( self ):
	self.component.editEnable = True
    
    
    def disableEdit( self ):
	self.component.editEnable = False
    
    
    def getEditPrompt( self ):
	return self.component.editPrompt
    
    
    def setEditPrompt( self, prompt ):
	self.component.editPrompt = prompt
    
    
    def getEditText( self ):
	return self.component.editText
    
    
    def setEditText( self, text ):
	self.component.editText = text[0:self.lineLength]
	
    
    def editCallback( self, callback ):
	self.component.editCallback = callback
	
	
    def setEditColour( self, colour ):
	self.editColour = colour
	self.component.editColour = colour
	
    def consolePixelSize( self ):
		widthMode = self.component.widthMode
		self.component.widthMode = "PIXEL"

		heightMode = self.component.heightMode
		self.component.heightMode = "PIXEL"
	
		width = self.component.width
		height = self.component.height

		self.component.widthMode = widthMode
		self.component.heightMode = heightMode

		return (width, height)
    
    
    def redraw( self ):
	
	# clear the console
	console = self.component
	console.clear()
	
	# find the lines to draw
	startIndex = self.scrollIndex
	endIndex = startIndex + self.numOfLines
	displayLines = self.displayLines[startIndex : endIndex]

	# make sure the lines start at the bottom
	if len( displayLines ) < self.numOfLines:
	    row = self.numOfLines - len( displayLines )
	else:
	    row  = 0
	
	# draw each line 
	for line in displayLines:
	    str = line[0]
	    colour = line[1]
	    
	    console.cursor = (0, row)
	    console.lineColour = colour
	    console.prints( str )
	    
	    row += 1
	    
	# update the edit line colour
	if self.component.editEnable:
	    self.setEditColour( self.editColour )
	    