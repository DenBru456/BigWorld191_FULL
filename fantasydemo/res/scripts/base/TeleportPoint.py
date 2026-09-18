import BigWorld
import FantasyDemo

class TeleportPoint( FantasyDemo.Base ):
	def __init__( self ):
		FantasyDemo.Base.__init__( self )
		
	def onRegister( self, succeeded ):
		if not succeeded:
			print "TeleportPoint.onRegister: Failed to register", self.label

	def teleport( self, cellEntity ):
		cellEntity.teleportTo( self.cell, self.dstPos, (0, 0, 0) )
		
# TeleportPoint.py
