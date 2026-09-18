import BigWorld, GUI, Keys
import Utils

from PyGUIBase import PyGUIBase

# -------------------------------------------------------------------------
# This class implements a scrolling list of whatever gui items you please
# -------------------------------------------------------------------------
class ScrollingList( PyGUIBase ):

	factoryString="PyGUI.ScrollingList"

	def __init__( self, component ):
		PyGUIBase.__init__( self, component )
		self.selection = 0
		self.layoutManager = Utils.GridLayoutManager()
		self.layoutManager.margin = 0.01
		self.itemGuiName = ""
		self.backFn = None
		self.budget = Utils.Budget( self.createItem, self.deleteItem )
		self.selectItemCallback = lambda: None

	def active( self, state ):
		if state == self.isActive:
			return
		PyGUIBase.active( self, state )
		self.selectItem( self.selection )

	#This method is required for page controls - the ScrollingList
	#works under a page control.
	def onSelect( self, pageControl ):
		pass

	#This method is called back by our gui Budget helper
	#This method returns a new component
	def createItem( self ):
		assert self.itemGuiName != ""
		g = GUI.load( self.itemGuiName )
		setattr( self.items, "m%d"%(len(self.items.children),), g)
		g.script.doLayout( self )
		return g

	#This method is called back by our gui Budget helper
	def deleteItem( self, c ):
		self.items.delChild(c)

	def setupItems( self, backFn, setupParams ):
		self.backFn = backFn

		oldidx = -1
		if self.selection < len( self.items.children ):
			oldidx = self.selection

		self.budget.balance( len(setupParams) )

		num = len( setupParams )
		for i in xrange( 0, num ):
			g=self.items.children[i][1]
			g.script.setup(setupParams[i])
			g.script.select(0)

		if num > 0:
			self.doLayout( None )
			if oldidx >= 0:
				self.selectItem( oldidx )

	def doLayout( self, parent ):
		totalHeight = 0
		screenWidth = BigWorld.screenWidth()
		for name, item in self.items.children:
			totalHeight = item.script.adjustFont( screenWidth )
		totalHeight *= 4
		self.component.items.height = totalHeight * 1.8
		self.component.height = totalHeight * 1.8

		position = self.component.items.position
		position[1] = 0.05 - (self.component.height - totalHeight) / 2.5 
		self.component.items.position = position

		lm = self.layoutManager
		lm.doLayout( self.items )

		#calculate min/max scroll
		th = self.component.items.height
		h = self.items.children[0][1].height
		m = lm.margin
		n = lm.numRows
		self.items.script.maxScroll[1] = max(0,lm.numRows*(h+m)-th-m)
		self.items.script.minScroll[1] = 0
		if self.items.script.maxScroll[1] == 0.0:
			self.scrollUp.visible = 0
			self.scrollDown.visible = 0

		PyGUIBase.doLayout( self, parent )


	# -------------------------------------------------------------------------
	# This method returns true if the given index is selectable
	# -------------------------------------------------------------------------
	def canSelect( self, idx ):
		if idx < 0:
			return 0
		if idx >= len( self.items.children ):
			return 0
		return self.items.children[idx][1].script.canSelect()

	# -------------------------------------------------------------------------
	# This method should be called to safely select an item.
	# -------------------------------------------------------------------------
	def selectItem( self, idx = 0 ):
		num = len( self.items.children )
		if num == 0: return

		oldIdx = self.selection

		if idx >= num:
			idx = num - 1
		if idx < 0:
			idx = 0
		self.selection = idx

		if oldIdx >= 0 and oldIdx < num:
			self.items.children[oldIdx][1].script.select(0)
		self.items.children[idx][1].script.select(1)
		self.checkSelectionVisible()

		self.updateControlBar()

		try:
			self.selectItemCallback( idx )
		except Exception, e:
			print "ERROR: ScrollingList.selectItem callback", e

	# -------------------------------------------------------------------------
	# This method updates the control bar based on the state of the currently
	# selected item.
	# -------------------------------------------------------------------------
	def updateControlBar( self ):
		pass

	# -------------------------------------------------------------------------
	#This method performs a scroll window check :
	#if we need to scroll the window to show the current selection, do so.
	#this method also shows/hides the scroll arrows.
	# -------------------------------------------------------------------------
	def checkSelectionVisible( self ):
		if self.items.script.maxScroll[1] == 0.0:
			self.items.script.scrollTo(0,0)
			self.scrollUp.visible = 0
			self.scrollDown.visible = 0
			return

		mgn = self.layoutManager.margin
		inv = self.items
		sel = inv.children[self.selection][1]
		selY = sel.position[1]
		selH = sel.height
		height = self.component.height / 2 - selH - mgn
		currPosY = selY + self.items.script.scroll[1]

		scrollTarget = self.items.script.scroll[1]
		if currPosY > height:
			dy = currPosY-height
			scrollTarget = scrollTarget - dy - selH/2
		elif currPosY < -height:
			dy = -height-currPosY
			scrollTarget = scrollTarget + dy + selH/2

		self.items.script.scrollTo(0,scrollTarget)

		#check for scroll arrows
		self.scrollUp.visible = self.items.script.canScrollUp()
		self.scrollDown.visible = self.items.script.canScrollDown()

	# -------------------------------------------------------------------------
	# This method handles any list traversal key presses.
	# -------------------------------------------------------------------------
	def handleTraversalKeys( self, down, key, modifiers ):
		if not down:
			return 0

		if key in [Keys.KEY_JOYDDOWN,Keys.KEY_DOWNARROW,Keys.KEY_S]:
			if len( self.items.children ) == 0:
				return 1
			oidx = None
			idx = self.selection
			while idx != oidx:
				if oidx == None: oidx = idx
				idx += 1
				if idx >= len( self.items.children ):
					idx = 0
				if self.canSelect( idx ):
					self.selectItem( idx )
					break
			BigWorld.playSound("ui/tick")
			return 1
		elif key in [Keys.KEY_JOYDUP,Keys.KEY_UPARROW,Keys.KEY_W]:
			if len( self.items.children ) == 0:
				return 1
			oidx = None
			idx = self.selection
			while idx != oidx:
				if oidx == None: oidx = idx
				idx -= 1
				if idx < 0:
					idx = len( self.items.children ) - 1
				if self.canSelect( idx ):
					self.selectItem( idx )
					break
			BigWorld.playSound("ui/tick")
			return 1

		return 0

	# -------------------------------------------------------------------------
	# This method is called handles key events for the list.
	# -------------------------------------------------------------------------
	def handleKeyEvent( self, down, key, modifiers ):
		if ( down ):
			if self.handleTraversalKeys( down, key, modifiers ):
				return 1
			elif key == [Keys.KEY_JOYA] or (
					key == Keys.KEY_RETURN and
					not BigWorld.isKeyDown( Keys.KEY_LALT ) and
					not BigWorld.isKeyDown( Keys.KEY_RALT )):
				if len( self.items.children ) == 0:
					return 1
				BigWorld.playSound("ui/boop")
				entry = self.items.children[self.selection][1]
				i = entry.script.onSelect( self )
				self.updateControlBar()
				return 1
			elif key in [Keys.KEY_JOYB,Keys.KEY_JOYBACK,Keys.KEY_ESCAPE, \
					Keys.KEY_BACKSPACE]:
				if self.backFn != None:
					self.active( 0 )
					BigWorld.playSound("ui/boop")
					self.backFn()
					return 1
		return 0

	def onLoad( self, section ):
		self.itemGuiName = section.readString( "itemGui", "")
		assert self.itemGuiName != ""

	# -------------------------------------------------------------------------
	# This method is called just after the component loads.  Here we perform
	# a check to make sure we have a items area.
	# -------------------------------------------------------------------------
	def onBound( self ):
		PyGUIBase.onBound( self )
		try:
			self.items = self.component.items
		except:
			print "the scrolling list should have a items area!!!"

		if hasattr( self.component, 'scrollUp' ):
			self.scrollUp = self.component.scrollUp
		if hasattr( self.component, 'scrollDown' ):
			self.scrollDown = self.component.scrollDown

		
