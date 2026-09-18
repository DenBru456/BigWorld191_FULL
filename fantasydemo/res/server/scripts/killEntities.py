#Kill Entities

for e in BigWorld.entities.values():
	if e.isReal() and e.id >= (1 << 24):
		e.destroy()
