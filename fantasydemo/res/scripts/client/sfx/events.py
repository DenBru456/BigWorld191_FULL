import BigWorld
import math
from sfx import s_sectionProcessors
from sfx import typeCheck
from Pixie import MetaParticleSystem
from bwdebug import *
import random
import traceback
from functools import partial
from Math import Vector3
from Math import Vector4LFO
from Math import Vector4Shader
from Math import Vector4
from Math import Vector4Animation
from Helpers.V4ShaderConsts import _mul
from Helpers.V4ShaderConsts import _add
from Helpers.V4ShaderConsts import _r0
from Helpers.V4ShaderConsts import _r1

# ------------------------------------------------------------------------------
# Event Timings
# ------------------------------------------------------------------------------
IMMEDIATE_EVENT				= 0
TRANSFORM_DEPENDENT_EVENT	= 1
DURATION_DEPENDENT_EVENT	= 2

# ------------------------------------------------------------------------------
# Particle System Action IDs.
# ------------------------------------------------------------------------------
SOURCE_PSA			=  1
SINK_PSA			=  2
BARRIER_PSA			=  3
FORCE_PSA			=  4
STREAM_PSA			=  5
JITTER_PSA			=  6
SCALER_PSA			=  7
TINT_SHADER_PSA		=  8
NODE_CLAMP_PSA		=  9
ORBITOR_PSA			= 10
FLARE_PSA			= 11
COLLIDE_PSA			= 12
MATRIX_SWARM_PSA	= 13
MAGNET_PSA			= 14
SPLAT_PSA			= 15

#------------------------------------------------------------------------------
#	Interface sfx.Event
#------------------------------------------------------------------------------
class Event:
	def __init__( self ):
		pass

	def load( self, pSection, prereqs = None ):
		return self

	#Start the event playing.  The event should return a time
	#suggesting how long it will take to stop the sfx.
	def go( self, sfx, actor, source, target, **kargs ):
		return 0.0

	#Stops the event playing.  The event should return a time
	#suggesting how long it will take to stop the sfx.
	def stop( self, actor, source, target ):
		return 0.0

	def duration( self, actor, source, target ):
		return 0.0

	#This method tells the SFX system whether or not this
	#event is dependent on the particle system having the
	#correct location, or knowledge of total duration, or
	#if it should just be played straight away.
	#
	#e.g. if set to 0, the event plays the same frame as attach
	#	  if set to 1, the event plays the frame after attach.
	#	  if set to 2, the event plays once the duration is known
	def eventTiming( self ):
		return IMMEDIATE_EVENT


#------------------------------------------------------------------------------
#	RandomDelayEvent - this event wraps any other event, and delays for a
#	random time before spawning the event.
#------------------------------------------------------------------------------
class RandomDelayEvent( Event ):
	def __init__( self ):
		Event.__init__( self )
		self.events = []
		self.minDelay = 0.0
		self.maxDelay = 1.0
		self.nextDelay = 1.0

	def load( self, pSection, prereqs = None ):
		for (name,section) in pSection.items():
			eventSection = pSection.items()[0][1]
			result = None
			if not name in ["MinDelay","MaxDelay"]:
				if s_sectionProcessors.has_key( name ):
					result = s_sectionProcessors[name]().load(section)
				else:
					ERROR_MSG( "No section processor matches the tag ", name, section.asString )
				if result:
					self.events.append( result )

		self.minDelay = pSection.readFloat( "MinDelay", self.minDelay )
		self.maxDelay = pSection.readFloat( "MaxDelay", self.maxDelay )
		if ( self.minDelay > self.maxDelay ):
			ERROR_MSG( "Min Delay was greater than Max Delay", self, pSection.asString )
			self.minDelay = 0.0
		self.nextDelay = self.getNextDelay()
		return self

	def getNextDelay( self ):
		return random.random() * (self.maxDelay-self.minDelay) + self.minDelay

	def go( self, sfx, actor, source, target, **kargs ):
		duration = 0.0
		if len( self.events ) > 0:
			BigWorld.callback( self.nextDelay, lambda:self.spawnEvents( sfx, actor, source, target ) )
			return self.duration( actor, source, target )
		return self.nextDelay

	def spawnEvents( self, sfx, actor, source, target ):
		for i in self.events:
			i.go( sfx, actor, source, target )
		self.nextDelay = self.getNextDelay()

	def duration( self, actor, source, target ):
		total = self.nextDelay

		for i in self.events:
			eventDuration = i.duration( actor, source, target )
			if eventDuration >= 0.0:
				total += eventDuration

		return total

