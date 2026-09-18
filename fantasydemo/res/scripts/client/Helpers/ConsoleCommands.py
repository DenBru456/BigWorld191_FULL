"""This module implements console commands.

Each function in this module corresponds to a console command. To add another
console command just add a function with the correct prototype.
"""

import BigWorld
import FantasyDemo
import Avatar
import Math

#def smsnum( player, string ):
#	"Set the SMS number for the player."
#
#	print "Number '" + string + "'"
#	player.cell.setPhoneNumber( string )

#def sms( player, string ):
#	"Send an SMS to the targetted player. If no player is targetted, send to self."
#	if BigWorld.target():
#		BigWorld.target().cell.sendSMS(
#			player.playerName + ": " + string )
#	else:
#		player.cell.sendSMS( string )
#	print "Sending '" + string + "'"

#def group( player, string ):
#	"Send a chat message to all group members."
#
#	# TODO: Prepending the player name is a bit of a hack.
#	player.base.groupChat( string )
#	FantasyDemo.addChatMsg( -1, "Group - you say: " + string )

#def gls( player, string ):
#	"List the players in your current group."
#	player.base.groupList()

#def fls( player, string ):
#	"List your current friends."
#	player.base.friendsList()

#def local( player, string ):
#	"Send a local chat message (e.g. all players at the table)"

#	if player.mode == Avatar.Avatar.MODE_SEATED:
#		# TODO: Why is modeTarget stored as an int?
#		BigWorld.entity(player.modeTarget).cell.tableChat( string )
#		FantasyDemo.addChatMsg( player.id, "[local] " + string )
#	else:
#		# TODO: This may mean a short range chat when not seated?
#		print "Should be seated for local chat."

#def tell( player, string ):
#	"Send a chat message to a named individual."

#	try:
#		dstName, msg = string.split( ' ', 1 )
#		player.base.tell( dstName, msg )
#		FantasyDemo.addChatMsg( player.id, "[To " + dstName + "] " + msg )
#	except:
#		print "Bad tell statement. '/tell {playerName} {msg}'"


def who( player, string ):
	"List all online players near you."
	playerList = "Players near you:\n"
	for i in BigWorld.entities.values():
		if i.__class__.__name__ == "Avatar":
			playerList = playerList + i.playerName + "\n"
	FantasyDemo.addChatMsg( -1, playerList )


def help( player, string ):
	"Display help a console command."
	if string:
		try:
			func = globals()[ string ]
			if callable( func ) and func.__doc__:
				FantasyDemo.addChatMsg( -1, func.__doc__ )
			else:
				raise "Not callable"
		except:
			FantasyDemo.addChatMsg( -1, "No help for " + string )
	else:
		isCallable = lambda x : callable( globals()[x] )

		keys = filter( isCallable, globals().keys() )
		keys.sort()

		FantasyDemo.addChatMsg( -1, "/help {command} for more info." )

		rows = 3
		rowLength = (len(keys) - 1)/rows + 1

		stripper = lambda c : not c in "[]'\""

		for i in range(rows):
			string = str( keys[i * rowLength: (i+1)*rowLength] )
			FantasyDemo.addChatMsg( -1, filter( stripper, string ) )


def target( player, string ):
	"Send a chat message to the targeted player"
	t = BigWorld.target()

	if t:
		try:
			t.cell.directedChat( player.id, string )
			FantasyDemo.addChatMsg( player.id, "[To " + t.playerName + "] " + string )
		except:
			pass


def pushUp( player, string ):
	"This is the same as pressing the pushUp key."
	player.pushUpKey()


def pullUp( player, string ):
	"This is the same as pressing the pullUp key."
	player.pullUpKey()


def follow( player, string ):
	"Follow the current target"
	if BigWorld.target() != None:
		player.physics.chase( BigWorld.target(), 2.0, 0.5 )
		player.physics.velocity = ( 0, 0, 6.0 )


def summon( player, string ):
	"Summon an instance of the specified entity type on the server at the "
	"present location of the connected/proxi entity"
	assert isinstance( BigWorld.connectedEntity(), Avatar.Avatar )
	BigWorld.connectedEntity().cell.summonEntity( string )


def weather( player, string ):
	import WeatherSystem
	WeatherSystem.newWeather().toggleRandomWeather( False )
	WeatherSystem.newWeather().summon( string )


def rain( player, string ):
	"Set the rain amount, from 0 to 1"
	import WeatherSystem
	WeatherSystem.newWeather().rain( float(string) )


def getV4FromString( string ):
	tokens = string.split(" ")
	v = [1,1,1,1]
	for i in tokens:
		try:
			v.append( float(i) )
		except:
			pass
	return Math.Vector4(v[-4:])


def fog( player, string ):
	"Set the fog colour and density, from 1 (normal) to 10 (very dense)"
	import WeatherSystem
	WeatherSystem.newWeather().fog( getV4FromString(string) )


def ambient( player, string ):
	"Set the ambient colour"
	import WeatherSystem
	WeatherSystem.newWeather().ambient( getV4FromString(string) )


def sunlight( player, string ):
	"Set the sunlight colour"
	import WeatherSystem
	WeatherSystem.newWeather().sun( getV4FromString(string) )



# ------------------------------------------------------------------------------
# Section: Gestures
# ------------------------------------------------------------------------------

