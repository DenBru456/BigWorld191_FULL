import BigWorld
import ResMgr
from bwdebug import *
from Queue import Queue
import Math
from functools import partial
import traceback

s_sectionProcessors = {}

def typeCheck( self, listOrType ):
	return 1

def prerequisites( filename ):
	if filename == "":
		return ()
	fx = SFX( filename )
	fx.prerequisites()
	return tuple(fx.prereqs)
	
debugTimings = 0


#------------------------------------------------------------------------------
#	class EventTimer.
#
#	This is a simple timer that can be extended while it is going.
#	When all 
#------------------------------------------------------------------------------
class EventTimer:
	def __init__( self ):
		self.semaphore = 0
		self.callbackFn = None
		
	def going( self ):
		return ( self.semaphore != 0 )
		
	def reserve( self ):
		self.semaphore += 1
		
	def release( self ):
		self.semaphore -= 1
		
	def begin( self, duration, callbackFn ):
		self.callbackFn = callbackFn
		self.semaphore += 1
		BigWorld.callback( duration, self.end )
		
	def extend( self, duration ):
		self.semaphore += 1
		BigWorld.callback( duration, self.end )
		
	def end( self ):
		self.semaphore -= 1
		if self.semaphore == 0:
			if self.callbackFn:
				self.callbackFn()
				self.callbackFn = None
		

#------------------------------------------------------------------------------
#	SFX - Abstract base class for SFX resources.  It will load an SFX xml file,
#	and create actors, joints and events.
#
#	Actors are the things that act, for example particle systems and PyModels.
#	Joints glue the actors to the source model / entity
#	Events are those things that play
#------------------------------------------------------------------------------
class SFX:
	def __init__( self, fileName ):
		self.actors = {}
		self.joints = {}
		self.events = []		
		self.fileName = fileName		
			
			
	def prerequisites( self ):
		self.prereqs = set()
		
		pSection = ResMgr.openSection( self.fileName )
		if not pSection:
			ERROR_MSG( "Could not open file", self.fileName )
			return None
		else:
			self.prerequisitesFromSection( pSection )
			self.prereqs.add( self.fileName )
			
			
	def create( self, prereqs = None ):		
		try:
			pSection = prereqs[ self.fileName ]
		except KeyError:
			pSection = ResMgr.openSection( self.fileName )
		except TypeError:
			pSection = ResMgr.openSection( self.fileName )
			#print "Warning - creating SFX from no prerequisites could be costly", self.fileName
			#traceback.print_stack()
		
		if pSection != None:
			self.createFromSection( pSection, prereqs )
		else:
			ERROR_MSG( "Could not open file", self.fileName )
			return None
			
		global debugTimings
		if debugTimings == 1:
			self.events.append( ("",timedEvents.DebugEventTiming()) )	


	def parse( self, tag, store, pSection, prereqs = None, gatherPrerequisites = False ):		
		for (sname,ds) in pSection.items():

			if sname == tag:
				section = ds.items()[0][1]									

				if s_sectionProcessors.has_key( section.name ):
					instance = s_sectionProcessors[section.name]()
					
					#We are either loading or gathering prerequisites during the parse..
					if not gatherPrerequisites:
						result = instance.load(section, prereqs)
						if result != None:
							try:
								store[ ds.asString ] = result
							except:
								store.append( (ds.asString,result) )
						else:
							ERROR_MSG( "None was returned.  Not adding to this effect : ", section.name, ds.asString )
					else:
						self.prereqs.add( section.asString )
						if hasattr( instance, "prerequisites" ):
							self.prereqs.update( instance.prerequisites(section) )
				else:
					ERROR_MSG( "No section processor matches the tag ", section.name, ds.asString )
					result = None	
				
				
	def modelName( self, visualName ):
	
		if len(visualName) > 7:
			if visualName[-7:] == ".visual":
				return visualName[:-7]+".model"
			
		return visualName


	def prerequisitesFromSection( self, pSection ):
		self.parse( "Actor", self.actors, pSection, gatherPrerequisites = True )
		self.parse( "Event", self.events, pSection, gatherPrerequisites = True )


	def createFromSection( self, pSection, prereqs = None ):	
		self.parse( "Actor", self.actors, pSection, prereqs )
		self.parse( "Joint", self.joints, pSection, prereqs )
		self.parse( "Event", self.events, pSection, prereqs )

		#check for all the actors
		for actor in self.joints.keys():
			if not self.actors.has_key( actor ):
				ERROR_MSG( "Actor not found", actor )
				del self.joints[actor]

		#check all actors are used
		for actor in self.actors.keys():
			if not self.joints.has_key(actor):
				WARNING_MSG( "Actor exists, but is not attached anywhere", actor )

				
	def extendTime( self, event, duration ):
		pass