s_sectionProcessors[ "RandomDelayEvent" ] = RandomDelayEvent


#------------------------------------------------------------------------------
#	PlaySound - plays an fxSound with the given name.
#------------------------------------------------------------------------------
class PlaySound( Event ):
	def __init__( self ):
		Event.__init__( self )
		self.tag = None
		self.attachToActor = False

	def load( self, pSection, prereqs = None ):
		self.tag = pSection.asString
		if self.tag == "":
			WARNING_MSG( "PlaySound had no associated tag" )
		self.attachToActor = pSection.has_key( "attachToActor" )
		return self

	def go( self, sfx, actor, source, target, **kargs ):

		# All the calls to playSound() are commented out here because
		# FantasyDemo is missing the majority of referenced sound events.

		# NOTE: We don't really need all this duration stuff.  PyModels have the
		# stopSoundsOnDestroy attribute which can be used to allow sounds to
		# continue playing after the model has been destroyed, which is a much
		# simpler and more efficient way to handle this problem.

		sound = None

		if self.tag != "":
			if kargs.has_key("suffix"):
				tag = self.tag + kargs[ 'suffix' ]
			else:
				tag = self.tag

			if self.attachToActor:
				try:
					pass # sound = actor.playSound( tag )
				except:
					ERROR_MSG( "error playing sound on actor", self, actor, source, tag )
					traceback.print_exc()
					traceback.print_stack()
			else:
				try:
					pass # sound = source.model.playSound(tag)
				except:
					try:
						pass # sound = source.playSound(tag)
					except:
						ERROR_MSG( "error playing sound", self, actor, source, tag )
						traceback.print_exc()
						traceback.print_stack()

		# return duration to allow sounds to play to their natural conclusion.
		# (otherwise if the rest of the sfx finished before the sound it would be truncated)
		#DEBUG_MSG("duration=", duration)
		return sound.duration if sound else 0.0


	def eventTiming( self ):
		return TRANSFORM_DEPENDENT_EVENT

s_sectionProcessors[ "PlaySound" ] = PlaySound



#------------------------------------------------------------------------------
#	ForceParticle - this class simply calls force(1)
#
#	Optional Parameter - "NumberToForce"
#------------------------------------------------------------------------------
class ForceParticle( Event ):
	def __call__( self ):
		return self

	def go( self, sfx, actor, source, target, **kargs ):
		#typeCheck( actor, [Pixie.MetaParticleSystem,Pixie.ParticleSystem] )

		try:
			amount = kargs["NumberToForce"]
		except:
			amount = 1

		try:
			actor.force(amount)
			#add 0.001 to fully allow forced particles to die out.
			return actor.duration() + 0.001
		except:
			ERROR_MSG( "actor is not a particle system!", actor )
			return 0.0

	def duration( self, actor, source, target ):
		try:
			return actor.duration() + 0.001
		except:
			return 0.0

	#We must signal the SFX system that it needs to wait until
	#the transform is fixed up before forcing particles out.
	def eventTiming( self ):
		return TRANSFORM_DEPENDENT_EVENT

s_forceParticle = ForceParticle()
s_sectionProcessors[ "ForceParticle" ] = s_forceParticle
s_sectionProcessors[ "Force" ] = s_forceParticle


#------------------------------------------------------------------------------
#	ParticleSubSystemEvent - This base class exists to provide a foundation
#	for all events that deal with selected subSystems of a MetaParticleSystem.
#------------------------------------------------------------------------------
class ParticleSubSystemEvent( Event ):
	def __init__( self ):
		Event.__init__( self )
		self.subSystems = []

	def load( self, pSection, prereqs = None ):
		self.subSystems = pSection.readStrings( "systemName" )
		return self

	def duration( self, actor, source, target ):
		return 0.0

	def isInteresting( self, subSystem ):
		return 1

	def populateSubSystemList( self, actor ):
		if type(actor) == MetaParticleSystem:
			if len(self.subSystems) == 0:
				self.subSystems = []
				for i in xrange(0,actor.nSystems()):
					sys = actor.system(i)
					if self.isInteresting( sys ):
						#note - append the index of the sub-system
						self.subSystems.append(i)

	def subSystemIterate( self, actor, source, target, callbackFn ):
		if type(actor) == MetaParticleSystem:
			if len(self.subSystems) == 0:
				self.populateSubSystemList(actor)

			for i in self.subSystems:
				sys = actor.system(i)
				#print "subSystemIterate - checking", sys
				callbackFn( actor, source, target, sys )
		else:
			try:
				callbackFn( actor, source, target, actor )
			except:
				ERROR_MSG( "actor is not a particle system!", actor )



