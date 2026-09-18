# Name: Bots to Beziel (?)
# Desc: Converts Bots to Beziels?
# Target: cellapps

#Bots to Beziel
count = 0
for entity in BigWorld.entities.values():
	if entity.isReal() and entity.id > 1000 and entity.id < 100000:
		entity.playerName = "Bot"
		entity.modelNumber = 4
		entity.rightHand = -1
		count += 1
print "%d entities converted" % (count)
