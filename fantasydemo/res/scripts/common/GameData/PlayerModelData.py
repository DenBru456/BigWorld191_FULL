'''The module contains data about available player models and their posible
customisations. All models and their customisations (dyes etc.) are required
to be present in the AvatarModelData module.
'''

import ResMgr
import AvatarModelData
import AvatarModel

PLAYER_MODELS = None


class Model:
	'''This class holds the list of required models and available customisations
	for one 'base model' such has Human Male.
	'''

	def __init__( self, dataSection ):
		self.name = dataSection.readString( "name" )
		self.models = dataSection.readStrings( "models/resPath" )
		self.customisations = self.loadCustomisations( dataSection["customisations"] )
		if not self.checkModel():
			raise Exception()


	def loadCustomisations( self, dataSection ):
		customisations = []
		for tag, section in dataSection.items():
			if tag == "modelCustomisation":
				customisations.append( ModelCustomisation( section ) )
	
			if tag == "materialCustomisation":
				customisations.append( MaterialCustomisation( section ) )
		return customisations


	def checkModel( self ):
		ok = True

		for model in self.models:
			if not model in AvatarModelData.MODEL_INDEXES.keys():
				print "ASSET ERROR: model '%s' not in AvatarModelData" % model
				ok = False

		if not ok:
			return False
	
		referencedModels = []
		for modelPath in self.models:
			modelIndex = AvatarModelData.MODEL_INDEXES[modelPath]
			referencedModels.append( AvatarModelData.INDEXED_MODELS[modelIndex] )
		mergedDyes = AvatarModel.mergeDyes( referencedModels )

		for customisation in self.customisations:
			if isinstance( customisation, ModelCustomisation ):
				for model in customisation.models:
					ok = ok and model.checkModel()
					
			if isinstance( customisation, MaterialCustomisation ):
				for materialGroup in customisation.materialGroups:
					if not materialGroup in mergedDyes:
						print "ASSET ERROR: material group '%s' not in model ['%s']" % materialGroup, "', '".join( self.models )
						ok = False					
					else:
						for tint in customisation.tints:
							if not tint in mergedDyes[materialGroup]:
								print "ASSET ERROR: '%s' is not a tint of material group '%s' in model ['%s']" % tint, materialGroup, "', '".join( self.models )
								ok = False
		return ok


class Customisation:
	def __init__( self, dataSection ):
		self.name = dataSection.readString( "name" )


class ModelCustomisation( Customisation ):
	'''This class represents a customisation where each option adds a new model
	to the base. These models can also then have their own customisations.
	'''
	def __init__( self, dataSection ):
		Customisation.__init__( self, dataSection )
		self.models = []
		for modelData in dataSection["models"].values():
			try:
				self.models.append( Model( modelData ) )
			except Exception, e:
				print "ASSET ERROR: Could not load avatar model '%s'" % modelData.readString( "name", "Unknown" )
				print e


class MaterialCustomisation( Customisation ):
	'''This class represents a material customisation where each option applies
	a different dye to the model.
	'''
	def __init__( self, dataSection ):
		Customisation.__init__( self, dataSection )
		self.materialGroups = dataSection.readStrings( "materialGroups/materialGroup" )
		self.tints = [d.readString("tintName") for d in dataSection['tints'].values()]


def load():
	global PLAYER_MODELS
	PLAYER_MODELS = []
	playerModelsSection = ResMgr.openSection( "scripts/data/player_model_data.xml/playerModels" )
	for modelData in playerModelsSection.values():
		try:
			print "Loading PlayerModel info: '%s'" % modelData.readString( "name" )
			PLAYER_MODELS.append( Model( modelData ) )
		except Exception, e:
			print "ASSET ERROR: Could not load model '%s'" % modelData.readString( "name", "Unknown" )
			print e

load()