#------------------------------------------------------------------------------
#	SwarmTargets - this sets up a list of target nodes.
#
#	Optional Parameters - "TargetNodes"
#------------------------------------------------------------------------------
class SwarmTargets( ParticleSubSystemEvent ):
	def __init__( self ):
		Event.__init__( self )
		self.nodeList = []

	def load( self, pSection, prereqs = None ):
		self.nodeList = pSection.readStrings( "Node" )
		return ParticleSubSystemEvent.load( self, pSection )

	def isInteresting( self, subSystem ):
		act = None
		try:
			act = subSystem.action(MATRIX_SWARM_PSA)
			return True
		except ValueError:
			act = None
			
		return (act != None)

	def setTargets( self, actor, source, target, subSystem ):
		act = subSystem.action(MATRIX_SWARM_PSA)
		act.targets = self.targetNodes

	def go( self, sfx, actor, source, target, **kargs ):
		#typeCheck( actor, [Pixie.MetaParticleSystem,Pixie.ParticleSystem] )
		nodes = []

		#Add static target nodes from target model
		for i in self.nodeList:
			try:
				try:
					nodes.append( target.model.node(i) )
				except AttributeError:
					#Adding to a model not an entity
					nodes.append( target.node(i) )
			except ValueError:
				#Node does not exist, continue
				pass
			except TypeError:
				#Can't get nodes from blank models
				nodes.append( target.root )

		#Add dynamic target nodes, if available
		if kargs.has_key( "TargetNodes" ):
			nodes += kargs["TargetNodes"]

		self.targetNodes = nodes
		self.subSystemIterate( actor, source, target, self.setTargets )
		self.targetNodes = None

		return 0

	def duration( self, actor, source, target ):
		return 0.0

s_sectionProcessors[ "SwarmTargets" ] = SwarmTargets


#------------------------------------------------------------------------------
#	Motion Trigger - this class wraps common code
#	to correctly spawn a motion triggered pSystem.
#------------------------------------------------------------------------------
class CorrectMotionTriggeredParticle( ParticleSubSystemEvent ):
	def resetMotionTriggerFlag( self, actions ):
		for i in actions:
			i.motionTriggered = 1

	def isInteresting( self, subSystem ):
		act = subSystem.action(SOURCE_PSA)
		return (act and act.motionTriggered)

	def buildActionList( self, actor, source, target, subSystem ):
		act = subSystem.action(SOURCE_PSA)
		if act:
			self.actions.append(act)

	def go( self, sfx, actor, source, target, **kargs ):
		#typeCheck( actor, [MetaParticleSystem,Pixie.ParticleSystem] )
		self.actions = []
		self.subSystemIterate( actor, source, target, self.buildActionList )
		self.resetMotionTriggerFlag( self.actions )
		BigWorld.callback( 0.001, lambda:self.resetMotionTriggerFlag(self.actions) )
		return 0.0

s_sectionProcessors[ "CorrectMotionTriggeredParticle" ] = CorrectMotionTriggeredParticle


#------------------------------------------------------------------------------
#	This SFX event resets any time triggered particle sub-systems.
#
#	This is useful in a MetaParticleSystem that mixes forced particles
#	and time triggered particles, where the SFX time is dependent on
#	the forced particles.
#
#	This means the second time the SFX is used, the time-triggered particles
#	will begin "from the beginning"
#------------------------------------------------------------------------------
class ResetTimeTriggeredParticles( ParticleSubSystemEvent ):
	def isInteresting( self, subSystem ):
		act = subSystem.action(SOURCE_PSA)
		return (act and act.timeTriggered)

	def resetTimeTrigger( self, actor, source, target, subSystem ):
		subSystem.clear()
		act = subSystem.action(SOURCE_PSA)
		act.timeTriggered = 0
		act.timeTriggered = 1

	def go( self, sfx, actor, source, target, **kargs ):
		#typeCheck( actor, [MetaParticleSystem,Pixie.ParticleSystem] )
		self.subSystemIterate( actor, source, target, self.resetTimeTrigger )
		return 0.0

