from GameData import PlayerModelData
import AvatarModel
import random

def modelListToCharacterClassString( models ):
	"""
	Return a string identifying what character class the given model list
	represents, e.g. ranger or warrior.

	@param models 	The list of resource paths pointing to models that
					are composed into a particular character class's
					in-game avatar.
	"""
	charClass = "(unknown)"

	# Just pick the first model in the list, and extract the third path
	# component (i.e. the path component after characters/avatars)
	if len( models ) > 0 and \
			models[0].startswith( "characters/avatars/" ):
		charClass = models[0].split( '/' )[2]

	return charClass


def defaultPlayerModel():
	return {'models':['characters/avatars/ranger/ranger_body.model',
					  'characters/avatars/ranger/ranger_head.model',],
			'dyes':[],
			'sfx':[] }

def randomPlayerModel():
	baseModel = random.choice( PlayerModelData.PLAYER_MODELS )

	return randomCustomisations( baseModel )


def reCustomisePlayerModel( unpackedAvatarModel ):
	for model in PlayerModelData.PLAYER_MODELS:
		if set( model.models ).issubset( set( unpackedAvatarModel['models'] ) ):
			return randomCustomisations( model )
	assert "source model is not a player model. ['%s']" % "', '".join( unpackedAvatarModel['models'] )


def randomCustomisations( baseModel ):
	assert isinstance( baseModel, PlayerModelData.Model )

	models = []
	dyes = []
	sfx = []

	def resolveModelCustomisations( model ):
		models = list( model.models )
		otherCustomisations = []
		for customisation in model.customisations:
			if isinstance( customisation, PlayerModelData.ModelCustomisation ):
				newModels, newCustomisations = resolveModelCustomisations( random.choice( customisation.models ) )
				models.extend( newModels )
				otherCustomisations.extend( newCustomisations )

			if isinstance( customisation, PlayerModelData.MaterialCustomisation ):
				otherCustomisations.append( customisation )

		return models, otherCustomisations

	models, customisations = resolveModelCustomisations( baseModel )

	for customisation in customisations:
		if isinstance( customisation, PlayerModelData.MaterialCustomisation ):
			tint = random.choice( customisation.tints )
			for materialGroup in customisation.materialGroups:
				dyes.append( {'materialGroup':materialGroup,
							  'tint':tint } )

	return {'models':models,
			'dyes':dyes,
			'sfx':sfx }



# This is a temporary solution until the character customisation screen is
# implemented.
def nextPresetModel( oldAvatarModel ):
	if oldAvatarModel in PRESET_MODELS:
		return PRESET_MODELS[(PRESET_MODELS.index( oldAvatarModel ) + 1) % len(PRESET_MODELS)]
	else:
		return PRESET_MODELS[0]

def previousPresetModel( oldAvatarModel ):
	if oldAvatarModel in PRESET_MODELS:
		return PRESET_MODELS[PRESET_MODELS.index( oldAvatarModel ) - 1]
	else:
		return PRESET_MODELS[0]


# created using [PlayerModel.randomPlayerModel() for i in range( 6 )]
PRESET_MODELS = \
	[
		{'models': ['characters/avatars/ranger/ranger_body.model', 'characters/avatars/ranger/ranger_head.model'], 'dyes': [{'tint': 'Default', 'materialGroup': 'Single_material_skinned'}, {'tint': 'Merchant', 'materialGroup': 'Legs_skinned'}], 'sfx': []},
		{'models': ['characters/avatars/warrior/warrior.model', 'characters/avatars/warrior/hair00.model', 'characters/avatars/warrior/1b_legs_01.model', 'characters/avatars/warrior/1b_arms_02.model', 'characters/avatars/warrior/1b_chest_01.model'], 'dyes': [], 'sfx': []},
		{'models': ['characters/avatars/warrior/warrior.model', 'characters/avatars/warrior/hair.model', 'characters/avatars/warrior/1b_legs_01.model', 'characters/avatars/warrior/1b_arms_02.model', 'characters/avatars/warrior/1b_chest_00.model'], 'dyes': [], 'sfx': []},
		{'models': ['characters/avatars/ranger/ranger_body.model', 'characters/avatars/ranger/ranger_head.model'], 'dyes': [{'tint': 'Default', 'materialGroup': 'Single_material_skinned'}, {'tint': 'Default', 'materialGroup': 'Legs_skinned'}], 'sfx': []},
		{'models': ['characters/avatars/warrior/warrior.model', 'characters/avatars/warrior/hair.model', 'characters/avatars/warrior/1b_legs_01.model', 'characters/avatars/warrior/1b_arms_00.model', 'characters/avatars/warrior/1b_chest_00.model'], 'dyes': [], 'sfx': []},
		{'models': ['characters/avatars/ranger/ranger_body.model', 'characters/avatars/ranger/ranger_head.model'], 'dyes': [{'tint': 'CustomTorso', 'materialGroup': 'Single_material_skinned'}, {'tint': 'Default', 'materialGroup': 'Legs_skinned'}], 'sfx': []},
	]

# PlayerModel.py