#------------------------------------------------------------------------------
#	OneShotSFX - Concrete base class for SFX that has a simple one-play cycle.
#	with this class, you call go( source, target ).  It will clean itself up
#	and when completely finished, its self.going flag will be reset.
#
#	maxDuration is an important parameter, it makes sure that OneShotSFX do
#	not build up in the world.   Some SFX files
#
#	This type of SFX does not keep a permanent assocation with any source.
#------------------------------------------------------------------------------
class OneShotSFX( SFX ):
	def __init__( self, fileName = None, maxDuration = 10.0, prereqs = None ):
		SFX.__init__( self, fileName )
		SFX.create( self, prereqs )
		self.timer = EventTimer()
		self.timers = {}
		for actorName in self.actors.keys():
			self.timers[actorName] = EventTimer()
		self.maxDuration = maxDuration
		if self.maxDuration < 0.0:
			WARNING_MSG( "maxDuration was negative!  setting to 10", self.maxDuration )
			self.maxDuration = 10.0
			
	
	#This method plays all the events that match the transformDependent flag.
	#e.g. the first pass through ( eventTiming = 0 ) happens during the
	#	  attach frame.  this is so particles can be cleared as they are attached
	#	  (so they don't draw in their last position for one frame)
	#
	#		the second pass through ( eventTiming = 1 ) happens after
	#		the transforms have been set, usually the next frame.  this is
	#		so particles etc. can be spawned at the correct location.
	#
	#		the third pass through ( eventTiming =2 ) happens after
	#		the total duration of the sfx is known.  this duration is put
	#		into the kargs.  this is for events that happen 80% through the effect
	#		(for example turning off time triggered particles for a nice fade-out,
	#		or setting up a colour animation that is timed exactly)
	
	def playEvents( self, eventTiming, source, target = None, callbackFn = None, **kargs ):
		for (actorName,event) in self.events:
			if event.eventTiming() == eventTiming:
				try: actor = self.actors[actorName]
				except: actor = None
				duration = min( event.go( self, actor, source, target, **kargs ), self.maxDuration )
				if actorName != "":
					if not self.lengths.has_key( actorName ):
						self.lengths[actorName] = duration
					else:
						self.lengths[actorName] = max( self.lengths[actorName], duration )
				self.totalDuration = max( duration, self.totalDuration )
			
		return self.totalDuration


	#This method should be the only method called on this SFX.  Once fully
	#finished, the self.going flag will be reset, and you can call go() again.
	#
	#If you pass in a callback function, it will be called upon full completion
	#of the effect
	def go( self, source, target = None, callbackFn = None, **kargs ):
		if self.timer.going():
			return
			
		#artificially increase the timer semaphore.  this makes sure
		#that we can't call go twice, even though the timer proper begins
		#next frame
		self.timer.reserve()
		self.lengths = {}
		self.totalDuration = 0.0

		for (actorName,attacher) in self.joints.items():
			attacher.attach( self.actors[actorName], source, target )
			
		self.playEvents(IMMEDIATE_EVENT,source,target,callbackFn,**kargs)

		#Callback the frame just after attachments were made.  This is
		#so the nodes we just attached to have a chance to set a correct
		#world transform, before we attach stuff.
		BigWorld.callback( 0.001, lambda: self.go2(source, target, callbackFn, **kargs) )


	#internal - once attached and have waited a frame, spawn all events
	def go2( self, source, target, callbackFn, **kargs ):
		self.playEvents(TRANSFORM_DEPENDENT_EVENT,source,target,callbackFn,**kargs)
		
		#now all the events have played, callback to detach all actors,
		#and callback to stop the sfx.
		for (actorName,duration) in self.lengths.items():
			if duration <= 0.0:
				duration = self.maxDuration
				self.totalDuration = self.maxDuration
			self.timers[actorName].begin( duration, partial(self.detach,actorName,source,target) )
			
		if (self.totalDuration > self.maxDuration) or (self.totalDuration <= 0.0):
			WARNING_MSG( "using maxDuration for this effect. perhaps this was unexpected?", self, source, target )
			self.totalDuration = self.maxDuration
		
		#now play duration-dependent events.	
		kargs["totalDuration"] = self.totalDuration
		kargs["actorDurations"] = self.lengths
		self.playEvents(DURATION_DEPENDENT_EVENT,source,target,callbackFn,**kargs)
		
		self.timer.begin( self.totalDuration, lambda:self.stop(source,target,callbackFn) )
		#release the reserved ref count on the timer.
		self.timer.release()
		
	def detach( self, actorName, source, target ):
		#DEBUG_MSG( "detach", actorName )
		self.joints[actorName].detach( self.actors[actorName],source,target )

	#internal - once all events have completed and all actors have been detached,
	#invoke callback if necessary.
	def stop( self, source, target, callbackFn ):
		#DEBUG_MSG( "stop" )
		if callbackFn:
			callbackFn()
			
	def extendTime( self, event, duration ):
		#if the event depends on an actor,
		#extend the actor's timer, so it isn't detached early
		for (actorName,ev) in self.events:
			if event == ev:
				self.timers[actorName].extend( duration )
				#DEBUG_MSG( "actor time extension", actorName, event, duration )
				
			
		#and extend our overall timer so the sfx doesn't finish
		#early
		#DEBUG_MSG( "time extension", event, duration )
		self.timer.extend(duration)
			
			
			