s_sectionProcessors[ "ResetTimeTriggeredParticles" ] = ResetTimeTriggeredParticles


#------------------------------------------------------------------------------
#	This SFX event plays time triggered particles for a specified time.
#
#	It uses the rate to fade in/out the particles.
#------------------------------------------------------------------------------
class RampTimeTriggeredParticles():
	def load( self, pSection, prereqs = None ):		
		self.duration = pSection.readFloat( "Duration", 0.0 )
		self.fadeTime = pSection.readFloat( "FadeTime", 2.0 )
		if (self.duration > 0.0 and self.fadeTime > self.duration):
			self.fadeTime = self.duration / 2.0
		return self
		
		
	def saveTimes( self, actor ):
		self.timeTriggeredSources = []
		for i in xrange(0,actor.nSystems()):			
			try:				
				source = actor.system(i).action(1)				
				if source.timeTriggered:					
					self.timeTriggeredSources.append((source, source.rate))					
			except:
				pass
				
				
	def restoreTimes( self, actor ):
		for (source,rate) in self.timeTriggeredSources:			
			source.rate = rate
				
				
	def setAll( self, actor, rate ):
		for (source,ignore) in self.timeTriggeredSources:			
			source.rate = rate


	#If duration > 0.0, sweet, we'll fade out automatically at the correct time
	#Otherwise (e.g. in the case of PersistentSFX use), call stop() when you want.
	def go( self, sfx, actor, source, target, **kargs ):
		if not hasattr(self, "timeTriggeredSources"):
			self.saveTimes(actor)
		
		actor.clear()
		self.setAll( actor, 0.0 )
		BigWorld.callback(0.0, partial(self.restoreTimes, actor) )
		if (self.duration > 0.0):			
			BigWorld.callback(self.duration - self.fadeTime, partial(self.stop, actor, source, target))
		
		return self.duration
		
		
	def stop( self, actor, source, target ):		
		self.setAll( actor, 0.0 )
		return self.fadeTime
		
		
	def duration( self ):
		return self.duration
		
		
	def eventTiming( self ):
		return IMMEDIATE_EVENT


s_sectionProcessors[ "RampTimeTriggeredParticles" ] = RampTimeTriggeredParticles


#------------------------------------------------------------------------------
#	This SFX event sets the orbitor point of OrbitorPSAs to the source.position
#
#	Required Parameters : "SetOrbitorPoint"
#------------------------------------------------------------------------------
class SetOrbitorPoint( ParticleSubSystemEvent ):
	def isInteresting( self, subSystem ):
		act = subSystem.action(ORBITOR_PSA)
		return ( act != None )

	def setOrbitorPoint( self, actor, source, target, subSystem ):
		try:
			act = subSystem.action(ORBITOR_PSA)
			act.point = source.position
		except:
			ERROR_MSG( "setOrbitorPoint has a problem with finding the position of the source object", source )

	def go( self, sfx, actor, source, target, **kargs ):
		#typeCheck( actor, [Pixie.MetaParticleSystem,Pixie.ParticleSystem] )
		self.subSystemIterate( actor, source, target, self.setOrbitorPoint )
		return 0.0

s_sectionProcessors[ "SetOrbitorPoint" ] = SetOrbitorPoint


#------------------------------------------------------------------------------
#	This SFX event sets a modulator onto the TintShader of sub systems.
#
#	Required Parameters : "SetColour"
#------------------------------------------------------------------------------
class SetColour( ParticleSubSystemEvent ):
	def isInteresting( self, subSystem ):
		act = subSystem.action(TINT_SHADER_PSA)
		return ( act != None )

	def setModulator( self, actor, source, target, subSystem ):
		act = subSystem.action(TINT_SHADER_PSA)
		act.modulator = self.colour

	def go( self, sfx, actor, source, target, **kargs ):
		#typeCheck( actor, [Pixie.MetaParticleSystem,Pixie.ParticleSystem] )
		try:
			self.colour = kargs["SetColour"]
			self.subSystemIterate( actor, source, target, self.setModulator )
		except:
			WARNING_MSG( "No colour was passed into the argument list", self, actor, source, target, kargs )
		return 0.0

s_sectionProcessors[ "SetColour" ] = SetColour


