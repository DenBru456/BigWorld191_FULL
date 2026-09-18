# Name: Create many Striffs
# Desc: Creates a lot of striffs over the 10k area
# Target: cellapp

#Many Striffs

import random
import Creature
import BigWorld

XRANGE = (-5000, 5000)
ZRANGE = (-5000, 5000)
CLUSTER_SIZE = 20
COUNT = 25

dict = {}
dict["creatureType"] = 1

for i in range(COUNT):
	x = random.randrange(XRANGE[0], XRANGE[1])
	z = random.randrange(ZRANGE[0], ZRANGE[1])

	dict["xorigin"] = x
	dict["zorigin"] = z
	dict["health"] = 30
	dict["maxHealth"] = 30

	for s in range(CLUSTER_SIZE):
		sx = random.randrange(CLUSTER_SIZE)
		sy = random.randrange(CLUSTER_SIZE)
		pos = (x, 0, z)
		# createEntity( class, spaceID, position, direction, state )
		e = BigWorld.createEntity("Creature", 1, pos, (0,0,0), dict)

print "Created %d entities" % (CLUSTER_SIZE * COUNT)
