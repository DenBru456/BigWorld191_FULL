import BigWorld
import random
import math

GRAVITY=0.001

def signedRand():
	return random.random() * 2.0 - 1.0

class Avatar( BigWorld.Entity ):
	velocity = (0,0)

	def __init__(self):
		BigWorld.Entity.__init__(self)

	def onTick(self,t):
		#print dir(self)
		# apply some acceleration
		if 1:
			acc = (-self.position[0]*GRAVITY + signedRand(),
				   -self.position[1]*GRAVITY + signedRand())
			self.velocity = (self.velocity[0]+0.01*acc[0], 
							 self.velocity[1]+0.01*acc[1])
			speed = math.sqrt(self.velocity[0]*self.velocity[0] + self.velocity[1]*self.velocity[1])
			if speed > 5:
				self.velocity = (5*self.velocity[0]/speed,5*self.velocity[1]/speed)
				speed = 5

			self.position = (self.position[0]+0.1*self.velocity[0], 
							 0,
							 self.position[2]+0.1*self.velocity[1])

			print BigWorld.entities.items()

		self.cell.chat("hello world")

	def onFinish(self):
		self.base.logOff()

