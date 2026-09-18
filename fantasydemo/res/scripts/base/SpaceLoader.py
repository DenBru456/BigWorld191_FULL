import BigWorld
import FDConfig

nameSeparator = "/"

class SpaceLoader( BigWorld.Base ):
	def __init__( self ):
		self.spaceDir = self.cellData[ "geometry" ]
		self.spaceLabel = self.spaceDir
		print "SpaceLoader", self.id, "geometry =", self.spaceDir

		if self.createOnCell:
			self.createCellEntity( self.createOnCell )
			self.createOnCell = None
		elif self.isDefault:
			# default space loader
			self.createInDefaultSpace()
		else:
			self.createInNewSpace()

	def onGetCell( self ):
		if FDConfig.AUTO_LOAD_ENTITIES:
			print "SpaceLoader.onGetCell loading space", self.spaceDir
			BigWorld.fetchEntitiesFromChunks( self.spaceDir,
					EntityLoader( self ) )

	def onLoseCell( self ):
		print "SpaceLoader", self.spaceDir, " destroyed"
		self.destroy()

class EntityLoader:
	def __init__( self, spaceLoader ):
		self.spaceLoader = spaceLoader
		self.teleportPoints = {}
		self.teleportSources = []

	def onSection( self, entity, matrix ):
		entityType = entity.readString( "type" )
		properties = entity[ "properties" ]
		pos = matrix.applyToOrigin()

		# create entity base
		if entityType == "SpaceLoader":
			# read the space name from the chunk data
			if len( properties.readString( "spaceLabel" ) ) > 0:
				self.spaceLoader.spaceLabel = properties.readString( "spaceLabel" )
		elif entityType == "TeleportSource":
			if properties.readString( "spaceLabel" ) == "":
				self.teleportSources.append( (entityType, properties, pos, matrix) )
			else:
				e = BigWorld.createBaseLocally( entityType,
				properties,
				createOnCell = self.spaceLoader.cell,
				position = pos,
				direction = (matrix.roll, matrix.pitch, matrix.yaw) )
		elif entityType == "TeleportPoint":
			e = BigWorld.createBaseLocally( entityType,
				properties,
				createOnCell = self.spaceLoader.cell,
				position = pos,
				direction = (matrix.roll, matrix.pitch, matrix.yaw) )
			e.dstPos = pos
			if e.label in self.teleportPoints:
				print "Warning: EntityLoader.onSection TeleportPoint", e.label, "already exists in space", self.spaceLoader.spaceDir
			else:
				self.teleportPoints[ e.label ] = e
		else:
			BigWorld.createBaseAnywhere( entityType,
				properties,
				createOnCell = self.spaceLoader.cell,
				position = pos,
				direction = (matrix.roll, matrix.pitch, matrix.yaw) )

	def onFinish( self ):
		spaceQualifier = self.spaceLoader.spaceLabel + nameSeparator

		for (entityType, properties, pos, matrix) in self.teleportSources:
			e = BigWorld.createBaseLocally( entityType,
				properties,
				spaceLabel = self.spaceLoader.spaceLabel,
				createOnCell = self.spaceLoader.cell,
				position = pos,
				direction = (matrix.roll, matrix.pitch, matrix.yaw) )

		# register all teleport points globally
		for l in self.teleportPoints:
			e = self.teleportPoints[l]
			print "Registering teleport point", spaceQualifier + e.label
			e.registerGlobally( spaceQualifier + e.label, e.onRegister )

		del self.teleportPoints
		del self.teleportSources

		print "Finished loading entities for space", self.spaceLoader.spaceLabel
		# space loader is no longer needed
		self.spaceLoader.destroyCellEntity()

# Teleporter.py
