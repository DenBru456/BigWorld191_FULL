# Name: Kill storms
# Desc: Destroys all storm/rain entities
# Target: baseapps

#Kill Wind
import WeatherSystem
count = 0
for e in BigWorld.entities.values():
	if e.__class__ == WeatherSystem.WeatherSystem :
		e.cell.kill( ["STORM", "RAIN"] )
		count += 1
print "Killed %d storms" % (count)
