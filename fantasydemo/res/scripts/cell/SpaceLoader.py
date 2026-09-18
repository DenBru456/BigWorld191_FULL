import BigWorld

START_TIME_OF_DAY = 7.5 * 60 * 60 # 7:30
GAME_SECONDS_PER_SECOND = 6 # 4 real hours for a day

class SpaceLoader( BigWorld.Entity ):
	def __init__( self ):
		if self.geometry:
			BigWorld.addSpaceGeometryMapping(
					self.spaceID, None, self.geometry )
		BigWorld.setSpaceTimeOfDay( self.spaceID, START_TIME_OF_DAY,
				GAME_SECONDS_PER_SECOND )
				
# SpaceLoader.py