def wave( player, string ):
	"Makes the player wave."
	player.playGesture( 1 )

def laugh( player, string ):
	"Makes the player laugh."
	player.playGesture( 16 )

def cry( player, string ):
	"Makes the player cry."
	player.playGesture( 3 )

def point( player, string ):
	"Makes the player point."
	player.playGesture( 24 )

def shrug( player, string ):
	"Makes the player shrug."
	player.playGesture( 4 )

def yes( player, string ):
	"Makes player's head shake."
	player.playGesture( 19 )

def no( player, string ):
	"Makes player's head shake."
	player.playGesture( 20 )

def beckon( player, string ):
	"Makes the player beckon."
	player.playGesture( 21 )

def fat( player, string ):
	"Makes the player fat."
	player.playGesture( 44 )

def skinny( player, string ):
	"Makes the player skinny."
	player.playGesture( 45 )

# ------------------------------------------------------------------------------
# Section: Friends List
# ------------------------------------------------------------------------------

def addFriend( player, string ):
	"Adds a friend to player's friends list."
	player.addFriend( string )

def delFriend( player, string ):
	"Deletes a friend from player's friends list."
	player.delFriend( string )

def infoFriend( player, string ):
	"Gets information about a friend."
	player.infoFriend( string )

def listFriends( player, string ):
	"Lists your friends (and their online status)."
	player.listFriends()

def msgFriend( player, string ):
	"Sends a message to a friend. e.g. /msgFriend john : hello!"
	words = string.split( ':', 1 )
	name = words[0].strip()
	if len(words) > 1:
		message = words[1].lstrip()
	else:
		message = ""

	player.msgFriend( name, message )

# ------------------------------------------------------------------------------
# Section: Features
# ------------------------------------------------------------------------------

def killstorm( player, string ):
	"Clears storm."

#	BigWorld.weather( BigWorld.player().spaceID ).windAverage( 20, 20 )
#	BigWorld.weather( BigWorld.player().spaceID ).windGustiness( 20 )
	BigWorld.weather( BigWorld.player().spaceID ).system( "CLEAR" ).direct( 1, ( 0, 0, 0, 0 ), 1 )
	BigWorld.weather( BigWorld.player().spaceID ).system( "CLOUD" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
	BigWorld.weather( BigWorld.player().spaceID ).system( "RAIN" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
	BigWorld.weather( BigWorld.player().spaceID ).system( "STORM" ).direct( 0, ( 0, 0, 0, 0 ), 1 )

#def cloud( player, string ):
#	"Changes cloud cover, 1000m upwind from the player."

#	BigWorld.weather( BigWorld.player().spaceID ).windAverage( 20, 20 )
#	BigWorld.weather( BigWorld.player().spaceID ).windGustiness( 20 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "CLEAR" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "CLOUD" ).direct( 1, ( .5, 5, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "RAIN" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "STORM" ).direct( 0, ( 0, 0, 0, 0 ), 1 )

def storm( player, string ):
	"Creates a storm, 1000m upwind from the player."

#	BigWorld.weather( BigWorld.player().spaceID ).windAverage( 20, 20 )
#	BigWorld.weather( BigWorld.player().spaceID ).windGustiness( 20 )
	BigWorld.weather( BigWorld.player().spaceID ).system( "CLEAR" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
	BigWorld.weather( BigWorld.player().spaceID ).system( "CLOUD" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
	BigWorld.weather( BigWorld.player().spaceID ).system( "RAIN" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
	BigWorld.weather( BigWorld.player().spaceID ).system( "STORM" ).direct( 1, ( 0, 0, 0, 0 ), 1 )

#def rain( player, string ):
#	"Starts rain, 1000m upwind from the player."

#	BigWorld.weather( BigWorld.player().spaceID ).windAverage( 20, 20 )
#	BigWorld.weather( BigWorld.player().spaceID ).windGustiness( 20 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "CLEAR" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "CLOUD" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "RAIN" ).direct( 1, ( .5, 5, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "STORM" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).temperature( 28, 0 )

#def hail( player, string ):
#	"Starts hail, 1000m upwind from the player."

#	BigWorld.weather( BigWorld.player().spaceID ).windAverage( 20, 20 )
#	BigWorld.weather( BigWorld.player().spaceID ).windGustiness( 20 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "CLEAR" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "CLOUD" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "RAIN" ).direct( 1, ( .5, 5, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "STORM" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).temperature( 3, 0 )

#def snow( player, string ):
#	"Starts snow, 1000m upwind from the player."

#	BigWorld.weather( BigWorld.player().spaceID ).windAverage( 20, 20 )
#	BigWorld.weather( BigWorld.player().spaceID ).windGustiness( 20 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "CLEAR" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "CLOUD" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "RAIN" ).direct( 1, ( .5, 5, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).system( "STORM" ).direct( 0, ( 0, 0, 0, 0 ), 1 )
#	BigWorld.weather( BigWorld.player().spaceID ).temperature( -50, 0 )

def teleport( player, dst ):
	BigWorld.player().tryToTeleport( dst )

# ------------------------------------------------------------------------------
# Section: Aliases
# ------------------------------------------------------------------------------

# The following are aliases for commands.
#l = local
#g = group
#t = tell
