import BigWorld
import math
import random
import Math

# This entity provides a button that players can use to spawn new Guards.

# Data Requirements:
# The connected graph is fully bidirectional for all links
# The 'typeName' corresponds to a known entity type
# The dictionary string can be resolved to a valid python dictionary

# Notes:
# 'spawnFrequency' is the time between successive summons or zero for once 
#  per use
# 'modName' is the name of the model used for the button


class GuardSpawner( BigWorld.Entity ):

	TIMER_SPAWNING = 1
	TIMER_WAITING_FOR_PATROL_PATH = 2
	TIMER_ENTITY_COUNT_DECREMENT = 3

	#-------------------------------------------------------------------------
	# Constructor.
	#-------------------------------------------------------------------------
	def __init__( self ):
		BigWorld.Entity.__init__( self )

		self.spawnTimers = dict()
		self.entityDecrementTimer = self.addTimer( 5.0, 1.0, GuardSpawner.TIMER_ENTITY_COUNT_DECREMENT )


		self.entityCreationDictionary = {}
		try:
			dictionary = eval( self.dictionary )
			dictionary = dict( dictionary )
			if not 'playerName' in dictionary:
				dictionary['playerName'] = 'Orc'
			self.entityCreationDictionary = dictionary
		except:
			print 'GuardSpawner@', self.position, ' Bad dictionary parameter : ', self.dictionary

		print 'GuardSpawner@', self.position, ' dictionary : ', self.entityCreationDictionary


	#-------------------------------------------------------------------------
	# This method is called when a timer expires.
	#-------------------------------------------------------------------------
	def onTimer(self, timerID, userID):
		if userID == GuardSpawner.TIMER_SPAWNING:
			self.spawnOne( timerID )
		elif userID == GuardSpawner.TIMER_ENTITY_COUNT_DECREMENT:
			while len( self.entityDecrementList ) > 0 and BigWorld.time() > self.entityDecrementList[0]:
				self.destroyOne()


	def createGuard( self, timeToLive = None, owner = None ):
		"""
		Spawn a new Guard entity.
		If timeToLive is set, it will clean itself up automatically.
		If owner is set, it will register with that Base for later cleanup.
		"""
		try:
			nodeLink = random.choice( self.spawnPoints )

			guardDict = dict( self.entityCreationDictionary )

			guardDict['initialPatrolNode'] = nodeLink
			guardDict['spaceID'] = self.spaceID
			guardDict['position'] = nodeLink.position
			if timeToLive:
				guardDict['timeToLive'] = timeToLive
			if owner:
				guardDict['owner'] = owner

			BigWorld.createEntityOnBaseApp( self.entityTypeName, guardDict )

		except BigWorld.UnresolvedUDORefException:
			print 'GuardSpawner.spawnOne UnresolvedUDORefException ', nodeLink.guid
			raise

		
	def spawnOne( self, timerID ):
			self.createGuard( self.guardTimeToLive )
			self.spawnTimers[ timerID ] = self.spawnTimers[ timerID ] - 1		
	
			if self.spawnTimers[ timerID ] <= 0:
				self.cancel( timerID )
				del self.spawnTimers[ timerID ]
				if len( self.spawnTimers ) == 0:
					self.spawning = False

			self.numberSpawned = self.numberSpawned + 1
			self.entityDecrementList.append( BigWorld.time() + self.guardTimeToLive )


	def destroyOne( self ):
		if len(self.entityDecrementList) > 0:
			self.numberSpawned = self.numberSpawned - 1
			del self.entityDecrementList[0]


	def spawnLoadGuards( self, count, owner ):
		"""
		Dump a large number of guards into the game at once.
		"""
		while count > 0:
			self.createGuard( owner = owner )
			count -= 1

	# Exposed
	def spawnEntities( self, sourceID, count, duration, maxCount ):
		print 'GuardSpawner.spawnEntities', count, duration, maxCount
		queuedEntities = sum( self.spawnTimers.values() )
		entitiesToSpawn = min( count, maxCount - (self.numberSpawned + queuedEntities) )

		print 'GuardSpawner.spawnEntities entitiesToSpawn=', entitiesToSpawn

		if entitiesToSpawn <= 0:
			return
		
		frequency = duration / count
		
		timer = self.addTimer( 0, frequency, GuardSpawner.TIMER_SPAWNING )
		self.spawnTimers[timer] = entitiesToSpawn
		self.spawning = True
	
	
	def addLoadDemoGuards( self, sourceID, count ):
		self.base.addLoadDemoGuards( count )


	def delLoadDemoGuards( self, sourceID, count ):
		self.base.delLoadDemoGuards( count )


# GuardSpawner.py
