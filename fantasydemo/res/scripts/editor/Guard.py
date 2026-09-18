import WorldEditor


class Guard:

	def modelName( self, props ):
		return "characters/npc/fd_orc_guard/orc.model"


	def canLink( self, propName, thisInfo, otherInfo ):
		thisProps = thisInfo["properties"]
		otherProps = otherInfo["properties"]
		
		if propName == "initialPatrolNode":
			if otherInfo["type"] != "PatrolNode":
				# Only allows linking to PatrolNodes
				return False
			
		return True
		
# Guard.py
