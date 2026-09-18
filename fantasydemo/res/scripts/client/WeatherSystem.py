"""This module implements the WeatherSystem entity type."""


import BigWorld
import ResMgr
import sfx
import random
from functools import partial
import FantasyDemo
import traceback
from Helpers import Bloom
from Helpers.Listener import Listenable
from FDGUI import Minimap

weatherXML = ResMgr.openSection( "scripts/data/weather.xml" )

def average(list):
	return reduce(lambda a,b: a + b, list) / len(list)


class WeatherSystem(BigWorld.Entity):

	def __init__(self):
		BigWorld.Entity.__init__( self )


	def onEnterWorld( self, prereqs ):
		if not self.weatherMap.has_key(self.name):
			self.weatherMap[self.name] = [self]
		else:
			self.weatherMap[self.name].append(self)
		self.recalcWeather()
		Minimap.addEntity( self )


	def onLeaveWorld( self ):
		Minimap.delEntity( self )
		self.weatherMap[self.name].remove(self)
		self.recalcWeather()		


	def recalcWeather( self ):
		list = self.weatherMap[self.name]

		if self.name == "TEMPERATURE":
			if list == []:
				BigWorld.weather(self.spaceID).temperature(25, 1)
			else:
				temperature = average([item.arg0 for item in list])
				BigWorld.weather(self.spaceID).temperature(temperature, 1)
		elif self.name == "WIND":
			if list == []:
				BigWorld.weather(self.spaceID).windAverage(0, 0)
				BigWorld.weather(self.spaceID).windGustiness(0)
			else:
				avgx = average([item.arg0 for item in list])
				avgy = average([item.arg1 for item in list])
				gustiness = average([item.arg2 for item in list])
				BigWorld.weather(self.spaceID).windAverage(avgx, avgy)
				BigWorld.weather(self.spaceID).windGustiness(gustiness)
		else:
			if list == []:
				BigWorld.weather(self.spaceID).system(self.name).direct(0, (0,0,0,0), 1)
			else:
				propensity = average([item.propensity for item in list])
				arg0 = average([item.arg0 for item in list])
				arg1 = average([item.arg1 for item in list])
				BigWorld.weather(self.spaceID).system(self.name).direct( \
					propensity, (arg0, arg1, 0, 0), 1)


# The weatherMap is a global dictionary of all the weather systems
# in the client's AoI. It is keyed by weather type. For each weather
# type, there is a list of all the systems of that type. There is
# one default weatherSystem in the map, so that there will be clear
# weather if no other weatherSystems are spawned.

class WeatherSystemDummy:
	pass

defaultWeather = WeatherSystemDummy()
defaultWeather.name = "CLEAR"
defaultWeather.propensity = 1
defaultWeather.arg0 = 0
defaultWeather.arg1 = 0

WeatherSystem.weatherMap = { "CLEAR" : [defaultWeather] }

import Math


