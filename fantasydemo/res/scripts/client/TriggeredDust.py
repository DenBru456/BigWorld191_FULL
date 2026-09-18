import BigWorld
from Helpers import Caps
import math
import sfx
from FDGUI import Minimap


# ------------------------------------------------------------------------------
# Section: class TriggeredDust
# ------------------------------------------------------------------------------

ENTITIES_IN_WORLD = set()


class TriggeredDust( BigWorld.Entity ):
	def __init__( self ):
		BigWorld.Entity.__init__( self )


	def prerequisites( self ):		
		result = sfx.prerequisites( self.effectName )
		return result


	def onEnterWorld( self, prereqs ):
		#just hold onto all the resources required for our sfx
		#later on.
		self.prereqs = prereqs
		Minimap.addEntity( self )
		ENTITIES_IN_WORLD.add( self )		


	def onLeaveWorld( self ):
		del self.prereqs
		ENTITIES_IN_WORLD.remove( self )
		Minimap.delEntity( self )



	def use( self ):
		pass
	

	def trigger( self ):
		if len( self.effectName ) > 0:
			s = sfx.OneShotSFX( self.effectName )
			s.go( self )


	def name( self ):
		return "Triggered Dust"

# TriggeredDust.py
