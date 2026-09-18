import BigWorld
import FantasyDemo
import AvatarModel


class Account( BigWorld.Entity ):
	def __init__( self ):
		BigWorld.Entity.__init__( self )
		self.loadedModels = None
		self.setCharacterList( self.characterList )

	# --- Logon  ---
	def failLogon( self, message ):
		FantasyDemo.addMsg( message )
		BigWorld.disconnect()
		FantasyDemo.goSinglePlayer()

	def logMessage( self, msg ):
		FantasyDemo.addLogMessage( msg )

	def switchMyCharacter( self, cName, cType ):
		self.base.switchCharacter( cName, cType )

	def createNewCharacter( self, characterName, callback ):
		self.base.createNewAvatar( str( characterName ) )
		self.createCharacterRequesterCallback = callback

	def createCharacterCallback( self, succeeded, msg, characterList ):
		self.setCharacterList( characterList )
		self.createCharacterRequesterCallback( succeeded, msg )

	def setCharacterList( self, characterList ):
		self.characterList = characterList
		resources = []
		for character in self.characterList:
			unpackedAvatarModel = AvatarModel.unpack( character['characterModel'] )
			resources.extend( AvatarModel.getPrerequisites( unpackedAvatarModel ) )
		BigWorld.loadResourceListBG( tuple( resources ), self.onModelsLoaded )

	def onModelsLoaded( self, resourceRefs ):
		self.loadedModels = resourceRefs

class PlayerAccount( Account ):
	def handleKeyEvent( self, isDown, key, mods ):
		pass


# Account.py
