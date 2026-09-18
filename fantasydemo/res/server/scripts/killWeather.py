# Name: Kill weather
# Desc: Destroys all weather entities
# Target: cellapps

#Kill Weather
import WeatherSystem

for e in BigWorld.entities.values():
	if e.isReal() and e.__class__ == WeatherSystem.WeatherSystem:
		e.destroy()
print "Killed weather"