#------------------------------------------------------------------------------
#	This SFX event sets the basis for the particle systems(s)
#
#	Required Parameters : "Basis", a tuple of (dir,pos)
#------------------------------------------------------------------------------
class SetBasis( ParticleSubSystemEvent ):
	def setBasis( self, actor, source, target, subSystem ):
		subSystem.explicitPosition = self.worldPos
		subSystem.explicitDirection = self.worldDir

	def go( self, sfx, actor, source, target, **kargs ):
		#typeCheck( actor, [Pixie.MetaParticleSystem,Pixie.ParticleSystem] )
		try:
			(self.worldDir,self.worldPos) = kargs["Basis"]
			self.subSystemIterate( actor, source, target, self.setBasis )
			del self.worldDir
			del self.worldPos
		except:
			WARNING_MSG( "No basis was passed into the argument list", self, actor, source, target, kargs )
		return 0.0

s_sectionProcessors[ "SetBasis" ] = SetBasis


#------------------------------------------------------------------------------
#	This SFX event sets the basis for the PyModel
#
#	Required Parameters : "Basis", a tuple of (dir,pos)
#------------------------------------------------------------------------------
class AlignModel( ParticleSubSystemEvent ):
	def go( self, sfx, actor, source, target, **kargs ):
		#typeCheck( actor, [PyModel] )
		try:
			if kargs.has_key( "ModelAlignment" ):
				(dir,pos) = kargs["ModelAlignment"]
			elif kargs.has_key( "Basis" ):
				(dir,pos) = kargs["Basis"]

			actor.position = pos
			actor.yaw = math.atan2( dir.x, dir.z )
		except:
			WARNING_MSG( "No basis was passed into the argument list", self, actor, source, target, kargs )
		return 0.0

s_sectionProcessors[ "AlignModel" ] = AlignModel


#------------------------------------------------------------------------------
#	This SFX event clears all sub-systems.
#
#	This is useful in a forced particle environment, to reset any previous
#	forced particles.
#------------------------------------------------------------------------------
class ClearParticles( ParticleSubSystemEvent ):

	def clearSubSystem( self, actor, source, target, subSystem ):
		subSystem.clear()

	def go( self, sfx, actor, source, target, **kargs ):
		#typeCheck( actor, [MetaParticleSystem,Pixie.ParticleSystem] )
		self.subSystemIterate( actor, source, target, self.clearSubSystem )
		return 0.0

s_sectionProcessors[ "ClearParticles" ] = ClearParticles


#---------------------------------------------------
#	PlayAction - this class plays an action on a model
#---------------------------------------------------
class PlayAction:
	def __init__( self ):
		self.actions = []

	def load( self, pSection, prereqs = None ):
		self.actions = pSection.readStrings( "Action" )
		return self

	def go( self, sfx, actor, source, target, **kargs ):
		#typeCheck( actor, BigWorld.Model )
		dur = 0.0
		#try:
		curr = actor
		for i in self.actions:
			try:
				curr = getattr( curr, i )()
				dur += curr.duration
			except EnvironmentError:
				DEBUG_MSG( "ActionQueuer op() cannot queue actions when our Model is not in the world", i, actor, source, target )
		#except:
		#	ERROR_MSG( "Error playing action list on", actor, self.actions )
		#	return -1
		return dur

	def duration( self, actor, source, target ):
		dur = 0.0
		try:
			for i in self.actions:
				try:
					dur += actor.action(i).duration
				except:
					pass
			#DEBUG_MSG( "PlayAction duration %f" % (duration,) )
			return dur
		except:
			#DEBUG_MSG( "PlayAction duration excepetion" )
			return 0.0

	def eventTiming( self ):
		return TRANSFORM_DEPENDENT_EVENT

s_sectionProcessors[ "PlayAction" ] = PlayAction
s_sectionProcessors[ "PlayActions" ] = PlayAction