#
#	NewWeatherSystem binds together n skyboxes with a bunch of weather settings.
#
class NewWeatherSystem:
	def __init__( self, ds ):
		self.name = ds.name
		self.skyBoxes = ds.readStrings( "skyBox" )
		self.skyBoxModels = []
		self.rain = ds.readFloat( "rain", 0.0 )
		self.sun = ds.readVector4( "sun", (1,1,1,1) )
		self.ambient = ds.readVector4( "ambient", (1,1,1,1) )
		self.fog = ds.readVector4( "fog", (1,1,1,1) )
		self.temperature = ds.readFloat( "temperature", 25.0 )
		self.windSpeed = ds.readVector2( "windSpeed", (0.0,0.0) )
		self.windGustiness = ds.readFloat( "windGustiness", 0.0 )
		#Note : "skyBoxFogFactor" - how much does the changed colour / increased
		#density of the scene fogging affect the sky box cloud layers
		self.skyBoxFogFactor = ds.readFloat( "fogFactor", 0.15 )
		#inline bloom parameters
		self.bloom = ds["bloom"]
		self.bloomPreset = ds.readString("bloom", "Standard")
		self.fader = Math.Vector4Morph()
		self.fader.duration = 1.0
		f = self.fogAmount( self.fog[3] )
		self.fader.target = (f,0,0,0)
		self.sfx = None
		self.sfxName = ds.readString( "sfx" )
		self.loaded = False


	def addSkyBox( self, modelName ):
		self.skyBoxes.append( modelName )


	#Load sky boxes in the background thread.
	def loadSkyBoxes( self, callback = None, immediate = False ):
		if self.loaded:
			if callback:
				callback()
		else:
			if not immediate:
				BigWorld.loadResourceListBG( self.skyBoxes, partial(self.onLoadSkyBoxes,callback) )
			else:
				resourceRefs = {}
				for i in self.skyBoxes:
					resourceRefs[i] = BigWorld.Model(i)
				self.onLoadSkyBoxes( callback, resourceRefs )


	#Callback when sky boxes have loaded in the background thread.
	def onLoadSkyBoxes( self, callback, resourceRef ):
		self.loaded = True
		for [key,value] in resourceRef.items():
			model = value
			self.skyBoxModels.append( model )
		if callback != None:
			callback()


	#This detaches the sky box models and sfx and frees all references
	#to them thus unloading their textures and meshes etc.
	def unload( self ):
		for i in self.skyBoxModels:
			BigWorld.delSkyBox(i, self.fader)
		self.skyBoxModels = []
		if self.sfx != None:
			self.sfx.detach()
			self.sfx = None
		self.loaded = False


	def loadSFX( self, callback = None ):
		if self.sfxName != "":
			BigWorld.loadResourceListBG( sfx.prerequisites(self.sfxName), partial(self.onLoadSFX, callback) )
		else:
			if callback:
				callback()


	def onLoadSFX( self, callback, resourceRef ):
		if self.sfx != None:
			self.sfx.detach()
			self.sfx = None

		#Check self.loaded here - the weather system may have been told to go
		#away while the sfx was loading, in which case we ignore the callback.
		if self.loaded:
			self.sfx = sfx.PersistentSFX( self.sfxName, resourceRef )
			self.sfx.attach( BigWorld.player().model )
			self.sfx.go()
			if callback:
				callback()


	def fadeOutSFX( self ):
		if self.sfx != None:
			return self.sfx.stop()
		return 0.0


	#Fade in / out this weather system's sky boxes.  We load
	#our models/textures on demand when fading in, and free them
	#if we have fully faded out.
	#
	#If immediate is set to True, then the natural fade out speed
	#the sfx is clamped to the passed in fade time. If immediate
	#is False, the sfx will fade out at its own natural speed,
	#determined by the sfx itself to prevent popping.
	def fadeIn( self, fadingIn, fadeSpeed, immediate = False ):
		spaceID = BigWorld.player().spaceID
		curr = self.fader.value
		if fadingIn:
			if not self.loaded:
				print "calling fadeIn on a weather system that isn't loaded.  please call prepareResources() first", self.name
				traceback.print_stack()
				return
			for sb in self.skyBoxModels:
				BigWorld.addSkyBox( sb, self.fader )
			f = self.fogAmount(self.fog[3])
			self.fader.duration = fadeSpeed-0.1
			self.fader.target = (f,0,0,1)
			BigWorld.weather(spaceID).temperature(self.temperature, fadeSpeed)
			BigWorld.weather(spaceID).windAverage(self.windSpeed[0], self.windSpeed[1])
			BigWorld.weather(spaceID).windGustiness(self.windGustiness)
			if self.bloom:
				Bloom.loadStyle( self.bloom, fadeSpeed )
			else:
				Bloom.selectPreset( self.bloomPreset, fadeSpeed )
		else:
			if self.loaded:
				sfxFadeSpeed = self.fadeOutSFX()
				if not immediate:
					fadeSpeed = max(fadeSpeed, sfxFadeSpeed)
				BigWorld.callback( fadeSpeed, self.unload )
				self.fader.duration = fadeSpeed-0.1
				self.fader.target = (curr[0],curr[1],curr[2],0)


	def fogAmount( self, amount ):
		return (amount-1.0) * self.skyBoxFogFactor


	def prepareResources( self, callback = None, immediate = False ):
		if not self.loaded:
			self.loadSkyBoxes( partial(self.loadSFX,callback), immediate )
		else:
			if callback:
				callback()


	def setFadeSpeed( self, duration ):
		self.fader.duration = duration


