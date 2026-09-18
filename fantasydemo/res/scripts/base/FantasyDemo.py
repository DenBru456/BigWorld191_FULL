import BigWorld
import FDConfig
import TradingSupervisor
import AuctionHouse
import HierarchyCheck
from GameData import FantasyDemoData
import Watchers

# This is imported here to avoid loading in the main thread.
import UserDataObjectRef


# ------------------------------------------------------------------------------
# Section: Callbacks
# ------------------------------------------------------------------------------

def onBaseAppReady( isBootstrap ):
	# If we are restoring from database, we will already have entities.
	isRestoring = (len( BigWorld.entities ) != 0)

	# Load all the runscript watchers for this baseapp
	Watchers.addWatchers()

	if isBootstrap and not isRestoring:
		TradingSupervisor.wakeupTradingSupervisor()
		AuctionHouse.wakeup()

		isDefault = True

		# create space loader for each space
		for geometry in FantasyDemoData.SPACES:
			entity = BigWorld.createBaseLocally( "SpaceLoader",
						geometry = geometry,
						isDefault = isDefault)
			isDefault = False

def onBaseAppShutDown( state ):
	if state == 0:
		TradingSupervisor.destroyTradingSupervisor()
		AuctionHouse.destroyAuctionHouse()

# ------------------------------------------------------------------------------
# Section: Common base class
# ------------------------------------------------------------------------------

class Base( BigWorld.Base ):
	def __init__( self ):
		BigWorld.Base.__init__( self )

		# This is useful if using disaster recovery.
		# if not self.databaseID:
		#	self.writeToDB()

		if hasattr( self, "cellData" ):
			try:
				cell = self.createOnCell
				self.createOnCell = None
			except AttributeError, e:
				cell = None

			if cell != None:
				self.createCellEntity( cell )
			elif self.cellData["spaceID"]:
				self.createCellEntity()
			else:
				self.createInDefaultSpace()

	def onLoseCell( self ):
		rsm = None
		if hasattr( self, 'respawnInterval' ) and self.respawnInterval != 0:
			gb = BigWorld.globalBases
			if not gb.has_key( 'RespawnManager' ):
				rsm = BigWorld.createEntity( 'RespawnManager' )
			else:
				rsm = gb['RespawnManager']
			rsm.registerForRespawn( self.__module__, self.entityData, self.respawnInterval )
		self.destroy()

def onInit( isReload ):
	""" Callback function when scripts are loaded. """

	# Check that the entitydef inheritance hierarchy strictly
	# matches the Python class hierarchy.

	# HierarchyCheck.checkTypes()
	pass

# FantasyDemo.py
