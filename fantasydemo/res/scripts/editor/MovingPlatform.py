class MovingPlatform:
	def modelName( self, props ):
		return 'sets/items/platform.model'


	# platform nodes linking conditions
	def canLink( self, propName, thisInfo, otherInfo ):
		if otherInfo['type'] == 'PlatformNode':
			return True
		else:
			return False

# MovingPlatform.py