overruns = {}
sfxBuffer = {}

def outputOverruns():
	global overruns
	if len(overruns.keys()) == 0:
		return
		
	DEBUG_MSG( "---------------SFX Buffer Overruns------------------" )
	DEBUG_MSG( "Warning - during that run, some buffered sfx ran out" )
	DEBUG_MSG( "" )
	for (fileName,(discard,largest)) in overruns.items():
		DEBUG_MSG( fileName, largest )
	overruns = {}
	DEBUG_MSG( "----------------------------------------------------" )
	
	
def cleanupBufferedEffects():	
	global sfxBuffer
	sfxBuffer = {}	


#------------------------------------------------------------------------------
#	Buffered version of OneShotSFX.  Only called internally ( don't create
#	one of these yourself! )
#------------------------------------------------------------------------------
class BufferedOneShotSFX( OneShotSFX ):
	def __init__( self, fileName, maxDuration, queue, prereqs = None ):
		OneShotSFX.__init__( self, fileName, maxDuration, prereqs )
		self.queue = queue
		
	#internal - once all events have completed and all actors have been detached,
	#reset the going flag, and invoke callback if necessary.
	def stop( self, source, target, callbackFn ):
		global overruns
		OneShotSFX.stop( self, source, target, callbackFn )
		self.queue.put( self )
		
		
#------------------------------------------------------------------------------
#	Callback function for asynchronous buffering of SFX.
#------------------------------------------------------------------------------
def onAsyncLoadBufferedSFX( fileName, maxDuration, resourceRefs ):	
	global sfxBuffer
	queue = sfxBuffer[fileName]
	queue.put( BufferedOneShotSFX( fileName, maxDuration, queue, resourceRefs ) )


#------------------------------------------------------------------------------
#	This method preloads the whole sfx buffer given by fileName.
#
#	If no prerequisites are passed in, then the entire buffer is synchronously
#	created.  This may create a pause in the rendering thread.
#
#	If prerequisites are provided, it immediately queues up one sfx, and
#	then asnychronously loads the rest.
#------------------------------------------------------------------------------
def preloadBufferedOneShotSFX( fileName, maxDuration = 10.0, prereqs = None ):
	pSection = None
	if prereqs != None:
		pSection = prereqs[fileName]
	else:
		pSection = ResMgr.openSection( fileName )
		
	if not pSection:
		ERROR_MSG( "Could not open file", fileName )
		return False
		
	global sfxBuffer
	sfxBuffer[fileName] = Queue()
	queue = sfxBuffer[fileName]			
	bufferSize = pSection.readInt( "bufferSize", 10 )
	
	if prereqs != None:
		resourceIDs = tuple(prereqs.keys())
		queue.put(BufferedOneShotSFX( fileName, maxDuration, queue, prereqs ))
		for i in xrange(0,bufferSize-1):
			BigWorld.loadResourceListBG( resourceIDs, partial( onAsyncLoadBufferedSFX, fileName, maxDuration ) )
	else:
		for i in xrange(0,bufferSize):
			queue.put( BufferedOneShotSFX( fileName, maxDuration, queue ) )
		
	return True