#
#	NewWeather holds a bunch of NewWeatherSystems and implements smooth fading between them.
#
class NewWeather( Listenable ):

	def __init__( self ):
		Listenable.__init__( self )

		self.fadeSpeed = 15.0
		self.system = None
		self.randomWeatherCallback = None
		self.summoning = False
		self.pendingWeatherChange = None
		BigWorld.delStaticSkyBoxes()
		self.onChangeSpace()


	#This method chooses a random weather system every 60 seconds.
	def toggleRandomWeather( self, force = None ):
		if force != None:
			turningOff = not force
		else:
			turningOff = (self.randomWeatherCallback != None)

		if turningOff and self.randomWeatherCallback != None:
			BigWorld.cancelCallback( self.randomWeatherCallback )
			self.randomWeatherCallback = None
			FantasyDemo.addChatMsg( -1, 'Random weather turned off' )
		elif not turningOff:
			self.randomWeather( True )
			FantasyDemo.addChatMsg( -1, 'Random weather turned on' )


	# How to know if random weather has been turned on
	def isWeatherRandom( self ):
		return self.randomWeatherCallback != None


	#This method chooses the next or previous weather system
	#in the list.
	def nextWeatherSystem( self, direction, immediate = False ):
		systems = self.weatherSystemsForCurrentSpace()

		idx = 0
		if self.system != None:
			for s in systems:
				if s.name == self.system.name:
					break
				idx += 1

		if direction:
			idx += 1
		else:
			idx -= 1

		self.toggleRandomWeather(False)
		self.summon( systems[idx % len(systems)].name, immediate )


	def randomWeather( self, initial = False ):
		if initial or self.randomWeatherCallback != None:
			self.randomWeatherCallback = BigWorld.callback( 60.0, self.randomWeather )
			systems = self.weatherSystemsForCurrentSpace()
			ds = random.choice( systems )
			self.summon( ds.name )


	def setFadeSpeed( self, duration ):
		self.fadeSpeed = max( 0.1, duration )
		self.weatherController.duration = self.fadeSpeed
		self.sunlightController.duration = self.fadeSpeed
		self.ambientController.duration = self.fadeSpeed
		self.fogController.duration = self.fadeSpeed
		if self.system:
			self.system.setFadeSpeed( self.fadeSpeed )


	def weatherSystemsForCurrentSpace( self ):
		systems = []

		import FantasyDemo
		try:
			spaceName = FantasyDemo.rds.spaceNameMap[ BigWorld.player().spaceID ]
			for section in weatherXML.values():
				excludes = section.readStrings( "exclude" )
				if spaceName not in excludes:
					systems.append( section )
		except KeyError:
			print "Player in in unknown space with ID %d" % ( BigWorld.player().spaceID )
			return systems

		return systems


	def onChangeSpace( self ):
		m = Math.Vector4Morph()
		m.duration = self.fadeSpeed
		m.target = (0,0,0,0)
		m.time = m.duration
		BigWorld.weatherController(m)
		self.weatherController = m

		m = Math.Vector4Morph()
		m.duration = self.fadeSpeed
		m.target = (1,1,1,1)
		m.time = m.duration
		BigWorld.sunlightController(m)
		self.sunlightController = m

		m = Math.Vector4Morph()
		m.duration = self.fadeSpeed
		m.target = (1,1,1,1)
		m.time = m.duration
		BigWorld.ambientController(m)
		self.ambientController = m

		m = Math.Vector4Morph()
		m.duration = self.fadeSpeed
		m.target = (1,1,1,1)
		m.time = m.duration
		BigWorld.fogController(m)
		self.fogController = m

		BigWorld.delStaticSkyBoxes()


	def summon( self, systemName, immediate = False, serverSync = False ):
		# servSync is True if the change is the result of a server weather sync

		if self.system and self.system.name == systemName:
			return

		if immediate:
			self.setFadeSpeed( 2.5 )
		else:
			self.setFadeSpeed( 15.0 )

		if self.summoning and not immediate:
			self.pendingWeatherChange = systemName
			self.listeners.newWeather( systemName = systemName )
			return

		for ds in weatherXML.values():
			if ds.name == systemName:
				try:
					if not serverSync and BigWorld.getEnvironmentSync():
						p = BigWorld.player()
						p.cell.syncServWeather(p.spaceID, systemName)
				except KeyError:
					pass
				system = NewWeatherSystem(ds)
				self.summoning = True
				self.listeners.newWeather( system = system )
				system.prepareResources( partial(self.systemReadySummon, system, immediate), immediate )


	def systemReadySummon( self, system, immediate ):

		#FantasyDemo.addChatMsg( -1, 'Weather forecast : %s' % (system.name,) )

		if self.system:
			self.system.fadeIn( False, self.fadeSpeed, immediate )
			self.system = None

		if system != None:
			self.system = system
			self.system.fadeIn( True, self.fadeSpeed )
			self.skyBoxFogFactor = system.skyBoxFogFactor
			self.rain( system.rain )
			self.ambient( system.ambient )
			self.fog( system.fog, False )
			self.sun( system.sun )
			BigWorld.callback( self.fadeSpeed, self.onSystemSummoned )
		else:
			self.onSystemSummoned()


	def onSystemSummoned( self ):
		self.listeners.newWeather( system = self.system )

		self.summoning = False

		if self.pendingWeatherChange != None:
			self.summon( self.pendingWeatherChange )
			self.pendingWeatherChange = None


	def newSystemByName( self, systemName ):
		for ds in weatherXML.values():
			if ds.name == systemName:
				system = NewWeatherSystem(ds)
				return system

		return None


	#This method takes a Vector4Morph, keeps its current direction
	#and adds a new value[index] to the end.
	def animateValue( self, value, v4a, index ):
		expected = Math.Vector4( v4a.target )
		expected[index] = value
		v4a.target = expected


	#This method takes a Vector4Animation, keeps its current direction
	#and adds a new value.xyzw to the end.
	def animateVector4( self, v4a, value ):
		v4a.target = value


	#The rain is just a single value, modifying index 0 of the weather Controller
	def rain( self, amount ):
		self.animateValue( amount, self.weatherController, 0 )


	#The fog is a colour multiplier and density multiplier.
	def fog( self, value, applyToSystem = True ):
		self.animateVector4( self.fogController, value )
		if applyToSystem:
			fogAmount = value[3]
			self.animateValue( self.system.fogAmount(fogAmount), self.system.fader, 0 )


	#The sun is a simple colour multiplier.
	def sun( self, value ):
		self.animateVector4( self.sunlightController, value )


	#The ambient is a simple colour multiplier.
	def ambient( self, value ):
		self.animateVector4( self.ambientController, value )


s_newWeather = None
def newWeather():
	global s_newWeather
	if not s_newWeather:
		s_newWeather = NewWeather()
	return s_newWeather


#This method releases the new weather system, while not necessary for memory
#leak reasons (as when scripts are shutdown, this python object is also released)
#we want better control over when the weather system singleton is released.
def fini():
	s_newWeather = None

#WeatherSystem.py


