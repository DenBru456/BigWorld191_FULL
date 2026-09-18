import BigWorld
from FDGUI import Minimap

# This implements the MovingPlatform on the Client.
class MovingPlatform( BigWorld.Entity ):

	PLATFORM_MODEL = 'sets/items/platform.model'

	def __init__( self ):
		BigWorld.Entity.__init__( self )


	def prerequisites( self ):
		return [ MovingPlatform.PLATFORM_MODEL ]


	# This is called by BigWorld when the Entity enters AoI, through creation or movement.
	def onEnterWorld( self, prereqs ):
		self.model = BigWorld.PyModelObstacle( 	MovingPlatform.PLATFORM_MODEL, self.matrix, True )

		# Set appropriate filter for server controlled Entity
		self.filter = BigWorld.AvatarFilter()
		self.model.vehicleID = self.id

		BigWorld.addShadowEntity( self )
		Minimap.addEntity( self )


	# This is called by BigWorld when the Entity leaves AoI, through creation or movement.
	def onLeaveWorld( self ):
		Minimap.delEntity( self )
		BigWorld.delShadowEntity( self )
		self.model = None


	def name( self ):
		return "Moving Platform"


# MovingPlatfrom.py