#------------------------------------------------------------------------------
#	Entry point for using Buffered version of OneShotSFX
#------------------------------------------------------------------------------		
def getBufferedOneShotSFX( fileName, maxDuration = 10.0, prereqs = None ):
	global sfxBuffer
	global overruns	
	
	if not sfxBuffer.has_key( fileName ):
		if preloadBufferedOneShotSFX( fileName, maxDuration, prereqs ) == False:
			return None
			
	queue = sfxBuffer[fileName]
	if not queue.empty():
		if overruns.has_key( fileName ):
			(current,largest)=overruns[fileName]
			overruns[fileName]=(0,largest)
		return queue.get()
	else:
		#WARNING_MSG( "ran out of buffered sfx", fileName )
		if not overruns.has_key( fileName ):
			overruns[fileName]=(1,1)
		else:
			(current,largest)=overruns[fileName]
			overruns[fileName]=(current+1,max(largest,current+1))
		return None
		
		
def bufferedOneShotSFX( fileName, source, target = None, callbackFn = None, maxDuration = 10.0, prereqs = None, **kargs ):	
	s = getBufferedOneShotSFX( fileName, maxDuration, prereqs )
	s.maxDuration = maxDuration
	if s:
		s.go( source, target, callbackFn, **kargs )


#------------------------------------------------------------------------------
#	PersistentSFX - Concrete base class for SFX that persist on an object.
#	with this class, you must call attach(), then go() go() go() then detach()
#
#	Once attached, there is a persistent association with the source.  Thus
#	when calling go(), you need not pass in the source again.
#
#	You can pass in a callback fn to go(), which is called back when the effect
#	has properly finished one pass through for all its events.
#------------------------------------------------------------------------------
class PersistentSFX( SFX ):
	def __init__( self, fileName = None, prereqs = None ):
		SFX.__init__( self, fileName )
		SFX.create( self, prereqs )
		self.timer = EventTimer()
		self.source = None
		self.target = None

	def attach( self, source ):
		self.source = source
		for (actor,attacher) in self.joints.items():
			attacher.attach( self.actors[actor], source )

	def go( self, target = None, callbackFn = None, **kargs ):
		self.totalDuration = 0.0
		self.target = target
		for (actorName,event) in self.events:
			if event.eventTiming() == 0:
				try: actor = self.actors[actorName]
				except: actor = None
				self.totalDuration = max( self.totalDuration, event.go( self, actor, self.source, target, **kargs ) )
		
		BigWorld.callback( 0.001, lambda:self.go2(target, callbackFn, **kargs ) )
	
	def go2( self, target = None, callbackFn = None, **kargs ):		
		for (actorName,event) in self.events:
			if event.eventTiming() > 0:
				try: actor = self.actors[actorName]
				except: actor = None
				self.totalDuration = max( self.totalDuration, event.go( self, actor, self.source, target, **kargs ) )

		if callbackFn:
			self.timer.begin( self.totalDuration + 0.001, callbackFn )
			
	def stop( self ):
		stopTime = 0.0
		for (actorName,event) in self.events:
			actor = self.actors[actorName]
			stopTime = max( stopTime, event.stop( actor, self.source, self.target ) )
		return stopTime

	def goNextFrame( self, target = None, callbackFn = None, **kargs ):
		#this method is now deprecated
		self.go( target, callbackFn, **kargs )

	def detach( self ):
		for (actor,attacher) in self.joints.items():
			attacher.detach( self.actors[actor], self.source )
		self.source = None
		self.target = None

import Pixie
	
#intialise a Queue, this is purely to avoid hitting the scripts/common/Lib
#folder in the main thread (Queue is the first thing in FD that uses the
#python threading library) when a bufferedSFX is first used.
queue = Queue()

#Initialise the framework
import actors
import events
import moreEvents
import timedEvents
import joints
import shockwave

from events import IMMEDIATE_EVENT
from events import TRANSFORM_DEPENDENT_EVENT
from events import DURATION_DEPENDENT_EVENT