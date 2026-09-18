import FantasyDemo

# ------------------------------------------------------------------------------
# Section: class GuardSpawner
# ------------------------------------------------------------------------------

class GuardSpawner( FantasyDemo.Base ):
	def __init__( self ):
		FantasyDemo.Base.__init__( self )

	def registerGuard( self, newGuard ):
		self.guardList.append( newGuard )

	# todo: remove as this is probably redudant
	def deregisterGuard( self, oldGuardID ):
		for guard in self.guardList:
			if guard.id == oldGuardID:
				self.guardList.remove( guard )

	# This gets called directly on the entity by util.py.
	def addLoadDemoGuards( self, count ):
		numToLoad = min( count, 500 - self.loadedGuards )
		if numToLoad > 0:
			self.cell.spawnLoadGuards( numToLoad, self )
			self.loadedGuards += numToLoad

	# This gets called directly on the entity by util.py.
	def delLoadDemoGuards( self, count ):
		numToDel = min( count, self.loadedGuards )
		if numToDel > 0:
			removed = 0
			while removed < numToDel and len( self.guardList ) > 0:
				guard = self.guardList.pop()
				guard.destroyGuard()
				removed += 1
			self.loadedGuards -= removed

# GuardSpawner.py
