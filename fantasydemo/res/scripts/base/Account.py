import BigWorld
from functools import partial
import AvatarModel
import PlayerModel

# ------------------------------------------------------------------------------
# Section: class Account
# ------------------------------------------------------------------------------

# This function is supposed to call the billing system.
def AsyncBillingRequest( username, password, callback ):
	print "BigWorld Billing [ Username: ", username, ", Password: ", password, "]"
	if (len(password) % 2) == 0:
		print "BigWorld Billing [",username," accepted ]"
		callback( True )
	else:
		print "BigWorld Billing [",username," rejected ]"
		callback( False )

class Account( BigWorld.Proxy ):

	def __init__( self ):
		BigWorld.Proxy.__init__( self )
		self.isBot = False
		self.haveWebClient = False
		self.updateCharacterList()

	def onEntitiesEnabled( self ):
		if self.activeCharacter == None:
			if self.accountName.startswith( 'Bot_' ):
				self.botLoggedOn()
			else:
				AsyncBillingRequest( self.accountName, self.password, self.onBillingReqCb )
		else:
			# Re-login attempt, give client straight away
			self.activeCharacter.giveClientTo( None )
			self.giveClientTo( self.activeCharacter )

	def onLogOnAttempt( self, ip, port, password ):
		if ip == 0:
			# from web login, let it come in regardless
			return BigWorld.LOG_ON_ACCEPT
		if self.activeCharacter != None:
			# already have a character logged on - reject
			return BigWorld.LOG_ON_REJECT
		if ip == self.lastClientIpAddr and password == self.password:
			return BigWorld.LOG_ON_ACCEPT
		if self.clientAddr[0] == 0:
			# if we only have a web session holding onto us, allow
			return BigWorld.LOG_ON_ACCEPT

		# default - reject re-logon
		return BigWorld.LOG_ON_REJECT



	def onBillingReqCb( self, success ):
		if success:
			if (self.databaseID == 0):
				self.writeToDB()
		else:
			self.failLogon( "Rejected by billing system"  )

	def botLoggedOn( self ):
		self.isBot = True
		if len(self.characterList) == 0:
			self.createNewAvatar( self.accountName )
		else:
			self.characterBeginPlay( self.characterList[0]['name'] )


	def createNewAvatar( self, avatarName, response=None ):
		avatar = BigWorld.createBaseLocally( "Avatar",
				{ "playerName":avatarName,
					"persistentAvatarModelData":PlayerModel.randomPlayerModel() } )
		avatar.writeToDB( partial( self.onCreatedNewAvatar, response=response) )

	def characterBeginPlay( self, characterName ):
		for character in self.persistentCharacterList:
			if character['name'] == characterName:
				BigWorld.createBaseFromDBID(	character['type'],
												character['databaseID'],
												self.onLoadedAvatar )
				return
		print 'Unknown character', characterName


	def onCreatedNewAvatar( self, success, avatar, response ):
		if success:
			newAvatarName = avatar.cellData['playerName']
			self.persistentCharacterList.append( dict(
													name = newAvatarName,
													databaseID = avatar.databaseID,
													type = 'Avatar',
													characterModel = avatar.persistentAvatarModelData ) )
			self.updateCharacterList()
			print 'New character', newAvatarName, 'created'
			if self.isBot:
				self.onAvatarReady( avatar )
			else:
				avatar.destroy()
				if response == None:
					self.client.createCharacterCallback( True, '', self.characterList )
				else:
					# web request
					response.success = True
					response.done()
		else:
			print 'Failed to create new Avatar %s for player %s' % \
				(avatar.cellData['playerName'], self.accountName)
			if not self.isBot:
				errMsg = 'A character with name %s already exists.' % \
					avatar.cellData['playerName']
				self.client.createCharacterCallback( False, errMsg, self.characterList )
			avatar.destroy()
			if response:
				response.success = False
				response.errMsg = errMsg
				response.done()

	def updateCharacterList( self ):
		newCharacterList = []
		for character in self.persistentCharacterList:
			newCharacter = {}
			newCharacter['name'] = character['name']
			newCharacter['characterModel'] = AvatarModel.pack( character['characterModel'] )
			newCharacterList.append( newCharacter )
		self.characterList = newCharacterList

	def onLoadedAvatar( self, avatar, dbID, wasActive ):
		if avatar != None and \
				BigWorld.entities.has_key( avatar.id ):
			# We should be on the same BaseApp as the avatar, but we may still
			# be passed a mailbox if the entity is already checked out.
			avatar = BigWorld.entities[avatar.id]
			self.onAvatarReady( avatar )
		else:
			if avatar != None:
				print "Account(%d).onLoadedAvatar: Avatar %d is not on " \
						"the same BaseApp as this account" % \
					(self.id, avatar.id)
			else:
				print "Account(%d).onLoadedAvatar: " \
						"Failed to load %s for player %s" % \
					(self.characterList[0]['type'], self.accountName)
			self.onAvatarReady( None )

	def onAvatarReady( self, avatar ):
		if avatar != None:
			self.activeCharacter = avatar
			avatar.account = self
			self.lastClientIpAddr = self.clientAddr[0]
			self.giveClientTo( avatar )
			if self.databaseID == 0:
				print "Writing Account to DB"
				self.writeToDB()
		else:
			self.failLogon( "Failed to create your avatar."  )

	def onClientDeath( self ):
		print "Account(%d).onClientDeath" % self.id
		if not self.haveWebClient:
			self.destroy()

	def onAvatarDeath( self, avatarDBID, avatarModel ):
		if self.isDestroyed:
			# Avatar could be holding a reference to us while we're destroyed
			return

		print "Account(%d).onAvatarDeath" % self.id
		for character in self.persistentCharacterList:
			if character['databaseID'] == avatarDBID:
				character['characterModel'] = AvatarModel.unpack( avatarModel )
		self.activeCharacter = None
		if not self.haveWebClient:
			self.destroy()

	def failLogon( self, message ):
		self.client.failLogon( message  )
		self.addTimer( 0.5 )

	def onTimer( self, id, userArg ):
		self.giveClientTo( None )
		self.destroy()

	# --- Character list stuff ---
	def updatePlayerCharacter( self, newEntity, dbID, wasActive ):
		print "Account.updatePlayerCharacter:"
		if newEntity != None:
			self.giveClientTo( newEntity )
			self.destroy()
		else:
			print "Failed to create new entity"
			self.client.logMessage( "Failed to load the character" )

	def switchCharacter( self, cName, cType ):
		def updateCharacterList( success, entity ):
			if success:
				newC = {}
				newC['name'] = cName
				newC['type'] = cType
				newC['databaseID'] = entity.databaseID
				self.characterList.append( newC )
				self.updateCharacterList()
				self.updatePlayerCharacter( entity, entity.databaseID, False )
			else:
				print "Failed to write new entity to the database"
				self.client.logMessage( "Internal error! "
					"Can't save newly created character. Abort!" )

		found = False

		for c in self.characterList:
			if c['name'] == cName and c['type'] == cType:
				found = True
				break
		if found:
			BigWorld.createBaseFromDBID( c['type'], c['databaseID'],
				self.updatePlayerCharacter )
		else:
			try:
				newCharacter = BigWorld.createBaseLocally( cType )
				# Write to database so that we can get a DBID
				newCharacter.writeToDB( updateCharacterList )
			except:
				print "Failed to create new entity of %s type" % cType
				self.client.logMessage( "Can't create new character. Abort!" )
				pass

