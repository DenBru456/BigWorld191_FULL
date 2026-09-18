import BigWorld

class TeleportPoint( BigWorld.Entity ):
	def __init__( self ):
		BigWorld.Entity.__init__( self )
		
	def updatePosition( self, position ):
		self.position = position
		
	def tryToTeleport( self, dst, playerID, spaceID ):
		#print "TeleportPoint.tryToTeleport:", self.spaceID, spaceID
		if spaceID == self.spaceID:
			BigWorld.entities[playerID].client.teleportTo( dst, True )

# TeleportPoint.py
