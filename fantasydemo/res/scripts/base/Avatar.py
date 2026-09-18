import BigWorld
from AvatarCommon import AvatarCommon
import random
from functools import partial
import TradeHelper
import TradingSupervisor
import Inventory
import ItemBase
import FDConfig
from GameData import FantasyDemoData
from SpaceLoader import nameSeparator
import TeleportPoint
import AvatarModel
import PlayerModel

SPIRAL_START_POSITION = False
RANDOM_START_POSITION = False
# Should a log on be allowed if an entity is already logged in?
ALLOW_NEW_LOG_ONS = False

def spiralGeneratorFunc():
	pos = [0, 0]
	axis = True
	direction = True
	numSteps = 1
	iter = numSteps
	while True:
		yield pos
		pos[ axis ] += [-1, 1][ direction ]
		iter -= 1
		if iter == 0:
			axis = not axis
			if axis:
				direction = not direction
				numSteps += 1
			iter = numSteps

spiralGenerator = spiralGeneratorFunc()

class Avatar( BigWorld.Proxy, AvatarCommon ):

	# item lock states
	TRADE_OFFERING 			= 1
	TRADE_OFFER 			= 2
	TRADE_REPLYING 			= 3
	TRADE_REPLY 			= 4
	TRADE_ACCEPTING 		= 5
	TRADE_REJECTED 			= 6
	TRADE_REPLY_CANCELLING 	= 7
	TRADE_OFFER_CANCELLING 	= 8

	def __init__( self ):
		BigWorld.Proxy.__init__( self )
		AvatarCommon.__init__( self )

		# @todo: implement yellow staff and remove code below
		# *** remove yellow staff ***
		import ItemBase
		items = []
		for i in self.inventoryItems:
			if i["itemType"] != ItemBase.ItemBase.STAFF_TYPE_2:
				items.append(i)
		self.inventoryItems = items
		# ***************************

		# List of friend base mailboxes. If friend is online, mailbox is not
		# None.
		# friendBases[i] is mailbox for friendsList[i].
		self.friendBases = []
		self.inventoryMgr = Inventory.InventoryMgr( self )

		self.tradingCallbacks = {}
		for callbackType in [	'onCreateAuction',
								'onBidOnAuction',
								'onBuyoutAuction' ]:
			self.tradingCallbacks[callbackType] = {}

		self.itemAllocCallbacks = []
		self.playerInfoCallbacks = []

		# self.playerName initialised below

		# allocate item serials if we don't already have them
		# e.g. for new items

		for item in self.inventoryItems:
			if item['serial'] == -1:
				item['serial'] = self.inventoryMgr._genItemSerial()

		self.haveWebClient = False

	def onEntitiesEnabled( self ):
		if SPIRAL_START_POSITION:
			radius = 250.0
			grid = spiralGenerator.next()
			self.cellData[ "position" ] = \
					(grid[0] * radius + random.randrange( 0, radius ), 0,
					grid[1] * radius + random.randrange( 0, radius ))
			print grid, self.cellData[ "position" ]


		elif RANDOM_START_POSITION:
			radius = 5000
			self.cellData[ "position" ] = (
				random.randrange( -radius, radius ),
				0,
				random.randrange( -radius, radius )
			)
		else:
			self.cellData[ "position" ] = FantasyDemoData.DEFAULT_SPACE_START_POS

		self.playerName = self.cellData[ "playerName" ]

		self.cellData['avatarModel'] = AvatarModel.pack( self.persistentAvatarModelData )

		self.createInDefaultSpace()

		self.initFriendsList()

	def onCreateCellFailure( self ):
		print "onCreateCellFailure", self.id
		if self.account != None:
			self.account.onAvatarDeath( self.databaseID, self.cellData['avatarModel'] )
		self.client.clientOnCreateCellFailure()

	def onLoseCell( self ):
		self.notifyAdmirers( False )
		if self.account != None:
			self.account.onAvatarDeath( self.databaseID,
				self.cellData['avatarModel'] )
		if not self.haveWebClient: 	# wait for keep alive to expire if we have a
									# web session holding onto us
			self.destroy()

	def onClientDeath( self ):
		if hasattr(self, "cell" ):
			self.destroyCellEntity()
		else:
			if not self.haveWebClient:
				self.destroy()

	def teleportTo( self, label ):
		dst = BigWorld.globalBases[ label ]

		# teleport entity
		dst.teleport( self.cell )

	def tryToTeleport( self, label, isSource, spaceID ):
		try:
			if label in BigWorld.globalBases.keys() and BigWorld.globalBases[ label ].className == "TeleportPoint":
				# teleport player to location
				self.client.addInfoMsg( "Player teleporting to:" + label )
				self.client.teleportTo( label, False )
			else:
				self.matchTeleportLabel( label, isSource, spaceID )
		except:
			self.matchTeleportLabel( label, isSource, spaceID )

	def matchTeleportLabel( self, label, isSource, spaceID ):
			print "Trying to match label:", label

			# check if there is a possible match
			ds = []
			for dst in  BigWorld.globalBases.keys():
				try:
					if dst.endswith( label ) and BigWorld.globalBases[ dst ].className == "TeleportPoint":
						ds.append( dst )
				except:
					self.client.addInfoMsg( "Error: Teleport point is not correct type." )

			if len( label ) > 0 and len( ds ) > 0:
				if len( ds ) == 1:
					# teleport directly
					self.client.teleportTo( ds[0], False )
				elif isSource:
					self.client.addInfoMsg( "TeleportSource matches multiple destinations" )
				elif spaceID != 0:
					# try and teleport to each teleport point
					for dst in ds:
						BigWorld.globalBases[ dst ].cell.tryToTeleport( dst, self.id, spaceID )
				else:
					# present player with desinations to choose from
					self.client.addInfoMsg( "Your destination does not match. Try the following:")
					for d in ds:
						self.client.addInfoMsg( d )
			else:
				if isSource:
					self.client.addInfoMsg( "TeleportSource has incorrect destination" )
				else:
					self.client.addInfoMsg( "No such destination '" + label + "'")




	# -------------------------------------------------------------------------
	# Friends list
	# -------------------------------------------------------------------------
	MAX_FRIENDS = 30

	def initFriendsList( self ):
		# Send list of friend names to client.
		if not FDConfig.UNSCRIPTED_BOTS_MODE:
			self.client.newFriendsList( [ x[0] for x in self.friendsList ] )

		# Set friend base mailboxes to None (i.e. assume they are offline)
		# Note: Client also assumes friends are offline during initialisation.
		self.friendBases =  [ None for x in self.friendsList ]
		for i in range( len(self.friendsList) ):
			BigWorld.lookUpBaseByDBID( "Avatar", self.friendsList[i][1], \
				partial( self.onInitDBLookUpCb, i ) )

		self.notifyAdmirers( True )

	def onInitDBLookUpCb( self, idx, friendBase ):
		if type(friendBase) is not bool:
			# Friend is online
			self.friendBases[idx] = friendBase
			self.client.setFriendStatus( idx, True )

	def notifyAdmirers( self, online ):
		if online:
			ourBase = self
		else:
			ourBase = None
		for admirerDBID in self.admirersList:
			BigWorld.lookUpBaseByDBID( "Avatar", admirerDBID, \
				partial( Avatar_onNotifyAdmirersDBLookUpCb, self.databaseID, \
				ourBase ) )

	def addFriend( self, friendName ):
		if friendName == self.playerName:
			self.client.showMessage( 3, 'System',\
				"Adding yourself as a friend is not allowed." )
		elif len(self.friendsList) >= self.MAX_FRIENDS:
			self.client.showMessage( 3, 'System',\
				"You already have the maximum number of friends allowed: " \
				+ str(self.MAX_FRIENDS) )
		else:
			BigWorld.createBaseFromDB( "Avatar", friendName, \
				partial( self.onAddFriendCreateBaseCb, friendName ) )

	def onAddFriendCreateBaseCb( self, friendName, friendBase, dbID, \
								wasActive ):
		if friendBase != None:
			if wasActive:
				friendBase.addAdmirer( self.databaseID, self, True )
			else:
				# addAdmirer() needs playerName to be set.
				friendBase.playerName = friendBase.cellData[ "playerName" ]
				friendBase.addAdmirer( self.databaseID, self, False )
				# Should destroy the base that we've created temporarily
				friendBase.destroy()
		else:
			self.client.showMessage( 3, 'System',
				"Cannot add unknown player: " + friendName )

	def onAddedAdmirerToFriend( self, friendName, friendDBID, friendBase ):
		# Double check here due to race condition of multiple addFriends
		# when we have MAX_FRIENDS - 1 friends
		if len(self.friendsList) >= self.MAX_FRIENDS:
			self.client.showMessage( 3, 'System', \
				"You already have the maximum number of friends allowed: " \
				+ str(self.MAX_FRIENDS) )
		else:
			self.friendsList.append( ( friendName, friendDBID ) )
			self.friendBases.append( friendBase )
			online = friendBase != None
			self.client.onAddedFriend( friendName, online )

	def delFriend( self, friendIdx ):
		friendBase = self.friendBases.pop(friendIdx)
		if friendBase != None:
			friendBase.delAdmirer( self.databaseID )
		else:
			BigWorld.createBaseFromDBID( "Avatar", \
				self.friendsList[friendIdx][1], self.onDelFriendCreateBaseCb )
		del self.friendsList[ friendIdx ]

	def onDelFriendCreateBaseCb( self, friendBase, dbID, wasActive ):
		if friendBase != None:
			friendBase.delAdmirer( self.databaseID )
			# Should destroy the base that we've created temporarily
			friendBase.destroy()

	def addAdmirer( self, admirerDBID, admirerBase, online ):
		self.admirersList.append( admirerDBID )
		if online:
			onlineBase = self
		else:
			onlineBase = None
		admirerBase.onAddedAdmirerToFriend( self.playerName, self.databaseID, \
			onlineBase )

	def delAdmirer( self, admirerDBID ):
		self.admirersList.remove( admirerDBID )

	# friendBase is None if friend is going offline.
	# friendBase is friend's base mailbox if they are coming online
	def onFriendStatusChange( self, friendDBID, friendBase ):
		for i in range( len (self.friendsList ) ):
			if self.friendsList[i][1] == friendDBID:
				self.friendBases[i] = friendBase
				online = friendBase != None
				self.client.setFriendStatus( i, online )
				break

	def sendMessageToFriend( self, friendIdx, message ):
		friendBase = self.friendBases[friendIdx]
		if friendBase != None:
			friendBase.client.onReceiveMessageFromAdmirer( self.playerName, \
				message )
		else:
			self.client.showMessage( 3, 'System',
				"Cannot send message to offline player." )

	def getFriendInfo( self, friendIdx ):
		friendBase = self.friendBases[friendIdx]
		if friendBase != None:
			friendBase.getInfoForAdmirer( self )
		else:
			self.client.showMessage( 3, 'System', \
				"Cannot get information on offline player." )

	def getInfoForAdmirer( self, admirerBase ):
		friendNames = [ name for (name, dbid) in self.friendsList ]
		self.cell.getInfoForAdmirer( \
			"[Friends: " + str(friendNames)[1:-1] + "]", admirerBase )

	#make so that system can talk to client
	def messageToClient( self, mesg ):
		self.client.showMessage( 3, 'System', mesg )

	def setBandwidthPerSecond( self, bps ):
		self.bandwidthPerSecond = bps

	# -------------------------------------------------------------------------
	# Section: Items trading
	# -------------------------------------------------------------------------

	def tradeCommitActive( self, outItemsLock ):
		"""Cell is requesting base to commit an items trade (actively).
		Params:
			outItemsLock		lock handle to item being traded out
		"""
		self.outItemsLock = outItemsLock
		# now wait for tradeSyncRequest


	def tradeSyncFail( self ):
		"""The passive base is notifying us that it could not
		initiate the trade (by calling tradeSyncRequest).
		"""
		self.tradeCommitNotify( False, self.outItemsLock, [], 0, [], [], 0 )


	def tradeCommitPassive( self, outItemsLock, activeBase ):
		"""Cell is requesting base to commit an items trade (passively).
		Params:
			outItemsLock		lock handle to item being traded out
			activeBase			base of active partner
		"""
		try:
			itemsSerials, itemsTypes, goldPieces = \
					self.inventoryMgr.itemsLockedRetrieve( outItemsLock )

			tradeParams = { "dbID": self.databaseID, \
							"tradeID": self.lastTradeID+1, \
							"lockHandle": outItemsLock, \
							"itemsSerials": itemsSerials, \
							"itemsTypes": itemsTypes, \
							"goldPieces": goldPieces	}

			activeBase.tradeSyncRequest( self, tradeParams )

		except Inventory.LockError:
			activeBase.tradeSyncFail()
			self.tradeCommitNotify( False, outItemsLock, [], 0, [], [], 0 )
			errorMsg = "Avatar.tradeCommitPassive: couldn't retrieve locked "\
				"items "
			parameters = '(lock=%d)' % outItemsLock
			print errorMsg + parameters


	def tradeSyncRequest( self, partnerBase, partnerTradeParams ):
		"""The meeting of the active and passive trading info collections.
		Will request TradingSupervisor to commence a trading operation.
		Params:
			partnerBase			base of partner
			partnerDBID			BDID of partner
			partnerTradeID		tradeID of partner
			inItemsLock			lock handle to items being traded in
			inItemsSerials		serial of items being traded in
			inItemsTypes	   types of items being traded in
			inGoldPieces      ammount of gold being traded in
		"""
		try:
			outItemsSerials, outItemsTypes, outGoldPieces = \
					self.inventoryMgr.itemsLockedRetrieve( self.outItemsLock )
			supervisor = BigWorld.globalBases[ "TradingSupervisor" ]

			selfTradeParams = { "dbID": self.databaseID, \
								"tradeID": self.lastTradeID+1, \
								"lockHandle": self.outItemsLock, \
								"itemsSerials": outItemsSerials, \
								"itemsTypes": outItemsTypes, \
								"goldPieces": outGoldPieces	}

			supervisor.commenceTrade( self, selfTradeParams,
				partnerBase, partnerTradeParams )

		except Inventory.LockError:
			errorMsg  = 'Avatar.tradeSyncRequest: lock error (lock=%d)'
			print errorMsg % ( self.outItemsLock )


	def tradeSyncReject( self ):
		self.tradeCommitNotify( False, self.outItemsLock, [], 0, [], [], 0 )
		partnerBase.tradeCommitNotify( False, partnerTradeParams[
			"lockHandle" ], [], 0, [], [], 0 )


	def tradeCommit(
			self, supervisor, tradeID, outItemsLock,
			outItemsSerials, outGoldPieces,
			inItemsTypes, inGoldPieces ):
		"""Performs the trade for this entity.
		Params:
			supervisor			mailbox of trading supervisor
			tradeID				ID of this trade
			outItemsLock		lock handle to items being traded out
			outItemsSerials	serial of items being traded out
			outGoldPieces		ammount of gold being traded out
			inItemsTypes	   types of items being traded in
			inGoldPieces      ammount of gold being traded in
		"""
		TradeHelper.tradeCommit(
			self, supervisor, tradeID, outItemsLock,
			outItemsSerials, outGoldPieces,
			inItemsTypes, inGoldPieces )


	def tradeCommitNotify( self, success,
			outItemsLock, outItemsSerials,
			outGoldPieces, inItemsTypes,
			inItemsSerials, inGoldPieces ):
		"""The active party (either us our our partner) is informing us the
		result of the trade sync. Forward this information to the cell.
		Params:
			success:				True is trade was successful. False is it failed
			outItemsLock		lock handle to items being traded out
			outItemsSerials	serial of items being traded out
			outGoldPieces		ammount of gold being traded out
			inItemsTypes	   types of items being traded in
			inGoldPieces      ammount of gold being traded in
		"""
		if not success and outItemsLock != 0:
			try:
				self.inventoryMgr.itemsUnlock( outItemsLock )
			except Inventory.LockError:
				errorMsg = "Avatar.tradeCommitNotify: couldn't unlock items (lock=%d)"
				print errorMsg % outItemsLock

		if hasattr(self, 'cell'):
			self.cell.tradeCommitNotify( success, outItemsLock,
					outItemsSerials, outGoldPieces, inItemsTypes,
					inItemsSerials, inGoldPieces )

	# -------------------------------------------------------------------------
	# Section: Items locking
	# -------------------------------------------------------------------------

	def itemsLockRequest( self, lockHandle, itemsSerials, goldPieces ):
		"""The cell is requesting us to lock inventory items.
		Params:
			lockHandle			lock handle to be reused
			itemsSerials		serials of items to be locked
			goldPieces			ammount of gold to be locked
		"""
		try:
			inventoryMgr = self.inventoryMgr

			if lockHandle == Inventory.NOLOCK:
				lockHandle = inventoryMgr.itemsLock(itemsSerials, goldPieces)
			else:
				inventoryMgr.itemsRelock( lockHandle, itemsSerials, goldPieces )
			itemsSerials, itemsTypes, goldPieces = \
					inventoryMgr.itemsLockedRetrieve( lockHandle )

			if hasattr( self, 'cell' ):
				self.cell.itemsLockNotify( True, lockHandle,
						itemsSerials, itemsTypes, goldPieces )

		except (Inventory.LockError, ValueError), e:
			print "Lock error: %s: %s" % ( e.__class__, e )
			if hasattr(self, 'cell'):
				self.cell.itemsLockNotify( False, lockHandle, [], [], 0 )
			errorMsg  = 'Avatar.itemsLockRequest: lock error '
			arguments = '(lock=%d, items=%s, gold=%d)'
			print errorMsg + arguments % ( lockHandle, itemsSerials, goldPieces )

		return lockHandle

	def itemsUnlockRequest( self, lockHandle ):
		"""the client (via the cell) is requesting us to unlock inventory items.
		Params:
			lockHandle			handle to the previously locked items.
		"""
		supervisor = BigWorld.globalBases[ "TradingSupervisor" ]
		if not supervisor.isAPendingTrade( self.id, lockHandle ):
			try:
				self.inventoryMgr.itemsUnlock( lockHandle )
			except Inventory.LockError:
				pass
			success = True
		else:
			success = False

		if hasattr(self, 'cell'):
			self.cell.itemsUnlockNotify( success, lockHandle )

		return success

	# -------------------------------------------------------------------------
	# Section: Web interface methods
	# -------------------------------------------------------------------------


	def webGetPlayerInfo( self, response ):
		"""
		Retrieves the player name and other player info.

		Return values: 	playerName::STRING
						online::BOOL
						databaseID::DATABASEID
						health::INT32
						maxHealth::INT32
						frags::INT32
		"""

		response.databaseID = self.databaseID
		response.charClass = \
			PlayerModel.modelListToCharacterClassString(
				self.persistentAvatarModelData['models'] )

		if not hasattr( self, 'cell' ):
			response.online = False
			response.playerName = self.cellData['playerName']
			response.position = (0., 0., 0.)
			response.direction = (0., 0., 0.)
			response.health = self.cellData['health']
			response.maxHealth = self.cellData['maxHealth']
			response.frags = self.cellData['frags']
			response.done()
		else:
			response.online = True
			# need to ask the cell to retrieve some of this information
			self.playerInfoCallbacks.append( response )
			self.cell.getPlayerInfoBaseRequest()


	def onPlayerInfo( self, playerName, position, direction, health,
			maxHealth, frags ):
		"""
		Called back from the cell after a request to retrieve player
		information.

		@param	playerName		the player's name
		@param	position		the player's position as a float 3-tuple
		@param	direction		the player's direction as a float 3-tuple
		@param	health			the player's health
		@param	maxHealth		the player's maximum health
		@param	frags			the player's frag count
		"""

		if self.playerInfoCallbacks:
			response = self.playerInfoCallbacks.pop( 0 )

			response.playerName 	= playerName
			response.position 		= position
			response.direction 		= direction
			response.health 		= health
			response.maxHealth 		= maxHealth
			response.frags 			= frags

			response.done()


	def webGetGoldAndInventory( self, response ):
		"""
		Retrieves the available gold pieces and the inventory state.

		Response return values:

		response.goldPieces::GOLDPIECES
			The Avatar's available gold pieces.

		response.inventoryItems::PYTHON
			List of item descriptions as dictionaries with keys:
				'serial':		the serial number of the item
				'itemType':		the item type
				'lockHandle':	lock handle associated with this item

		lockedItems::PYTHON
			List of locked item descriptions as dictionaries with keys:
				'serials':		a list of serial numbers of locked items
				'goldPieces':	the gold pieces locked

		"""

		response.goldPieces = self.inventoryMgr.availableGoldPieces()

		response.inventoryItems = []
		response.lockedItems = {}

		for lockedEntry in self.inventoryLocks:
			response.lockedItems[ lockedEntry["lockHandle"] ] = {
				'serials'		: [],
				'goldPieces'	: lockedEntry[ "goldPieces" ]
			}

		for inventoryEntry in self.inventoryItems:
			response.inventoryItems.append( {
				'serial'		: inventoryEntry['serial'],
				'itemType'		: inventoryEntry['itemType'],
				'lockHandle'	: inventoryEntry['lockHandle']
			} )

			if inventoryEntry['lockHandle'] != -1:
				response.lockedItems[inventoryEntry['lockHandle']]['serials'].\
					append( inventoryEntry['serial'] )

		response.done()


	def webCreateAuction( self, response,
			itemSerial, expiry, startBid, buyout ):
		"""
		Web method to create an auction.

		Response return values:
		response.success::BOOL
			Success?

		response.errMsg::STRING
			Error message.

		response.auctionID::AUCTIONID
			The auction ID of the new auction.
		"""

		#print "Avatar(dbid=%d).webCreateAuction( " \
		#	"itemSerial=%s, expiry=%.01f, startBid=%d, buyout=%s )" % \
		#	(self.databaseID, itemSerial, expiry, startBid, str( buyout ))

		itemType = None

		# find the item type of the item pointed to by the item serial
		for itemDesc in self.inventoryItems:
			if itemDesc['serial'] == itemSerial:
				itemType = itemDesc['itemType']
				break

		if itemType is None:
			response.errMsg = "Could not retrieve item type for itemSerial=%d"\
				% (itemLock)
			response.success = False
			response.done()
			return

		# Lock the item.
		itemLock = self.itemsLockRequest( -1, [ itemSerial ], 0 )
		if itemLock == -1:
			response.errMsg = "Could not lock item with serial: %s" %\
				(itemSerial)
			response.success = False
			response.done()
			return

		try:
			auctionHouse = BigWorld.globalBases['AuctionHouse']
		except KeyError:
			self.itemsUnlockRequest( itemLock )
			response.errMsg = 'Auction House entity does not exist or ' \
				'is not globally registered.'
			response.success = False
			response.done()
			return


		self.tradingCallbacks['onCreateAuction'][ itemSerial ] = \
			partial( self._webCreateAuction2, itemSerial, itemLock, response )

		auctionHouse.createAuction( self, self.databaseID, itemLock, itemType, itemSerial,
			startBid, expiry, buyout )


	def onCreateAuction( self, itemSerial, auctionID, success, errMsg ):
		"""
		Callback from AuctionHouse entity when it is finished creating an
		auction.

		@param 	itemSerial	The item serial.
		@param	auctionID	The auction ID.
		@param	success		Success?
		@param	errMsg		Error message.
		"""

		callbacks = self.tradingCallbacks['onCreateAuction']
		cb = callbacks[ itemSerial ]
		del callbacks[ itemSerial ]
		cb( auctionID, success, errMsg )


	def _webCreateAuction2( self, itemSerial, itemLock, response, auctionID,
			success, errMsg ):

		response.success = success
		if success:
			response.auctionID = auctionID
		else:
			# unlock serial
			print "Avatar._webCreateAuction2: Unlocking itemLock=%s because" \
				"of failure to create auction: %s: " %\
				( str( itemLock ), errMsg ),
			if self.itemsUnlockRequest( itemLock ):
				print "success"
			else:
				print "failed"
		response.errMsg = errMsg
		response.done()


	def webBidOnAuction( self, response, auctionID, buyingOut, bidAmount ):
		"""
		Web method to bid on, or to buyout, an auction. Buyouts are indicated
		by asserting the buyingOut boolean value, in which case the bidAmount
		value is ignored.

		@param	response	The response object.
		@param	auctionID 	The auction ID.
		@param	buyingOut	Whether to bid or buyout the auction.
		@param	bidAmount	This represents the maximum bid amount by the
							calling entity.

		Response return values:

		response.success::BOOL
			Whether the action was successful.

		response.errMsg::STRING
			The error message.

		"""

		#print "Avatar(dbid=%d).webBidOnAuction( " \
		#	"auctionID=%s, buyingOut=%s, bidAmount=%d" % \
		#	(self.databaseID, auctionID, str( buyingOut ), bidAmount)

		try:
			auctionHouse = BigWorld.globalBases['AuctionHouse']
		except KeyError:
			print "Avatar(dbid=%d).webBidOnAuction: "\
				"Couldn't find AuctionHouse entity!" %\
				(self.databaseID)
			response.success = False
			response.errMsg = "Could not find AuctionHouse entity."
			response.done()
			return

		if buyingOut:
			#print "Avatar.webBidOnAuction: Buying out!"
			self.tradingCallbacks[ 'onBuyoutAuction' ][ auctionID ] = \
				partial( self._webBuyoutAuction2, response )
			auctionHouse.buyoutAuction( self, self.databaseID, auctionID )
			# we need the buyout amount, we are called back on lockGoldAmount
			return

		# lock away the bidAmount
		if self.inventoryMgr.availableGoldPieces() < bidAmount:
			response.success = False
			response.errMsg = \
				"You do not have sufficient available gold to make this bid"
			response.done()
			#print "Avatar(dbid=%d).webBidOnAuction: " \
			#	"Insufficient gold to make bid" % \
			#	(self.databaseID)
			return

		lockHandle = self.itemsLockRequest( Inventory.NOLOCK, [], bidAmount )
		if lockHandle == -1:
			response.success = False
			response.errMsg = "Could not lock %d gold"
			response.done()
			print "Avatar(dbid=%d).webBidOnAuction: Could not lock gold" %\
				(self.databaseID)
			return

		self.tradingCallbacks[ 'onBidOnAuction' ][ auctionID ] = \
			partial( self._webBidOnAuction2, response, lockHandle )
		auctionHouse.bidOnAuction( self, self.databaseID, auctionID, bidAmount,
			lockHandle )


	def onBidOnAuction( self, auctionID, success, errMsg ):
		"""
		Callback from the AuctionHouse when the bid initiated from this player
		has been completed.

		@param	auctionID	the auction ID
		@param	success		success?
		@param	errMsg		error message
		"""

		# find the callback
		callbacks = self.tradingCallbacks['onBidOnAuction']
		cb = callbacks[ auctionID ]
		del callbacks[auctionID]
		cb( auctionID, success, errMsg )


	def _webBidOnAuction2( self, response, lockHandle, auctionID, success,
			errMsg ):

		#print "Avatar(dbid=%d).webBidOnAuction: " \
		#	"auctionID=%s, success=%s, errMsg=%s" %\
		#	(self.databaseID, auctionID, success, errMsg)

		if not success:
			self.itemsUnlockRequest( lockHandle )
		response.success = success
		response.errMsg = errMsg
		response.done()


	def onBuyoutAuction( self, auctionID, success, errMsg ):
		"""
		Callback method from the AuctionHosue when it has finished processing
		a buyout done by this player.

		@param	auctionID	the auction ID
		@param	success		success?
		@param	errMsg		error message
		"""

		# find the callback
		callbacks = self.tradingCallbacks[ 'onBuyoutAuction' ]
		cb = callbacks[ auctionID ]
		del callbacks[ auctionID ]
		cb( auctionID, success, errMsg )


	def _webBuyoutAuction2( self, response, auctionID, success, errMsg ):

		response.success = success
		response.errMsg = errMsg
		response.done()


	def lockAuctionGold( self, auctionID, goldAmount, existingLock ):
		"""
		A request method for the AuctionHouse to (re)lock an amount of gold
		to complete an auction.

		If there is an existing lock that needs to be unlocked prior to the new
		lock, it can be provided, and it is unlocked before relocking the given
		gold amount.

		Calls back on AuctionHouse.onLockGoldAmount when complete.

		@param	auctionID		the auction ID
		@param	goldAmount		the gold amount to lock
		@param	existingLock	any existing lock to be unlocked prior to
								locking the goldAmount
		"""

		auctionHouse = BigWorld.globalBases['AuctionHouse']
		if existingLock != -1:
			# check whether we have enough gold before we unlock the old lock

			(lockedItemsSerials, lockedItemsTypes, lockedGoldPieces) = \
				self.inventoryMgr.itesmLockedRetrieve( existingLock )

			if lockedGoldPieces + self.inventoryMgr.availableGoldPieces() \
					< goldAmount:
				auctionHouse.onLockGoldAmount( False,
					"Insufficient gold pieces",
					auctionID, self, Inventory.NOLOCK )
				return

			self.itemsUnlockRequest( existingLock )

		lockHandle = self.itemsLockRequest( Inventory.NOLOCK,
				[], goldAmount )

		if lockHandle == Inventory.NOLOCK:
			auctionHouse.onLockGoldAmount( False, "Could not lock gold",
				auctionID, self, lockHandle )
		else:
			auctionHouse.onLockGoldAmount( True, '',
				auctionID, self, lockHandle )


	def onAuctionExpired( self, auctionID, itemLock ):
		"""
		Callback from the AuctionHouse when an auction sold by this player
		expires without a bid having been placed.
		"""

		#print "Avatar.onExpireAuction: auctionID=%s, itemLock=%s" %\
		#	(str( auctionID ), str( itemLock ))

		self.itemsUnlockRequest( itemLock )


	def onAuctionWon( self, auctionID, itemLock, bidPrice ):
		"""
		Callback method from the AuctionHouse when this Avatar has won an
		auction. Calls back on the AuctionHouse.completeAuction to complete
		the trade with the new lock handle for the auction bid amount at
		expiry (which may be different from the maximum bid amount made by
		this player).

		@param	auctionID	the auction ID
		@param	itemLock	the lock handle for the maximum bid used when this
							player bid
		@param	bidPrice	the actual amount of gold that the auction was bid
							at when it expired
		"""

		#print "Avatar.onWinAuction: "\
		#	"auctionID = %s, itemLock = %d, bidPrice = %d" \
		#	% (auctionID, itemLock, bidPrice)

		# unlock my maximum bid, and relock the auction bid amount at expiry
		self.itemsUnlockRequest( itemLock )
		newLockHandle = self.itemsLockRequest( Inventory.NOLOCK, [], bidPrice )

		# notify the AuctionHouse to do the trade
		BigWorld.globalBases['AuctionHouse'].completeAuction(
			auctionID, self, newLockHandle )


	def onAuctionOutbid( self, auctionID, itemLock ):
		"""
		Callback method from the AuctionHouse when this Avatar has been outbid
		by another bidder for the specified auction that this player has bid on.

		@param	auctionID	the auction ID
		@param	itemLock	the lock handle for the maximum bid used when this
							player bid
		"""

		#print "Avatar.onAuctionOutbid: "\
		#	"databaseID=%d, auctionID=%s, itemLock=%d" % \
		#	(self.databaseID, auctionID, itemLock)

		# give me my money back!
		self.itemsUnlockRequest( itemLock )

	def setAvatarModel( self, encodedAvatarModel ):
		self.persistentAvatarModelData = AvatarModel.unpack( encodedAvatarModel )
		self.cell.setAvatarModel( encodedAvatarModel )

	# -------------------------------------------------------------------------
	# Section: Items pick-up and drop
	# -------------------------------------------------------------------------

	def pickUpResponse( self, success, droppedItemID, itemType ):
		"""DroppedItem is responding to a pickup request (by the avatar's cell).
		Params:
			success			True is pickup request was granted. False otherwise
			droppedItemID	id of item entity being picked up
			itemType			type of item being picked up
		"""
		if success:
			itemsSerial = self.inventoryMgr.addItem( itemType )
			self.cell.pickUpResponse( True, droppedItemID, itemType, itemsSerial )

		else:
			self.cell.pickUpResponse( False, droppedItemID, 0, 0 )

	def dropRequest( self, itemSerial ):
		"""Client is requesting to drop an item from the inventory.
		Params:
			itemSerial			serial of item to be dropped
		"""
		try:
			itemType = self.inventoryMgr.removeItem( itemSerial )
			self.cell.dropNotify( itemSerial, itemType )
		except ValueError:
			self.client.dropDeny()
			errorMsg = 'Avatar.dropNotify: No such item in inventory: %d'
			print errorMsg % itemSerial
		except Inventory.LockError:
			self.client.dropDeny()
			errorMsg = 'Avatar.dropNotify: Item is locked: %d'
			print errorMsg % itemSerial

	# -------------------------------------------------------------------------
	# Section: Items commerce
	# -------------------------------------------------------------------------

	def commerceSellRequest( self, itemsLock, itemSerial, merchantBase ):
		"""Cell is requesting to sell an item to a merchant.
		Lock item and request merchant to buy the item from use.
		Params:
			itemLock				handle to locked item in client
			itemSerial			serial of item in inventory
			merchantBase		base mailbox of the buyer merchant
		"""
		try:
			inventoryMgr = self.inventoryMgr
			inventoryMgr.itemsRelock( itemsLock, [itemSerial], 0 )
			self.outItemsLock = itemsLock
			itemsSerials, itemTypes, gold = \
					inventoryMgr.itemsLockedRetrieve( self.outItemsLock )
			merchantBase.commerceBuyRequest(
					self.outItemsLock, itemsSerials, itemTypes, self )
			# now wait for tradeSyncRequest (called by the merchant)
		except (Inventory.LockError, ValueError):
			self.tradeCommitNotify( False, itemsLock, [], 0, [], [], 0 )
			errorMsg  = 'Avatar.commerceSellRequest: lock error (item=%d)'
			print errorMsg % ( itemSerial )


	def commerceBuyRequest( self, avatarLock,
			merchantBase, merchantDBID, merchantTradeID,
			merchantLock, itemsSerials, itemsTypes ):
		"""A merchant is requesting up to buy an item from him.
		Delegates processing to the trade helper class.
		Params:
			avatarLock			handle to locked item in client.
			merchantBase		base mailbox of the seller merchant.
			merchantDBID		DBID of seller merchant
			merchantTradeID	tradeID of seller merchant
			merchantLock		handle of locke item in seller's inventory
			itemsSerials		serials of items being bought
			itemsTypes			types of items being bought
		"""
		try:
			itemPrice = ItemBase.price( itemsTypes[0] )
			self.inventoryMgr.itemsRelock( avatarLock, [], itemPrice )
			self.outItemsLock = avatarLock

			merchantParams = { "dbID": merchantDBID, \
								"tradeID": merchantTradeID, \
								"lockHandle": merchantLock, \
								"itemsSerials": itemsSerials, \
								"itemsTypes": itemsTypes, \
								"goldPieces": 0	}

			self.tradeSyncRequest( merchantBase, merchantParams )

		except Inventory.LockError:
			self.tradeCommitNotify( False, avatarLock, [], 0, [], [], 0 )
			merchantBase.tradeCommitNotify( False, merchantLock, [], 0, [], [], 0 )
			errorMsg  = 'Avatar.commerceBuyRequest: lock error (gold=%d)'
			print errorMsg % ( itemPrice )


	def onLogOnAttempt( self, ip, port ):
		# Allow log on to this entity if there is no client, ie from the web.
		if self.clientAddr == (0, 0):
			return BigWorld.LOG_ON_ACCEPT
		else:
			if ALLOW_NEW_LOG_ONS:
				# Log this entity off and let the new log on to then proceed
				# normally.
				self.logOff()
				return BigWorld.LOG_ON_WAIT_FOR_DESTROY
			else:
				# Do not allow the log on attempt.
				return BigWorld.LOG_ON_REJECT

	def onKeepAliveStart( self ):
		self.haveWebClient = True

	def onKeepAliveStop( self ):
		print "Avatar(%d).onKeepAliveStop" % self.id
		self.haveWebClient = False
		self.webLogout()

	def webLogout( self ):
		print "Avatar(%d).webLogout" % self.id
		if not hasattr( self, "cell" ):
			if self.account != None:
				self.account.onAvatarDeath( self.databaseID, self.cellData['avatarModel'] )
			self.destroy()


# end of class Avatar

# this callback needs to be a global instead of a method of Avatar because we
# notify our admirers when the Avatar is being destroyed.
def Avatar_onNotifyAdmirersDBLookUpCb( ourDBID, ourBase, admirerBase ):
	if type(admirerBase) is not bool:
		# Admirer is online
		admirerBase.onFriendStatusChange( ourDBID, ourBase )

# Avatar.py