#------------------------------------------------------------------------------
#	AddDecal - adds a decal to a sfx
#
#	DecalInfo is an optional parameter of type (start point, end point), which
#	specifies a collision ray for choosing where the decal should appear.
#------------------------------------------------------------------------------
class AddDecal( Event ):
	def __init__( self ):
		Event.__init__( self )
		self.decalIndex = -1
		self.decalSize = 0.0
		self.decalExtent = (0,0,0)

	def load( self, pSection, prereqs = None ):
		try:
			self.decalIndex = BigWorld.decalTextureIndex( pSection.asString )
		except:
			#not supported on PC (yet)
			return

		if self.decalIndex != -1:
			self.decalSize = pSection.readFloat( "size", 1 )
			self.decalExtent = pSection.readVector3( "extent", (0,-1,0) )
		else:
			WARNING_MSG( "AddDecal had no associated tag" )
		return self

	def go( self, sfx, actor, source, target, **kargs ):
		#check if not supported, or did not load properly.
		if self.decalIndex == -1:
			return

		try:
			start = kargs["DecalInfo"][0]
			end = kargs["DecalInfo"][1]
		except KeyError:
			start = Vector3( source.position )
			for i in xrange(0,3): start[i] -= self.decalExtent[i] * 0.5
			end = start + self.decalExtent

		try:
			BigWorld.addDecal( start, end, self.decalSize, self.decalIndex )
		except:
			ERROR_MSG( "Could not add decal" )
		return 0.0

	def eventTiming( self ):
		return TRANSFORM_DEPENDENT_EVENT

s_sectionProcessors[ "AddDecal" ] = AddDecal



#------------------------------------------------------------------------------
#	Flicker - flicker the light's colour
#
#	Its basically a canned noise effect that you can scale with
#	- speed	( multiplier on standard speed of the standard effect )
#	- amplitude ( % darkening of the original colour )
#------------------------------------------------------------------------------
class Flicker:
	def __init__( self ):
		self.colour = None
		self.lightFlicker = None
		self.amplitude = 1.0
		self.speed = 1.0

	def load( self, pSection, prereqs = None ):
		self.amplitude = pSection.readFloat( "amplitude", self.amplitude )
		self.speed = pSection.readFloat( "speed", self.speed )
		return self

	def go( self, sfx, actor, source, target, **kargs ):
		self.colour = actor.colour
		
		lfo1 = Vector4LFO()
		lfo1.period = 0.4 / self.speed
		lfo1.amplitude = self.amplitude
		lfo2 = Vector4LFO()
		lfo2.period = 0.149 / self.speed
		
		scalarOffset = (1.0 - self.amplitude)
		offset = Vector4(scalarOffset, scalarOffset, scalarOffset, scalarOffset)
		
		self.lightFlicker = Vector4Shader()
		self.lightFlicker.addOp( _mul, _r1, lfo1, lfo2 )
		self.lightFlicker.addOp( _add, _r1, _r1, offset )
		self.lightFlicker.addOp( _mul, _r0, self.colour, _r1 )
		
		actor.shader = self.lightFlicker
		
		return 0.0
		

	def stop( self, actor, source, target ):
		actor.colour = self.colour
		actor.shader = None
		self.lightFlicker = None
		return 0.0

	def duration( self, actor, source, target ):
		return 0.0
		
	def eventTiming( self ):
		return IMMEDIATE_EVENT
		
s_sectionProcessors[ "Flicker" ] = Flicker



#------------------------------------------------------------------------------
#	Fade - fade the light's colour
#
#	Fade off the light over time, good for explosions of light
#
#	TODO : when Vector4 are serialisable, make a generic light Animation event.
#	TODO : allow the fade to be dependent on the duration of the reset of the
#	effect.
#------------------------------------------------------------------------------
class Fade:
	def __init__( self ):
		self.colour = None
		self.time = 1.0		

	def load( self, pSection, prereqs = None ):
		self.time = pSection.readFloat( "time", self.time )		
		return self

	def go( self, sfx, actor, source, target, **kargs ):
		#Only retrieve self.colour once, this is for
		#buffered SFX that are re-used; retrieving actor
		#.colour the next time will get (0,0,0,0), even
		#though we try to set the colour back in stop()
		if not self.colour:
			self.colour = actor.colour		
				
		self.lightFader = Vector4Animation()
		self.lightFader.duration = 100000.0
		self.lightFader.keyframes = [
			(0.0 * self.time, self.colour),
			(1.0 * self.time, (0,0,0,0) ) ]
		
		actor.shader = self.lightFader
		return self.time

	def stop( self, actor, source, target ):		
		actor.shader = None
		actor.colour = self.colour
		self.lightFader = None
		return 0.0

	def duration( self, actor, source, target ):
		return self.time
		
	def eventTiming( self ):
		return IMMEDIATE_EVENT
		
s_sectionProcessors[ "Fade" ] = Fade