#			self.client.addMessage( 'unable to find select character' )

	def webGetCharacterList( self, response ):
		response.characters = []
		for character in self.persistentCharacterList:
			cInfo = {}
			cInfo['name'] = character.name
			cInfo['type'] = character.type
			cInfo['databaseID'] = character.databaseID
			cInfo['charClass'] = \
				PlayerModel.modelListToCharacterClassString(
					character.characterModel.models )
			response.characters.append( cInfo )
		response.done()

	def webChooseCharacter( self, response, cName, cType ):
		found = False

		for c in self.persistentCharacterList:
			if c['name'] == cName and c['type'] == cType:
				found = True
				break
		if found:
			def onWebChooseCharacter( response, avatar, dbID, active ):
				if type( avatar ) == bool:
					response.errMsg = "Could not load from database"
				else:
					print "Account(%d).webChooseCharacter: " \
							"got avatar entity: %d" % \
						(self.id, avatar.id)
					response.character = avatar

				response.done()

			BigWorld.createBaseFromDBID( c['type'], c['databaseID'],
				partial( onWebChooseCharacter, response ) )
		else:
			response.errMsg = "Cannot find character"
			response.done()

	def webCreateCharacter( self, response, name ):
		self.createNewAvatar( name, response )

	def webLogout( self ):
		print "Account(%d).webLogout" % self.id
		if not self.hasClient and self.activeCharacter == None:
			self.destroy()

	def onKeepAliveStart( self ):
		self.haveWebClient = True

	def onKeepAliveStop( self ):
		print "Account(%d).onKeepAliveStop" % self.id
		self.haveWebClient = False
		self.webLogout()


# Account.py
