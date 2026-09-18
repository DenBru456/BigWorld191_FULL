# -*- coding: utf-8 -*-

import BigWorld
import Helpers.PyGUI as PyGUI
from functools import partial
from bwdebug import ERROR_MSG
import types
import Cursor

from Helpers.PyGUI import PyGUIEvent
from FDToolTip import ToolTipInfo


class WeatherWindow( PyGUI.DraggableWindow ):

	factoryString = "FDGUI.WeatherWindow"

	def __init__( self, component ):
		PyGUI.DraggableWindow.__init__( self, component )
		self.component.script = self
		self.timeCallback = None
		self.origTimeOfDay = "160" # The default in the C++ code
		self.weatherName = "Clear"
		self.weatherSystem = None
		self.weatherSystemName = None
		self.lastWindSpeed = 0.0
		self.lastTemperature = 25


	def onActive( self ):
		self.onTimeOfDayUpdated()
		self.timeCallback = BigWorld.callback( 0.1 if self._isTimeAccelerated() else 1.0, self.timeOfDayCallback )

		if self.weatherSystem == None and self.weatherSystemName == None:
			import WeatherSystem
			weather = WeatherSystem.newWeather()
			if weather.pendingWeatherChange:
				self.weatherSystemName = weather.pendingWeatherChange
			elif weather.system:
				self.weatherSystem = weather.system
			else:
				self.weatherSystemName = 'Clear'

		self._onWeatherUpdated()


	def avatarFini( self, avatar ):
		if self.timeCallback:
			BigWorld.cancelCallback( self.timeCallback )
			self.timeCallback = None


	def timeOfDayCallback( self ):
		if self.isActive:
			self.onTimeOfDayUpdated()
			self.timeCallback = BigWorld.callback( 0.1 if self._isTimeAccelerated() else 1.0, self.timeOfDayCallback )


	def _newWeather( self, system = None, systemName = None ):
		self.weatherSystem = system
		self.weatherSystemName = systemName
		self.lastWindSpeed = None
		self.lastTemperature = None
		self._onWeatherUpdated()


	@PyGUIEvent( "closeBox", "onClick" )
	def onCloseBoxClick( self ):
		self.active( False )


	def onTimeOfDayUpdated( self ):
		timeOfDayString = BigWorld.timeOfDay()
		if ':' not in timeOfDayString:
			# Error message has been suppressed for Austin. Restore it post-conference
			# so we know what's going on here.
			#ERROR_MSG( "BigWorld.timeOfDay() returned invalid string '%s'" % (timeOfDayString,) )
			return

		self.component.timeOfDay.text = timeOfDayString
		hours, minutes = timeOfDayString.split(':')
		self.component.timeOfDaySlider.script.value = int(hours) + int(minutes) / 60.0

		self.component.accelerateTimeCheckBox.script.setToggleState( self._isTimeAccelerated() )


	def _isTimeAccelerated( self ):
		if BigWorld.server() is not None:
			secsPerHour = int( BigWorld.getWatcher( "Client Settings/Secs Per Hour" ) )
			return secsPerHour < 50.0
		return False


	@PyGUIEvent( "timeOfDaySlider", "onValueChanged" )
	def onTimeOfDaySlider( self ):
		BigWorld.timeOfDay( str( self.component.timeOfDaySlider.script.value ) )
		self.component.timeOfDay.text = BigWorld.timeOfDay()


	@PyGUIEvent( "accelerateTimeCheckBox", "onActivate", True )
	@PyGUIEvent( "accelerateTimeCheckBox", "onDeactivate", False )
	def onAccelerateTimeCheckBox( self, on ):
		if on:
			self.origTimeOfDay = BigWorld.getWatcher( "Client Settings/Secs Per Hour" )
			BigWorld.setWatcher( "Client Settings/Secs Per Hour", 1.0 )
			BigWorld.cancelCallback( self.timeCallback )
			self.timeOfDayCallback()
		else:
			BigWorld.setWatcher( "Client Settings/Secs Per Hour", self.origTimeOfDay )
			#BigWorld.setWatcher( "Client Settings/Time of Day", 15.0 )
		self.onTimeOfDayUpdated()


	def _onWeatherUpdated( self ):
		import WeatherSystem
		weather = WeatherSystem.newWeather()
		windSpeed = self.lastWindSpeed
		temperature = self.lastTemperature

		if self.weatherSystemName:
			weatherName = self.weatherSystemName
			system = weather.newSystemByName( weatherName )
		elif self.weatherSystem:
			system = self.weatherSystem
			weatherName = system.name

		if system:
			if windSpeed == None:
				windSpeed = system.windSpeed[0] + system.windSpeed[1]
			if temperature == None:
				temperature = system.temperature

		self.component.weatherName.text = weatherName
		if self.weatherButtons.has_key( weatherName ):
			self.weatherButtons[ weatherName ].script.setToggleState( True )
		else:
			button = self.weatherButtons.values()[0].script
			button.setToggleState( True )
			button.setToggleState( False )

		self.component.windSpeedSlider.script.value = windSpeed
		self.component.windSpeed.text = "%.1f m/s" % (windSpeed,)
		self.component.temperatureSlider.script.value = temperature
		self.component.temperature.text = u"%d °C" % (temperature,)

		self.component.randomWeatherCheckBox.script.setToggleState( weather.isWeatherRandom() )


	@PyGUIEvent( "weatherGrid.clearWeatherButton", "onClick", "Clear" )
	@PyGUIEvent( "weatherGrid.cloudyWeatherButton", "onClick", "Cloudy" )
	@PyGUIEvent( "weatherGrid.cloudy2WeatherButton", "onClick", "Cloudy2" )
	@PyGUIEvent( "weatherGrid.cloudy3WeatherButton", "onClick", "Cloudy3" )
	@PyGUIEvent( "weatherGrid.stormyWeatherButton", "onClick", "Stormy" )
	@PyGUIEvent( "weatherGrid.rainyWeatherButton", "onClick", "Rainy" )
	@PyGUIEvent( "weatherGrid.hailWeatherButton", "onClick", "Hail" )
	@PyGUIEvent( "weatherGrid.dustStormWeatherButton", "onClick", "DustStorm" )
	@PyGUIEvent( "weatherGrid.snowWeatherButton", "onClick", "Snow" )
	@PyGUIEvent( "weatherGrid.blizzardWeatherButton", "onClick", "Blizzard" )
	@PyGUIEvent( "weatherGrid.fogWeatherButton", "onClick", "Fog" )
	@PyGUIEvent( "weatherGrid.peaSoupWeatherButton", "onClick", "PeaSoup" )
	def onWeatherButtonClick( self, weather ):
		import WeatherSystem
		WeatherSystem.newWeather().toggleRandomWeather( False )
		WeatherSystem.newWeather().summon( weather )
		self.component.weatherName.text = weather
		self.weatherName = weather
		self.lastWindSpeed = None
		self.lastTemperature = None


	@PyGUIEvent( "windSpeedSlider", "onValueChanged" )
	def onWindSpeedSlider( self ):
		self.lastWindSpeed = self.component.windSpeedSlider.script.value
		BigWorld.weather( BigWorld.player().spaceID ).windAverage( self.lastWindSpeed, 0.0 )
		self.component.windSpeed.text = "%.1f m/s" % (self.lastWindSpeed,)


	@PyGUIEvent( "temperatureSlider", "onValueChanged" )
	def onTemperatureSlider( self ):
		self.lastTemperature = self.component.temperatureSlider.script.value
		BigWorld.weather( BigWorld.player().spaceID ).temperature( self.lastTemperature, 0 )
		self.component.temperature.text = u"%d °C" % (self.lastTemperature,)


	@PyGUIEvent( "randomWeatherCheckBox", "onActivate", True )
	@PyGUIEvent( "randomWeatherCheckBox", "onDeactivate", False )
	def onRandomWeatherCheckBox( self, on ):
		import WeatherSystem
		WeatherSystem.newWeather().toggleRandomWeather( on )


	def active( self, show ):
		if self.isActive == show:
			return

		import WeatherSystem
		if show:
			WeatherSystem.newWeather().addListener( "newWeather", self._newWeather )
		else:
			WeatherSystem.newWeather().removeListener( "newWeather", self._newWeather )
			self.weatherSystem = None
			self.weatherSystemName = None

		PyGUI.DraggableWindow.active( self, show )
		Cursor.showCursor( show )

		if show:
			self.onActive()


	def onBound( self ):
		PyGUI.DraggableWindow.onBound( self )

		weatherGrid = self.component.weatherGrid
		self.weatherButtons = {
			'Clear': weatherGrid.clearWeatherButton,
			'Cloudy': weatherGrid.cloudyWeatherButton,
			'Cloudy2': weatherGrid.cloudy2WeatherButton,
			'Cloudy3': weatherGrid.cloudy3WeatherButton,
			'Stormy': weatherGrid.stormyWeatherButton,
			'Rainy': weatherGrid.rainyWeatherButton,
			'Hail': weatherGrid.hailWeatherButton,
			'DustStorm': weatherGrid.dustStormWeatherButton,
			'Snow': weatherGrid.snowWeatherButton,
			'Blizzard': weatherGrid.blizzardWeatherButton,
			'Fog': weatherGrid.fogWeatherButton,
			'PeaSoup': weatherGrid.peaSoupWeatherButton,
		}

		for key, value in self.weatherButtons.iteritems():
			toolTipInfo = ToolTipInfo( value, "tooltip1line", {'text':key, 'shortcut':''}  )
			value.script.setToolTipInfo( toolTipInfo )

