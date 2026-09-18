# Name: Bots to Orcs(?)
# Desc: Converts Bots to Orcs?
# Target: cellapps

#Bots to Orcs
count = 0
for entity in BigWorld.entities.values():
	if entity.isReal() and entity.id > 1000 and entity.id < 100000:
		entity.playerName = "Orc"
		entity.modelNumber = 192
		entity.rightHand = 7
		count += 1

print "%d entities converted" % (count)
