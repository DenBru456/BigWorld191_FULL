from sfx import s_sectionProcessors
from sfx import typeCheck
from bwdebug import *
import BigWorld
import traceback

#---------------------------------------------------
#	Interface sfx.Joint
#
#	A joint is a thing that joins two things together;
#	like a particle system to a hard-point
#	
#---------------------------------------------------
class Joint:
	def __init__( self ):
		pass
		
	def load( self, pSection, prereqs = None ):
		return self
		
	def attach( self, actor, source, target = None ):
		pass
		
	def detach( self, actor, source, target = None ):
		pass


#---------------------------------------------------
#	Interface sfx.SingletonJoint
#
#	A singleton joint is the base class for joints
#	that are singletons.  it exposes a call() method
#	to return the instance.
#	
#---------------------------------------------------		
class SingletonJoint( Joint ):
	def __init__( self ):
		Joint.__init__( self )
		
	def __call__( self ):
		return self
		
#---------------------------------------------------
#	This joint attaches a PyAttachment to an entity.
#
#	A PyAttachment can be a model, particle system etc.
#---------------------------------------------------
class Entity( SingletonJoint ):

	def attach( self, actor, source, target = None ):
		typeCheck( actor, [BigWorld.Entity] )
		
		if actor.attached:
			ERROR_MSG( "actor is already attached!", self, actor, source )
			return 0
			
		try:
			source.addModel( actor )
		except:
			ERROR_MSG( "error in addModel to entity", self, actor, source )
			
		#Move to the correct location
		moved = 0
		
		try:
			#actor is a model?  can add a motor
			actor.addMotor( BigWorld.Servo( actor.matrix ) )
			moved = 1
		except AttributeError:
			try:
				#actor is a particle system?
				actor.explicitPosition = source.position
				moved = 1
			except AttributeError:
				try:
					#actor is a meta-particle system
					for i in xrange(0,actor.nSystems()):
						actor.system(i).explicitPosition = source.position
					moved = 1
				except:
					traceback.print_exc()
					traceback.print_stack()
		
		if not moved:
			ERROR_MSG( "Unknown error trying to move actor to the correct location", actor, source )
			
	def detach( self, actor, source, target = None ):
		if not actor.attached:
			ERROR_MSG( "actor is not attached!", self, actor, source )
			return 0
			
		try:
			source.delModel( actor )
		except:
			ERROR_MSG( "error in delModel from entity", self, actor, source )
			
			
s_entity = Entity()
s_sectionProcessors[ "Entity" ] = s_entity


#---------------------------------------------------
#	This joint attaches a PyAttachment to model.root
#
#	The source can be blank models, entities
#	or PyModels
#
#	A PyAttachment can be a model, particle system etc.
#---------------------------------------------------
class ModelRoot( SingletonJoint ):

	def attach( self, actor, source, target = None ):			
		if actor.attached:
			ERROR_MSG( "actor is already attached!", self, actor, source )
			return 0
			
		try:
			source.root.attach( actor )
		except:
			try:
				source.model.root.attach( actor )
			except:
				ERROR_MSG( "error in addModel to modelRoot", self, actor, source )
			
					
	def detach( self, actor, source, target = None ):
		if not actor.attached:
			ERROR_MSG( "actor is not attached!", self, actor, source )
			return 0
			
		try:
			source.root.detach( actor )
		except:
			try:
				source.model.root.detach( actor )
			except:
				ERROR_MSG( "error in detach from modelRoot", self, actor, source )
			
			
s_modelRoot = ModelRoot()
s_sectionProcessors[ "ModelRoot" ] = s_modelRoot
			
#---------------------------------------------------
#	This joint attaches a PyAttachment to a node.
#
#	A PyAttachment can be a model, particle system etc.
#---------------------------------------------------
class Node( Joint ):
	def load( self, pSection, prereqs = None ):
		self.nodeName = pSection.asString
		return self
		
	def attach( self, actor, source, target = None ):
		#typeCheck( actor, [BigWorld.Model,BigWorld.Entity] )
		if actor.attached:
			ERROR_MSG( "actor is already attached!", actor, self.nodeName )
			return 0
		
		#First try entity ( or something with a model attribute )
		try:
			source.model.node( self.nodeName ).attach( actor )
		except AttributeError:
			#Attribute error - try as a model being passed in
			try:
				source.node( self.nodeName ).attach( actor )
			except ValueError:
				#Value error - probably an incorrect node name
				ERROR_MSG( "No such node", self.nodeName )
		except ValueError:
			#Value error - probably an incorrect node name
			ERROR_MSG( "No such node", self.nodeName )
		
	def detach( self, actor, source, target = None ):
		#typeCheck( actor, [BigWorld.Model,BigWorld.Entity] )		
		if not actor.attached:
			ERROR_MSG( "actor is not attached!", actor, self.nodeName )
			return 0
			
		#First try entity ( or something with a model attribute )
		try:
			source.model.node( self.nodeName ).detach( actor )
		except AttributeError:
			#Attribute error - try as a model being passed in
			try:
				source.node( self.nodeName ).detach( actor )
			except ValueError:
				#Value error - probably an incorrect node name
				ERROR_MSG( "No such node", self.nodeName )
		except ValueError:
			#Value error - probably an incorrect node name
			ERROR_MSG( "No such node", self.nodeName )
		
