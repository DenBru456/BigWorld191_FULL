# single-cell-only

import whrandom
import BigWorld

def offset(radius):
	return whrandom.randrange(-radius/2, radius/2)

def addStriffSpawns(count, point, radius):
	for i in range(count):
		pos = (point[0] + offset(radius), point[1], point[2] + offset(radius))
		striff = BigWorld.createEntityFromFile("projects/server/striff/spawn.mfo", pos, (0,0,0))
	
# Striffs
addStriffSpawns(30, (0, 26, 100), 20)	

addStriffSpawns(30, (783, -100, -212), 20)

