import BigWorld
import GUI
import Helpers.PyGUI.ToolTip as ToolTip
from Helpers.PyGUI.ToolTip import ToolTipInfo
from Helpers.PyGUI.ToolTip import ToolTipManager
import Helpers.PyGUI as PyGUI
import ResMgr
import Math
import FantasyDemo
from functools import partial

smallMinimapName = "gui/minimap_small.gui"
largeMinimapName = "gui/minimap_large.gui"

#for preload reasons only
smallMinimapDS = ResMgr.openSection( smallMinimapName )
largeMinimapDS = ResMgr.openSection( largeMinimapName )


class MinimapWindow( PyGUI.Window ):

	def _setparent( self, parent ):
		PyGUI.Window._setparent( self, parent )
		for child in self.component.children:
			child[1].script.parent = parent
	parent = property(PyGUI.Window._getparent, _setparent)


#------------------------------------------------------------------------------
# This class handles the minimap itself, not the border around it or the
# buttons.
#------------------------------------------------------------------------------
class Minimap( PyGUI.PyGUIBase ):
	def __init__( self, component ):
		PyGUI.PyGUIBase.__init__( self, component )
		self.toolTipInfo = ToolTipInfo( self.component, "tooltip1line" )
		self.toolTipInfo.infoDictionary["shortcut"] = ""
		self.toolTipInfo.delayType = ToolTip.IMMEDIATE_TOOL_TIP
		self.toolTipInfo.placement = ToolTip.PLACE_ABOVE
		self.handleMap = {}
		self.maxZoom = 1500
		self.minZoom = 100
		self.component.pointSizeScaling = (12.0, -6.0/5000.0)
		self.component.focus = True


	def onBound( self ):
		PyGUI.PyGUIBase.onBound( self )
		self.smallMinimap = GUI.load(smallMinimapName)
		self.largeMinimap = GUI.load(largeMinimapName)
		self.smallMinimap.script.minimap = self.component
		self.largeMinimap.script.minimap = self.component
		self.maximised = True
		self.maximise( False )


	def _minimap( self ):
		return self.component


	def _setparent( self, parent ):
		PyGUI.PyGUIBase._setparent( self, parent )
		self.largeMinimap.script.parent = parent
		self.smallMinimap.script.parent = parent
	parent = property(PyGUI.PyGUIBase._getparent, _setparent)


	def add( self, entity ):
		try:
			col = entity.minimapColour
		except:
			col = (128,128,128,255)

		entity.minimapHandle = self.component.addSimple(entity.matrix, col)
		self.handleMap[entity.minimapHandle] = entity.id


	def remove( self, entity ):
		if hasattr( entity, "minimapHandle" ):
			self.component.remove(entity.minimapHandle)


	def onEntryBlur( self, handle ):
		pass


	def onEntryFocus( self, handle ):
		BigWorld.callback( 0.0, partial(self._updateToolTip, handle) )


	def _updateToolTip( self, handle ):
		self.toolTipInfo.infoArea = self._toolTipArea()
		id = self.handleMap[handle]
		try:
			entity = BigWorld.entities[id]
			try:
				name = entity.name()
			except AttributeError:
				name = entity.__class__
			self.toolTipInfo.infoDictionary["text"] = "%s (id %d)" % (name,id)
			ToolTipManager.instance.setupToolTip(self.component, self.toolTipInfo)
		except KeyError:
			pass


	def _toolTipArea( self ):
		s = self.component.simpleEntrySize * 1.0
		pos = GUI.mcursor().position
		pos = self.component.screenToLocal(pos)
		toolTipArea = (pos[0]-s, pos[1]-s, pos[0]+s, pos[1]+s)
		return toolTipArea


	def ensureZoomInRange( self ):
		m = self._minimap()
		m.range = max( m.range, self.minZoom )
		m.range = min( m.range, self.maxZoom )


	def zoomIn( self ):
		m = self._minimap()
		range = m.range
		zoomRange = self.maxZoom - self.minZoom
		m.range = m.range - (zoomRange/5.0)
		if m.range < self.minZoom:
			m.range = self.minZoom


	def zoomOut( self ):
		m = self._minimap()
		range = m.range
		zoomRange = self.maxZoom - self.minZoom
		m.range = m.range + (zoomRange/5.0)
		if m.range > self.maxZoom:
			m.range = self.maxZoom


	def maximise( self, state = True ):
		if self.maximised == state:
			return

		from FDGUI import Z_ORDER_SMALLMINIMAP_MAP
		from FDGUI import Z_ORDER_SMALLMINIMAP_FRAME
		from FDGUI import Z_ORDER_LARGEMINIMAP_FRAME
		from FDGUI import Z_ORDER_LARGEMINIMAP_MAP

		self.maximised = state
		container = self.component.parent

		# NOTE : large/small minimap overlays are activated into the same
		# root as the container's root, not this component's root.
		# This is because this minimap requires a dummy parent
		# window for layout purposes only (MinimapWindow script).

		if self.maximised:
			self.smallMinimap.script.active(False)
			self.largeMinimap.script.active(True)
			(x,y,z) = self.component.position
			self.component.position = (x,y,Z_ORDER_LARGEMINIMAP_MAP)
			(x,y,z) = self.largeMinimap.position
			self.largeMinimap.position = (x,y,Z_ORDER_LARGEMINIMAP_FRAME)
			container.position = (0,0,Z_ORDER_LARGEMINIMAP_MAP)
			container.verticalAnchor = "CENTER"
			container.horizontalAnchor = "CENTER"
			container.size = self.largeMinimap.script.containerSize
			container.m.size = self.largeMinimap.script.minimapSize
			self.component.maskName = self.largeMinimap.script.maskName
		else:
			self.largeMinimap.script.active(False)
			self.smallMinimap.script.active(True)
			(x,y,z) = self.component.position
			self.component.position = (x,y,Z_ORDER_SMALLMINIMAP_MAP)
			(x,y,z) = self.smallMinimap.position
			self.smallMinimap.position = (x,y,Z_ORDER_SMALLMINIMAP_FRAME)
			container.position = (1,1,Z_ORDER_SMALLMINIMAP_MAP)
			container.verticalAnchor = "TOP"
			container.horizontalAnchor = "RIGHT"
			container.size = self.smallMinimap.script.containerSize
			container.m.size = self.smallMinimap.script.minimapSize
			self.component.maskName = self.smallMinimap.script.maskName

		if container.parent is not None:
			container.parent.reSort()

		self.ensureZoomInRange()


	def _normalisedMousePosition( self ):
		c = self.component
		pos = GUI.mcursor().position
		pos = c.screenToLocal( pos )
		pos[0] = pos[0] / c.width
		pos[1] = pos[1] / c.height
		if (pos[0] < 0) or (pos[0] > 1):
			return
		if (pos[1] < 0) or (pos[1] > 1):
			return
		if c.heightMode is not "PIXEL":
			pos[1] = 1.0 - pos[1]
		pos[0] = (pos[0] - 0.5) * 2.0
		pos[1] = (pos[1] - 0.5) * 2.0
		#print "teleportToMousePosition - normalised coordinates", pos[0], pos[1]
		return pos


	def teleportToMousePosition( self ):
		c = self.component
		pos = self._normalisedMousePosition()
		if pos is None:
			# Mouse was outside the view
			return

		try:
			m = Math.Matrix( c.viewpoint )
		except:
			m = Math.Matrix( BigWorld.camera().invViewMatrix )
		center = m.applyToOrigin()
		#print "teleportToMousePosition - center of map, range", center[0], center[2], c.range
		startPos = Math.Vector3( pos[0] * c.range + center[0], center[1] + 500.0, pos[1] * c.range + center[2] )
		endPos = Math.Vector3( startPos[0], startPos[1] - 1000.0, startPos[2] )
		colres = BigWorld.collide( BigWorld.player().spaceID, startPos, endPos )
		#print "collision start, end, colres : ", startPos, endPos, colres
		if colres != None:
			(pt, tri, mat) = colres
			BigWorld.player().physics.teleport(pt)
		else:
			FantasyDemo.addChatMsg( -1, "Cannot teleport this far away." )
			FantasyDemo.addChatMsg( -1, "Please try somewhere closer," )
			FantasyDemo.addChatMsg( -1, "Or wait for more of the world to load." )


	def handleMouseButtonEvent( self, comp, key, down, modifiers, pos ):
		if down:
			actionName = FantasyDemo.rds.keyBindings.getActionForKeyState( key )
			# Only the actions in this list are allowed for clicks on the minimap
			if actionName in ['Teleport']:
				return False

		return True


#utility fn to add/del an entity to/from the minimap
def addEntity( entity ):
	FantasyDemo.rds.fdgui.minimap.m.script.add( entity )


def delEntity( entity ):
	FantasyDemo.rds.fdgui.minimap.m.script.remove( entity )