s_sectionProcessors[ "Node" ] = Node


#---------------------------------------------------
#	This joint attaches a PyAttachment to a hardpoint.
#
#	A PyAttachment can be a model, particle system etc.
#---------------------------------------------------
class HardPoint( Joint ):
	def load( self, pSection, prereqs = None ):
		self.hpName = pSection.asString
		return self
		
	def attach( self, actor, source, target = None ):
		#typeCheck( actor, PyAttachment )
		if actor.attached:
			ERROR_MSG( "actor is already attached!", actor, self.hpName )
			return 0
			
		try:
			setattr( source.model, self.hpName, actor )
		except AttributeError:
			try:
				setattr( source, self.hpName, actor )
			except AttributeError:
				ERROR_MSG( "Missing hardpoint", source, "HP_" + self.hpName )
		except:
			try:
				setattr( source, self.hpName, actor )
			except:
				ERROR_MSG( "Unknown error", source, self.hpName )
		
	def detach( self, actor, source, target = None ):
		#typeCheck( actor, PyAttachment )
		if not actor.attached:
			ERROR_MSG( "Actor is not attached", actor, self.hpName )
			return 0
		try:
			source.model.node( "HP_" + self.hpName ).detach( actor )
		except AttributeError:
			try:
				source.node( "HP_" + self.hpName ).detach( actor )
			except:
				ERROR_MSG( "Unknown error", source, self.hpName )
			
s_sectionProcessors[ "HardPoint" ] = HardPoint
#because typos do happen...
s_sectionProcessors[ "Hardpoint" ] = HardPoint



#---------------------------------------------------
#	This joint attaches a Light to a node
#
#	The source must be a PyChunkLight
#---------------------------------------------------
class LightSource( Joint ):

	def load( self, pSection, prereqs = None ):
		self.nodeName = pSection.asString
		return self

	def attach( self, actor, source, target = None ):
		#typeCheck( actor, PyChunkLight )
		
		#get the node
		node = None
		if self.nodeName != "":
			try:			
				node = source.node( self.nodeName )
			except TypeError:
				#Type error - probably a blank model
				pass			
			except ValueError:			
				#Value error - probably an incorrect node name
				ERROR_MSG( "No such node", self.nodeName )
		
		try:
			if node != None:
				actor.source = node			
			else:			
				actor.source = source.root

			actor.visible = True
		except:
			ERROR_MSG( "error in set light source", self, actor, source )
			
					
	def detach( self, actor, source, target = None ):
		actor.visible = False
		actor.source = None		
			
			
s_sectionProcessors[ "LightSource" ] = LightSource


#---------------------------------------------------
#	This joint attaches a PyAttachment to a dummy
#	model owned by the player entity.
#
#	The benefit of using this attachment is that
#	it doesn't matter if the player changes their
#	model, or turns invisible.
#---------------------------------------------------
class DummyModel( SingletonJoint ):

	def __init__( self ):
		SingletonJoint.__init__( self )
		self.dummy = None


	def attach( self, actor, source, target = None ):
		if actor.attached:
			ERROR_MSG( "actor is already attached!", self, actor, source )
			return 0
			
		player = BigWorld.player()
		if not player:
			ERROR_MSG( "Cannot add effect to dummy model if there is no player.", self, actor, source )
			return 0
			
		self._ensureDummyExists()

		try:
			self.dummy.root.attach( actor )
		except:
			ERROR_MSG( "error in addModel to dummy", self, actor, source )


	def detach( self, actor, source, target = None ):
		if not actor.attached:
			ERROR_MSG( "actor is not attached!", self, actor, source )
			return 0

		player = BigWorld.player()
		if player != None:
			self.dummy.root.detach( actor )


	def _ensureDummyExists( self ):
		if None is self.dummy:			
			self.dummy = BigWorld.Model("")
			self.dummy.visibleAttachments = True
			BigWorld.player().addModel( self.dummy )
			servo = BigWorld.Servo( BigWorld.player().matrix )
			self.dummy.motors = (servo,)


s_dummyModel = DummyModel()
s_sectionProcessors[ "DummyModel" ] = s_dummyModel